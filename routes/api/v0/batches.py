from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Batch

router = APIRouter(prefix="/batches", tags=["Batches"])

@router.get("/")
def get_batches(db: Session = Depends(get_db)):
    return db.query(Batch).all()

@router.post("/")
def create_batch(batch_data: dict, db: Session = Depends(get_db)):
    new_batch = Batch(client_id=batch_data["client_id"], name=batch_data["name"])
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    return new_batch
