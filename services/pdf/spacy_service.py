import spacy
from services.pdf.pdf_service import extract_text_from_pdf, split_text_by_words

nlp = spacy.load("es_core_news_lg")

def extraer_personas_del_pdf(pdf_path, to_lower=True):
    """
    Extrae personas del PDF usando Spacy NER.
    """
    texto = extract_text_from_pdf(pdf_path, to_lower=to_lower)
    chunks = split_text_by_words(texto, chunk_size=1000)
    
    personas = []
    for chunk in chunks:
        documento = nlp(chunk)
        for ent in documento.ents:
            if ent.label_ == "PER":
                personas.append(ent.text)
    
    return personas

def extraer_personas_ambos_casos(pdf_path):
    """
    Extrae personas en minúsculas y en caso normal, devuelve ambas listas únicas.
    """
    personas_minusculas = extraer_personas_del_pdf(pdf_path, to_lower=True)
    personas_normal = extraer_personas_del_pdf(pdf_path, to_lower=False)
    
    personas_minusculas_unicos = sorted(set(personas_minusculas))
    personas_normal_unicos = sorted(set(personas_normal))
    
    return personas_minusculas_unicos, personas_normal_unicos