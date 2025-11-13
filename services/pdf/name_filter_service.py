import re
import pandas as pd
from pybloom_live import BloomFilter
from constants.constants import BLACKLIST


# ============================================================================
# FUNCIONES DE NORMALIZACIÓN
# ============================================================================

def normalizar_nombre(nombre):
    """Normaliza un nombre: mayúsculas, sin tildes, sin caracteres especiales."""
    mapeo_tildes = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N",
    }
    
    nombre_normalizado = str(nombre).strip().upper()
    for tilde, sin_tilde in mapeo_tildes.items():
        nombre_normalizado = nombre_normalizado.replace(tilde, sin_tilde)
    nombre_normalizado = re.sub(r"[^A-Z\s]", "", nombre_normalizado)
    nombre_normalizado = re.sub(r"\s+", " ", nombre_normalizado).strip()
    
    return nombre_normalizado


def limpiar_nombre_blacklist(nombre_normalizado):
    """Elimina palabras de la blacklist del nombre normalizado."""
    blacklist_normalizado = set(normalizar_nombre(b) for b in BLACKLIST)
    palabras = nombre_normalizado.split()
    palabras_filtradas = [p for p in palabras if p not in blacklist_normalizado]
    return " ".join(palabras_filtradas).strip()


# ============================================================================
# FUNCIONES DE CARGA DE DATOS
# ============================================================================

def cargar_dataset_nombres(ruta_csv):
    """Carga dataset CSV y crea Bloom Filter + índice por palabra."""
    df = pd.read_csv(ruta_csv)
    nombres_normalizados = set(normalizar_nombre(n) for n in df["name"].dropna().unique())
    
    bloom_filter = BloomFilter(capacity=len(nombres_normalizados), error_rate=0.001)
    for nombre in nombres_normalizados:
        bloom_filter.add(nombre)
    
    nombres_por_palabra = {}
    for nombre in nombres_normalizados:
        for palabra in nombre.split():
            if palabra not in nombres_por_palabra:
                nombres_por_palabra[palabra] = []
            nombres_por_palabra[palabra].append(nombre)
    
    return {
        "bloom_filter": bloom_filter,
        "nombres_set": nombres_normalizados,
        "nombres_por_palabra": nombres_por_palabra,
        "dataframe": df,
    }


# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================

def aplicar_regex_filtro(nombre):
    """Valida que el nombre tenga al menos 2 palabras."""
    pattern = re.compile(r"^[A-Z]+(?:\s[A-Z]+)+$")
    return pattern.match(nombre) is not None


def verificar_coincidencia_palabras(nombre_normalizado, dataset_info):
    """Verifica qué palabras del nombre están en el dataset."""
    palabras_candidato = nombre_normalizado.split()
    nombres_por_palabra = dataset_info["nombres_por_palabra"]
    palabras_encontradas = 0
    palabras_match = []
    detalles_palabras = []
    
    for palabra in palabras_candidato:
        if palabra in nombres_por_palabra:
            palabras_encontradas += 1
            palabras_match.append(palabra)
            detalles_palabras.append(f"✓ {palabra} - ENCONTRADA en dataset")
        else:
            detalles_palabras.append(f"✗ {palabra} - NO encontrada en dataset")
    
    porcentaje = (palabras_encontradas / len(palabras_candidato) * 100) if palabras_candidato else 0
    return palabras_encontradas, len(palabras_candidato), porcentaje, palabras_match, detalles_palabras


# ============================================================================
# FUNCIONES DE SCORING
# ============================================================================

def calcular_scoring(candidatos, dataset_info, personas_minusculas, personas_normal):
    """Calcula scoring para cada candidato."""
    bloom_filter = dataset_info["bloom_filter"]
    personas_minusculas_norm = set(normalizar_nombre(n) for n in personas_minusculas)
    personas_normal_norm = set(normalizar_nombre(n) for n in personas_normal)
    scoring_detallado = {}
    
    for candidato in candidatos:
        candidato_norm = normalizar_nombre(candidato)
        candidato_limpio = limpiar_nombre_blacklist(candidato_norm)
        palabras_eliminadas = [p for p in candidato_norm.split() if p not in candidato_limpio.split()]
        
        # Validar mínimo 2 palabras
        palabras_limpias = candidato_limpio.split()
        if not candidato_limpio or len(palabras_limpias) < 2:
            scoring_detallado[candidato] = {
                "score": -10,
                "detalles": ["Nombre inválido: debe tener al menos 2 palabras después de limpiar blacklist"],
                "detalles_palabras": [],
                "admitido": False,
                "en_dataset": False,
                "en_minusculas": False,
                "en_normal": False,
                "coincidencia_palabras_pct": 0,
                "palabras_sugeridas": [],
                "palabras_eliminadas": palabras_eliminadas,
                "candidato_limpio": candidato_limpio,
            }
            continue
        
        score = 0
        detalles = []
        palabras_sugeridas = []
        
        # Criterio 1: Nombre completo en dataset
        en_dataset = candidato_limpio in bloom_filter
        if en_dataset:
            score += 10
            detalles.append("Nombre completo en dataset (+10)")
        else:
            detalles.append("Nombre completo NO en dataset")
        
        # Criterio 2: Coincidencia palabra por palabra
        palabras_encontradas, palabras_totales, porcentaje, palabras_match, detalles_palabras = verificar_coincidencia_palabras(
            candidato_limpio, dataset_info
        )
        if porcentaje >= 50:
            score += 5
            detalles.append(f"Coincidencia de palabras: {palabras_encontradas}/{palabras_totales} ({porcentaje:.0f}%) (+5)")
        else:
            detalles.append(f"Coincidencia de palabras: {palabras_encontradas}/{palabras_totales} ({porcentaje:.0f}%) - Insuficiente")
            if palabras_match:
                palabras_sugeridas = palabras_match
        
        # Criterio 3: En análisis minúsculas
        en_minusculas = candidato_limpio in personas_minusculas_norm
        if en_minusculas:
            score += 5
            detalles.append("En análisis minúsculas (+5)")
        
        # Criterio 4: En análisis normal
        en_normal = candidato_limpio in personas_normal_norm
        if en_normal:
            score += 5
            detalles.append("En análisis normal (+5)")
        
        # Criterio 5: Formato válido
        if aplicar_regex_filtro(candidato_limpio):
            score += 3
            detalles.append("Formato válido (2+ palabras) (+3)")
        else:
            detalles.append("Formato inválido")
        
        scoring_detallado[candidato] = {
            "score": score,
            "detalles": detalles,
            "detalles_palabras": detalles_palabras,
            "admitido": score >= 8,
            "en_dataset": en_dataset,
            "en_minusculas": en_minusculas,
            "en_normal": en_normal,
            "coincidencia_palabras_pct": porcentaje,
            "palabras_sugeridas": palabras_sugeridas,
            "palabras_eliminadas": palabras_eliminadas,
            "candidato_limpio": candidato_limpio,
        }
    
    return scoring_detallado


def filtrar_nombres(candidatos, dataset_info, personas_minusculas, personas_normal, umbral_minimo=8):
    """Filtra nombres según umbral mínimo."""
    scoring = calcular_scoring(candidatos, dataset_info, personas_minusculas, personas_normal)
    nombres_admitidos = [n for n, info in scoring.items() if info["score"] >= umbral_minimo]
    nombres_descartados = [n for n, info in scoring.items() if info["score"] < umbral_minimo]
    
    return {
        "scoring_detallado": scoring,
        "nombres_admitidos": sorted(nombres_admitidos),
        "nombres_descartados": sorted(set(nombres_descartados)),
        "total_admitidos": len(nombres_admitidos),
        "total_descartados": len(set(nombres_descartados)),
        "nombres_originales_a_censurar": nombres_admitidos,  # ← AGREGADO
    }


# ============================================================================
# FUNCIONES DE REPORTE
# ============================================================================

def mostrar_reporte_simplificado(resultado):
    """Muestra reporte simplificado de nombres admitidos y descartados."""
    import sys
    sys.stdout.flush()
    
    print("\n" + "=" * 120)
    print("REPORTE DE FILTRADO DE NOMBRES (UMBRAL: 8 PUNTOS)")
    print("=" * 120)
    
    # Nombres admitidos
    print(f"\n✓ NOMBRES ADMITIDOS ({resultado['total_admitidos']}):")
    print("-" * 120)
    for nombre in resultado["nombres_admitidos"]:
        info = resultado["scoring_detallado"][nombre]
        candidato_limpio = info.get("candidato_limpio", nombre)
        palabras_eliminadas = info.get("palabras_eliminadas", [])
        print(f"  {nombre} → (limpio: {candidato_limpio}) [{info['score']} pts]")
        if palabras_eliminadas:
            print(f"    ⚠️  Palabras eliminadas (blacklist): {', '.join(palabras_eliminadas)}")
        for detalle in info["detalles"]:
            print(f"    • {detalle}")
        print()
    
    # Nombres descartados
    nombres_descartados = resultado["nombres_descartados"]
    print(f"\n✗ NOMBRES DESCARTADOS ({len(nombres_descartados)}):")
    print("-" * 120)
    for nombre in nombres_descartados:
        info = resultado["scoring_detallado"][nombre]
        candidato_limpio = info.get("candidato_limpio", nombre)
        palabras_eliminadas = info.get("palabras_eliminadas", [])
        print(f"  {nombre} → (limpio: {candidato_limpio}) [{info['score']} pts]")
        if palabras_eliminadas:
            print(f"    ⚠️  Palabras eliminadas (blacklist): {', '.join(palabras_eliminadas)}")
        for detalle in info["detalles"]:
            print(f"    • {detalle}")
        print()
    
    print("=" * 120)
    print(f"RESUMEN: {resultado['total_admitidos']} admitidos | {resultado['total_descartados']} descartados")
    print("=" * 120 + "\n")
    sys.stdout.flush()