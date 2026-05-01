from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CVResponse(BaseModel):
    cv: Dict[str, Any] = Field(..., description="Objeto JSON con el curriculum completo generado.")
    model: str = Field(..., example="gpt-3.5-turbo")
    generated_at: str = Field(..., example="2026-05-01T12:34:56Z")
    raw_output: Optional[str] = Field(
        None,
        description="Salida original del LLM antes de parsear a JSON, útil para depuración."
    )
