"""
Signature Routes
API endpoints for electronic signatures
"""
from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas.schemas import QuoteSignatureCreate, QuoteSignatureResponse
from app.services.signature_service import signature_service

router = APIRouter(prefix="/signatures", tags=["Signatures"])

# Dependency placeholder
async def get_current_user():
    pass

@router.post("/quotes/{quote_id}/generate-link")
async def generate_signature_link(
    quote_id: str, 
    client_email: str,
    user: dict = Depends(get_current_user)
):
    """Generate a signature link for a quote"""
    try:
        result = await signature_service.generate_signature_link(
            quote_id, 
            client_email, 
            user["id"]
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/validate/{token}")
async def validate_signature_token(token: str):
    """Validate a signature token and get quote details"""
    result = await signature_service.validate_signature_token(token)
    if not result:
        raise HTTPException(status_code=400, detail="Lien de signature invalide ou expiré")
    return result

@router.post("/sign/{token}")
async def sign_quote(
    token: str, 
    data: QuoteSignatureCreate,
    request: Request
):
    """Sign a quote with electronic signature"""
    try:
        # Get client info
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        result = await signature_service.sign_quote(
            token,
            data.model_dump(),
            ip_address,
            user_agent
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/quotes/{quote_id}", response_model=QuoteSignatureResponse)
async def get_signature(quote_id: str, user: dict = Depends(get_current_user)):
    """Get signature for a quote"""
    signature = await signature_service.get_signature(quote_id)
    if not signature:
        raise HTTPException(status_code=404, detail="Signature non trouvée")
    return signature

@router.get("/quotes/{quote_id}/verify")
async def verify_signature(quote_id: str):
    """Verify the authenticity of a signature"""
    result = await signature_service.verify_signature(quote_id)
    return result
