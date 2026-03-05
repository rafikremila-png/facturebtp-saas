"""
AI PDF Analysis Routes
Endpoints for analyzing construction PDFs with Gemini
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import tempfile
import os
import logging

from app.core.database import get_db
from app.services.pdf_analysis_service import get_pdf_analysis_service
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


@router.post("/analyze-pdf")
async def analyze_pdf(
    file: UploadFile = File(...),
    analysis_type: str = Form("full"),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze a construction PDF using AI (Gemini 3 Flash)
    
    Args:
        file: PDF file to analyze
        analysis_type: Type of analysis
            - 'full': Complete analysis
            - 'materials': Extract materials only
            - 'measurements': Extract measurements only
            - 'summary': Quick summary
    
    Returns:
        Structured analysis results
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les fichiers PDF sont acceptés"
        )
    
    # Validate analysis type
    valid_types = ['full', 'materials', 'measurements', 'summary']
    if analysis_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type d'analyse invalide. Valeurs acceptées: {valid_types}"
        )
    
    # Save file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Analyze PDF
        service = get_pdf_analysis_service()
        result = await service.analyze_construction_pdf(temp_path, analysis_type)
        
        return result
        
    except Exception as e:
        logger.error(f"PDF analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        )
    finally:
        # Clean up temp file
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass


@router.post("/extract-quote-items")
async def extract_quote_items(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Extract items for quote/invoice generation from a construction PDF
    
    Returns a list of items with:
    - description
    - quantity
    - unit
    - category
    - estimated_price (optional)
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les fichiers PDF sont acceptés"
        )
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        service = get_pdf_analysis_service()
        items = await service.extract_quote_items(temp_path)
        
        return {
            "success": True,
            "items_count": len(items),
            "items": items
        }
        
    except Exception as e:
        logger.error(f"Quote extraction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'extraction: {str(e)}"
        )
    finally:
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass


@router.post("/summarize-pdf")
async def summarize_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a quick summary of a construction document
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les fichiers PDF sont acceptés"
        )
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        service = get_pdf_analysis_service()
        summary = await service.summarize_document(temp_path)
        
        return {
            "success": True,
            "summary": summary,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du résumé: {str(e)}"
        )
    finally:
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
