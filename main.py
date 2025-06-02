# /main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import time
from datetime import datetime
from contextlib import asynccontextmanager
from config.settings import settings
from config.database import get_db, engine
from app.Models import Base  # Import Base from our new Models package
from app.Utils.Logger import logger
from app.Utils.db_init import initialize_default_roles_permissions
from routes.api.v0 import (
    auth, campaign_list_members, instagram, influencers, platforms, companies,
    categories, campaigns, statuses, message_channels, agents, list_assignments, message_templates,
    users, roles, permissions
)

# Create FastAPI application context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Actions to perform during startup
    Base.metadata.create_all(bind=engine)
    logger.info(f"{settings.APP_NAME} API starting up...")
    
    # Initialize default roles and permissions
    db = next(get_db())
    initialize_default_roles_permissions(db)
    
    yield
    
    # Actions to perform during shutdown
    logger.info(f"{settings.APP_NAME} API shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Influencer Marketing Platform API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host
    
    # Process request
    try:
        response = await call_next(request)
        
        # Log request details
        process_time = time.time() - start_time
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Client: {client_ip} - "
            f"Status: {response.status_code} - "
            f"Process Time: {process_time:.4f}s"
        )
        
        return response
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )

# Include routers
app.include_router(auth.router, prefix=settings.API_V0_STR)
app.include_router(users.router, prefix=settings.API_V0_STR)
app.include_router(roles.router , prefix=settings.API_V0_STR) 
app.include_router(permissions.router, prefix=settings.API_V0_STR)
app.include_router(companies.router, prefix=settings.API_V0_STR)
app.include_router(instagram.router, prefix=settings.API_V0_STR, tags=["Instagram Bot"])
app.include_router(categories.router, prefix=settings.API_V0_STR)
app.include_router(platforms.router, prefix=settings.API_V0_STR)
app.include_router(influencers.router, prefix=settings.API_V0_STR)
app.include_router(campaigns.router, prefix=settings.API_V0_STR)
app.include_router(statuses.router, prefix=settings.API_V0_STR)
app.include_router(message_channels.router, prefix=settings.API_V0_STR)
app.include_router(agents.router, prefix=settings.API_V0_STR)
app.include_router(campaign_list_members.router, prefix=settings.API_V0_STR)
app.include_router(list_assignments.router, prefix=settings.API_V0_STR)
app.include_router(message_templates.router, prefix=settings.API_V0_STR)



# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "0.1.0"
    }