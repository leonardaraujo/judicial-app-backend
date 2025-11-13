import pandas as pd

def normalizar_texto(texto):
    mapeo_tildes = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N",
    }
    texto = str(texto).strip().upper()
    for tilde, sin_tilde in mapeo_tildes.items():
        texto = texto.replace(tilde, sin_tilde)
    return texto

def unir_nombres_apellidos(csv_surnames, csv_names_female, csv_names_male, csv_salida):
    # Cargar apellidos
    df_surnames = pd.read_csv(csv_surnames)
    apellidos = df_surnames["surname"].dropna().unique()
    apellidos_norm = [normalizar_texto(a) for a in apellidos]

    # Cargar nombres femeninos
    df_names_female = pd.read_csv(csv_names_female)
    nombres_female = df_names_female["name"].dropna().unique()
    nombres_female_norm = [normalizar_texto(n) for n in nombres_female]

    # Cargar nombres masculinos
    df_names_male = pd.read_csv(csv_names_male)
    nombres_male = df_names_male["name"].dropna().unique()
    nombres_male_norm = [normalizar_texto(n) for n in nombres_male]

    # Unir y exportar
    todos = list(set(apellidos_norm) | set(nombres_female_norm) | set(nombres_male_norm))
    df_todos = pd.DataFrame({"nombre": todos})
    df_todos.to_csv(csv_salida, index=False)
    print(f"CSV exportado: {csv_salida} ({len(df_todos)} filas)")

# Ejemplo de uso:
unir_nombres_apellidos(
    "data/surnames.csv",
    "data/female_names.csv",
    "data/male_names.csv",
    "data/nombres_apellidos_normalizados.csv",
)