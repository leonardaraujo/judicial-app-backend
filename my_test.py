import time
from services.pdf.spacy_service import extraer_personas_ambos_casos
from services.pdf.pdf_service import extract_text_from_pdf, split_text_by_words
from services.pdf.name_filter_service import (
    filtrar_nombres,
    mostrar_reporte_simplificado,
    cargar_dataset_nombres,
    normalizar_nombre,
)
from services.pdf.censorship_service import censurar_pdf_con_rectangulos

# Centraliza el path del PDF
PDF_PATH = "uploaded_docs/caso_3.pdf"
PDF_CENSURADO_PATH = "uploaded_docs/caso_censurado.pdf"

# ============================================================================
# EXTRACCIÓN DE PERSONAS
# ============================================================================

print("🔍 Extrayendo personas del PDF...\n")

start = time.time()
personas_minusculas_unicos, personas_normal_unicos = extraer_personas_ambos_casos(PDF_PATH)
end = time.time()

# Unifica ambas listas
todas_personas = sorted(set(personas_minusculas_unicos + personas_normal_unicos))

# Deduplicar por normalización
personas_normalizadas = {}
for persona in todas_personas:
    persona_norm = normalizar_nombre(persona)
    if persona_norm not in personas_normalizadas:
        personas_normalizadas[persona_norm] = persona

todas_personas_unicas = list(personas_normalizadas.values())

print(f"✅ Total de personas únicas detectadas: {len(todas_personas_unicas)}")
print(f"⏱️  Tiempo de extracción: {end - start:.2f}s\n")

# ============================================================================
# CARGA DE DATASET
# ============================================================================

print("📚 Cargando dataset de nombres...\n")
dataset_info = cargar_dataset_nombres("data/name_surnames_normalizated.csv")

# ============================================================================
# FILTRADO Y VALIDACIÓN
# ============================================================================

print("🔎 Filtrando y validando nombres...\n")
resultado = filtrar_nombres(
    todas_personas_unicas,
    dataset_info,
    personas_minusculas_unicos,
    personas_normal_unicos,
    umbral_minimo=8
)

# Mostrar reporte
mostrar_reporte_simplificado(resultado)

# ============================================================================
# CENSURA DEL PDF
# ============================================================================

print("🔐 Censurando PDF...\n")

nombres_a_censurar = resultado["nombres_originales_a_censurar"]

censurar_pdf_con_rectangulos(
    PDF_PATH,
    PDF_CENSURADO_PATH,
    nombres_a_censurar
)

print(f"✅ PDF censurado generado: {PDF_CENSURADO_PATH}")
print(f"📋 Total de nombres censurados: {len(nombres_a_censurar)}\n")
print("=" * 120)