from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.Services.ClientService import ClientService
from app.Schemas.client import ClientCreate, Client
from config.database import get_db

router = APIRouter()

def get_client_service(db: Session = Depends(get_db)):
    return ClientService(db)

@router.post("/", response_model=Client)
def create_client(client: ClientCreate, client_service: ClientService = Depends(get_client_service)):
    return client_service.create_client(client)

@router.get("/{client_id}", response_model=Client)
def read_client(client_id: int, client_service: ClientService = Depends(get_client_service)):
    db_client = client_service.get_client(client_id)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

@router.get("/", response_model=list[Client])
def read_clients(skip: int = 0, limit: int = 10, client_service: ClientService = Depends(get_client_service)):
    return client_service.get_clients(skip, limit)

@router.put("/{client_id}", response_model=Client)
def update_client(client_id: int, client: ClientCreate, client_service: ClientService = Depends(get_client_service)):
    db_client = client_service.update_client(client_id, client)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

@router.delete("/{client_id}", response_model=Client)
def delete_client(client_id: int, client_service: ClientService = Depends(get_client_service)):
    db_client = client_service.delete_client(client_id)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client
