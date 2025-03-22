from sqlalchemy.orm import Session
from app.Repositories.ClientRepository import ClientRepository
from app.Schemas.client import ClientCreate

class ClientService:
    def __init__(self, db: Session):
        self.client_repo = ClientRepository(db)

    def create_client(self, client: ClientCreate):
        return self.client_repo.create_client(client)

    def get_client(self, client_id: int):
        return self.client_repo.get_client(client_id)

    def get_clients(self, skip: int = 0, limit: int = 10):
        return self.client_repo.get_clients(skip, limit)

    def update_client(self, client_id: int, client: ClientCreate):
        return self.client_repo.update_client(client_id, client)

    def delete_client(self, client_id: int):
        return self.client_repo.delete_client(client_id)
