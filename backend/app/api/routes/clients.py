"""
Client Routes
CRUD operations for clients
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.database import get_db
from app.services.client_service import get_client_service
from app.schemas.schemas import (
    ClientCreate, ClientUpdate, ClientResponse
)
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new client."""
    client_service = get_client_service(db)
    client = await client_service.create_client(current_user["id"], client_data)
    return ClientResponse.model_validate(client)


@router.get("", response_model=List[ClientResponse])
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    client_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all clients for the current user."""
    client_service = get_client_service(db)
    clients = await client_service.list_clients(
        user_id=current_user["id"],
        skip=skip,
        limit=limit,
        search=search,
        client_type=client_type
    )
    return [ClientResponse.model_validate(c) for c in clients]


@router.get("/stats")
async def get_clients_with_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all clients with invoice/quote statistics."""
    client_service = get_client_service(db)
    return await client_service.get_clients_with_stats(current_user["id"])


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific client."""
    client_service = get_client_service(db)
    client = await client_service.get_client_by_id(client_id, current_user["id"])
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )
    
    return ClientResponse.model_validate(client)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    client_data: ClientUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a client."""
    client_service = get_client_service(db)
    client = await client_service.update_client(client_id, current_user["id"], client_data)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )
    
    return ClientResponse.model_validate(client)


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a client."""
    client_service = get_client_service(db)
    success = await client_service.delete_client(client_id, current_user["id"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )
    
    return {"message": "Client supprimé"}


@router.post("/{client_id}/portal-token")
async def generate_portal_token(
    client_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a portal access token for a client."""
    client_service = get_client_service(db)
    token = await client_service.generate_portal_token(client_id, current_user["id"])
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )
    
    return {
        "token": token,
        "expires_in_days": 7,
        "message": "Token de portail généré"
    }
