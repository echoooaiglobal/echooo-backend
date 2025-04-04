from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes.api.v0.instagram import router as instagram_router
from routes.api.v0.clients import router as clients_router
from config.database import engine
from app.Models.Client import Base
from routes.api.v0.influencers import router as influencers_router
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Actions to perform during startup
    Base.metadata.create_all(bind=engine)
    yield
    # Actions to perform during shutdown (if any)

app = FastAPI(lifespan=lifespan)


# Allow requests from your Next.js frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.18.74:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)


app.include_router(instagram_router)
# app.include_router(instagram_router, prefix="/api/v0", tags=["Instagram Bot"])
app.include_router(clients_router, prefix="/api/v0", tags=["clients"])
app.include_router(influencers_router, prefix="/api/v0", tags=["influencers"])
