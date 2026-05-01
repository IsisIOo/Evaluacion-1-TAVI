from fastapi import APIRouter, HTTPException

from app.schemas.cv_request import CVRequest
from app.schemas.cv_response import CVResponse
from app.services.llm_service import CVGeneratorService

router = APIRouter(prefix="/api/v1/cv", tags=["cv"])


@router.post("/generate", response_model=CVResponse)
async def generate_cv_endpoint(request: CVRequest):
    try:
        result = CVGeneratorService.generate_cv_json(request)
        return CVResponse(
            cv=result["cv"],
            model=result["model_used"],
            generated_at=result["generated_at"],
            raw_output=result.get("raw_output"),
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
