import os
from dotenv import load_dotenv
import google.generativeai as genai
from constants.prompts import RESUME_TECHNICAL_PROMPT

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_document(text, prompt=RESUME_TECHNICAL_PROMPT):
    full_prompt = prompt + "\n" + text
    try:
        response = genai.GenerativeModel("models/gemini-2.5-flash-lite").generate_content(full_prompt)
        resumen = response.text.strip()
        # Limpieza opcional si Gemini devuelve markdown
        if resumen.startswith("```"):
            resumen = resumen.split("```")[1]
        return resumen
    except Exception as e:
        print("Error al resumir con Gemini:", e)
        return ""