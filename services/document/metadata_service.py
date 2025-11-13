import json
from constants.prompts import DOCUMENT_EXTRACTION_PROMPT
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_metadata(text):
    prompt = DOCUMENT_EXTRACTION_PROMPT + text
    response = genai.GenerativeModel("models/gemini-2.5-flash-lite").generate_content(
        prompt
    )
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
            "cited_jurisprudence": [],
        }
    return data