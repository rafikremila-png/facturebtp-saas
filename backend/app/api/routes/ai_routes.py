"""
AI Routes
API endpoints for AI-powered features
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
import uuid

from app.api.deps import get_current_user
from app.core.config import settings
from app.services.ai_document_service import ai_document_service

router = APIRouter(prefix="/ai", tags=["AI Features"])


class QuoteGenerationRequest(BaseModel):
    project_description: str
    project_type: Optional[str] = None
    surface_area: Optional[float] = None
    location: Optional[str] = None


@router.post("/analyze-document")
async def analyze_document(
    file: UploadFile = File(...),
    analysis_type: str = "invoice",
    user: dict = Depends(get_current_user)
):
    """Analyze a PDF document using AI"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")
    
    file_id = str(uuid.uuid4())
    file_path = settings.PDFS_PATH / f"{file_id}.pdf"
    
    try:
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        result = await ai_document_service.analyze_pdf(str(file_path), analysis_type)
        return result
        
    finally:
        if file_path.exists():
            file_path.unlink()


@router.post("/analyze-plan")
async def analyze_construction_plan(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Analyze a construction plan PDF"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")
    
    file_id = str(uuid.uuid4())
    file_path = settings.PDFS_PATH / f"{file_id}.pdf"
    
    try:
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return await ai_document_service.analyze_construction_plan(str(file_path))
        
    finally:
        if file_path.exists():
            file_path.unlink()


@router.post("/generate-quote")
async def generate_quote_items(
    data: QuoteGenerationRequest,
    user: dict = Depends(get_current_user)
):
    """Generate quote items based on project description"""
    return await ai_document_service.generate_quote_items(
        project_description=data.project_description,
        project_type=data.project_type,
        surface_area=data.surface_area,
        location=data.location
    )


@router.post("/estimate-cost")
async def estimate_project_cost(
    project_description: str,
    surface_area: Optional[float] = None,
    project_type: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Estimate project cost using AI"""
    return await ai_document_service.estimate_project_cost(
        project_description=project_description,
        surface_area=surface_area,
        project_type=project_type
    )
