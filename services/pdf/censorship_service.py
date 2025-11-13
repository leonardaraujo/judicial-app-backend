import fitz  # PyMuPDF
import unicodedata

def remover_tildes(texto):
    """Remueve tildes de un texto."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def censurar_pdf_con_rectangulos(input_pdf_path, output_pdf_path, palabras_a_censurar):
    """
    Censura visualmente todas las palabras de la lista en el PDF, cubriéndolas con un rectángulo negro.
    Busca variantes con/sin tildes y mayúsculas/minúsculas.
    """
    doc = fitz.open(input_pdf_path)
    for page in doc:
        for palabra in palabras_a_censurar:
            # Genera variantes de búsqueda
            variantes = set()
            variantes.add(palabra)  # Original
            variantes.add(palabra.lower())  # Minúsculas
            variantes.add(palabra.upper())  # Mayúsculas
            variantes.add(remover_tildes(palabra))  # Sin tildes
            variantes.add(remover_tildes(palabra).lower())  # Sin tildes, minúsculas
            variantes.add(remover_tildes(palabra).upper())  # Sin tildes, mayúsculas
            
            for variante in variantes:
                areas = page.search_for(variante, quads=True)
                for area in areas:
                    page.draw_rect(area.rect, color=(0, 0, 0), fill=(0, 0, 0))
    
    doc.save(output_pdf_path)