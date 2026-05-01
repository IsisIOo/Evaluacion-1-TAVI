import json
import re
from datetime import datetime
from typing import Any, Dict

from app.core.llm_manager import get_gemini_client, get_gemini_model
from app.schemas.cv_request import CVRequest


MODEL_PROMPT_TEMPLATE = """
Eres un generador de curriculum vitae en formato JSON inspirado en la plantilla Europass.
Recibes los datos del candidato y debes devolver un único objeto JSON válido.
No agregues texto adicional, no uses marcadores Markdown ni etiquetas HTML.

La estructura de salida debe ser:
{
  "personal_info": {
    "full_name": "",
    "professional_title": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "github": ""
  },
  "professional_summary": "",
  "career_objective": "",
  "experience": [
    {
      "job_title": "",
      "company": "",
      "start_date": "",
      "end_date": "",
      "location": "",
      "responsibilities": [""],
      "achievements": [""]
    }
  ],
  "education": [
    {
      "degree": "",
      "institution": "",
      "start_date": "",
      "end_date": "",
      "location": "",
      "description": ""
    }
  ],
  "skills": {
    "technical": [""],
    "soft": [""],
    "other": [""]
  },
  "languages": [
    {
      "language": "",
      "level": ""
    }
  ],
  "certifications": [
    {
      "title": "",
      "issuer": "",
      "date": "",
      "description": ""
    }
  ],
  "additional_information": ""
}
"""


def _sanitize_llm_json(text: str) -> str:
    if not text or not isinstance(text, str):
        raise ValueError("La respuesta del modelo no contiene texto válido.")

    candidate = text.strip()
    match = re.search(r"(\{.*\})", candidate, re.S)
    if match:
        candidate = match.group(1)

    candidate = candidate.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    return candidate


def _parse_llm_response(text: str) -> Dict[str, Any]:
    cleaned = _sanitize_llm_json(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"No se pudo parsear la respuesta JSON del modelo: {error}\nTexto recibido: {cleaned}"
        )


def _build_prompt(request: CVRequest) -> str:
    input_data = json.dumps(request.model_dump(exclude_none=True), ensure_ascii=False, indent=2)
    return (
        f"Genera un curriculum vitae en JSON usando el siguiente objeto de entrada:\n\n{input_data}\n\n"
        "Asegúrate de construir un CV completo con estilo Europass. Si faltan datos, completa la información de manera coherente "
        "a partir de los campos proporcionados. No agregues texto fuera del JSON. Usa las claves exactas del ejemplo de la estructura."
    )


class CVGeneratorService:
    @staticmethod
    def generate_cv_json(request: CVRequest) -> Dict[str, Any]:
        gemini_client = get_gemini_client()
        model_name = get_gemini_model()

        prompt = _build_prompt(request)
        full_prompt = MODEL_PROMPT_TEMPLATE + "\n" + prompt

        model = gemini_client.GenerativeModel(model_name)
        response = model.generate_content(full_prompt)

        raw_output = response.text
        cv_json = _parse_llm_response(raw_output)

        return {
            "cv": cv_json,
            "model_used": model_name,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "raw_output": raw_output,
        }
