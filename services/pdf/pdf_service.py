import pdfplumber
import re

def extract_text_from_pdf(file, to_lower=False):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    # Limpia saltos de línea y espacios extra
    text = re.sub(r'\s+', ' ', text).strip()
    if to_lower:
        return text.lower()
    return text

def split_text_by_words(text, chunk_size=1000):
    """Divide el texto en chunks sin cortar palabras"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1  # +1 por el espacio
        if current_length + word_length > chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks