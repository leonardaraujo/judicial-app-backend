from fastapi import APIRouter, File, UploadFile, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.document import Document
from services.pdf_service import extract_text_from_pdf
from fastapi.responses import FileResponse
import time
import shutil
import os
import google.generativeai as genai
import json

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
for model in genai.list_models():
    print(model)
router = APIRouter()

PROMPT = """
Eres un analizador de documentos jurídicos. Extrae la siguiente información de la sentencia penal y responde en formato JSON (las claves deben estar en inglés):
{
  "case_number": "",
  "case_year": "",
  "crime": "",
  "verdict": "",
  "cited_jurisprudence": []
}
- El "case_number" es el número de expediente, que suele aparecer al inicio del documento (normalmente en las primeras 100 palabras o primeras líneas) como "EXPEDIENTE N°", "EXP. N.", "EXP N°", "EXP. N.°", etc. Si hay varios números, elige el primero que aparece al principio.
- El "case_year" debe ser el segundo grupo numérico del "case_number" (por ejemplo, si el case_number es "11468-2018-44-0401-JR-PE-01", el case_year es "2018"). Si no hay case_number, deja case_year vacío.
- El "crime" debe ser solo el nombre del delito principal por el cual se juzga el caso, de forma breve y específica (por ejemplo: "asesinato", "violencia familiar", "crimen de odio", "conducción en estado de ebriedad", etc.). No incluyas detalles, nombres de personas, hechos, ni el veredicto.
- "verdict" solo puede ser: "Absuelto", "Culpable", "Sobreseído", "Archivado", "Prescrito", "Desestimado", "Nulidad".
- Si el texto menciona "Condenado", "Sentencia condenatoria" u otros sinónimos de culpabilidad, usa "Culpable".
- Si el texto menciona "Sentencia absolutoria" u otros sinónimos de absolución, usa "Absuelto".
- Para "cited_jurisprudence", extrae todas las referencias a jurisprudencia citada en el documento. Considera como jurisprudencia cualquier mención a "Exp.", "Sentencia", "Casación", "Resolución", "Pleno", "STC", "R.N.", "Recurso", "Jurisprudencia", etc. Incluye el texto completo de cada referencia, tal como aparece en el documento.
- No inventes ningún dato: solo responde con información que realmente esté presente en el texto recibido.
Si algún dato no está presente, deja el campo vacío o como lista vacía.
Texto del documento:
"""

def extract_metadata(text):
    prompt = PROMPT + text
    response = genai.GenerativeModel("models/gemini-2.5-flash-lite").generate_content(prompt)
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.strip().startswith("json"):
            raw = raw.strip()[4:]
    try:
        data = json.loads(raw)
        print("Parsed metadata:", data)
    except Exception as e:
        print("Error parsing Gemini response:", e)
        data = {
            "case_number": "",
            "case_year": "",
            "crime": "",
            "verdict": "",
            "cited_jurisprudence": []
        }
    return data

@router.post("/analyze_pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    total_start = time.time()
    # Guardar el archivo PDF en disco
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text_from_pdf(open(file_path, "rb"))
    gemini_start = time.time()
    metadata = extract_metadata(text)
    gemini_end = time.time()
    gemini_duration = gemini_end - gemini_start

    db: Session = SessionLocal()
    document = Document(
        case_number=metadata.get("case_number"),
        case_year=metadata.get("case_year"),
        crime=metadata.get("crime"),
        verdict=metadata.get("verdict"),
        cited_jurisprudence=json.dumps(metadata.get("cited_jurisprudence", []), ensure_ascii=False),
        file_path=file_path  # <-- Guarda la ruta del archivo
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    db.close()

    total_end = time.time()
    total_duration = total_end - total_start

    return JSONResponse(content={
        "metadata": metadata,
        "document_id": document.id,
        "file_url": f"/documents/download/{document.id}",
        "gemini_processing_time_seconds": round(gemini_duration, 3),
        "total_processing_time_seconds": round(total_duration, 3),
        "msg": "Document saved in PostgreSQL, file saved"
        # "msg": "Document saved in PostgreSQL, file saved and embedding in Qdrant"
    })

@router.get("/documents/download/{document_id}")
def download_document(document_id: int):
    db: Session = SessionLocal()
    doc = db.query(Document).filter(Document.id == document_id).first()
    db.close()
    if not doc or not doc.file_path or not os.path.exists(doc.file_path):
        return JSONResponse(status_code=404, content={"msg": "Archivo no encontrado"})
    return FileResponse(doc.file_path, media_type="application/pdf", filename=os.path.basename(doc.file_path))