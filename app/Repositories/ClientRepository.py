from sqlalchemy.orm import Session
from app.Models.Client import Client
from app.Schemas.client import ClientCreate

class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_client(self, client: ClientCreate):
        db_client = Client(**client.dict())
        self.db.add(db_client)
        self.db.commit()
        self.db.refresh(db_client)
        return db_client

    def get_client(self, client_id: int):
        return self.db.query(Client).filter(Client.id == client_id).first()

    def get_clients(self, skip: int, limit: int):
        return self.db.query(Client).offset(skip).limit(limit).all()

    def update_client(self, client_id: int, client: ClientCreate):
        db_client = self.get_client(client_id)
        if db_client:
            for key, value in client.dict().items():
                setattr(db_client, key, value)
            self.db.commit()
            self.db.refresh(db_client)
        return db_client

    def delete_client(self, client_id: int):
        db_client = self.get_client(client_id)
        if db_client:
            self.db.delete(db_client)
            self.db.commit()
        return db_client
