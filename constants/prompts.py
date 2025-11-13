DOCUMENT_EXTRACTION_PROMPT = """
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