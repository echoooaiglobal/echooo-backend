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
from app.Models import Base 
from app.Utils.Logger import logger
from app.Utils.db_init import initialize_all_default_data
from routes.api.v0 import (
    auth, campaign_influencers, communication_channels, influencers, platforms, companies,
    categories, campaigns, statuses, message_templates, system_settings, users, roles, permissions, 
    influencer_contacts, results, profile_analytics, orders,
    agent_assignments, assigned_influencers, influencer_assignment_histories, agent_social_connections,
    campaign_lists, outreach_agents, bulk_assignments
)
from routes.api.v0 import oauth
from app.Utils.startup import initialize_background_services, shutdown_background_services
from routes.api.v0 import scheduler_management  #comprehensive scheduler management API

# Create FastAPI application context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Actions to perform during startup
    # Base.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=engine, checkfirst=True)
    logger.info(f"{settings.APP_NAME} API starting up...")
    
    # Initialize ALL default data
    db = next(get_db())
    initialize_all_default_data(db)

    # Initialize background services
    await initialize_background_services()
    
    yield

    # Actions to perform during shutdown
    logger.info(f"{settings.APP_NAME} API shutting down...")

    # Shutdown background services
    await shutdown_background_services()
    
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
app.include_router(categories.router, prefix=settings.API_V0_STR)
app.include_router(platforms.router, prefix=settings.API_V0_STR)
app.include_router(influencers.router, prefix=settings.API_V0_STR)
app.include_router(campaigns.router, prefix=settings.API_V0_STR)
app.include_router(campaign_lists.router, prefix=settings.API_V0_STR)
app.include_router(statuses.router, prefix=settings.API_V0_STR)
app.include_router(communication_channels.router, prefix=settings.API_V0_STR)
app.include_router(campaign_influencers.router, prefix=settings.API_V0_STR)
app.include_router(message_templates.router, prefix=settings.API_V0_STR)
app.include_router(influencer_contacts.router, prefix=settings.API_V0_STR)
app.include_router(results.router, prefix=settings.API_V0_STR)
app.include_router(profile_analytics.router, prefix=settings.API_V0_STR)
app.include_router(orders.router, prefix=settings.API_V0_STR)
app.include_router(oauth.router, prefix=settings.API_V0_STR)
app.include_router(scheduler_management.router, prefix=settings.API_V0_STR)
app.include_router(agent_assignments.router, prefix=settings.API_V0_STR)
app.include_router(assigned_influencers.router, prefix=settings.API_V0_STR)
app.include_router(influencer_assignment_histories.router, prefix=settings.API_V0_STR)
app.include_router(system_settings.router, prefix=settings.API_V0_STR)
app.include_router(agent_social_connections.router, prefix=settings.API_V0_STR)
app.include_router(outreach_agents.router, prefix=settings.API_V0_STR)
app.include_router(bulk_assignments.router, prefix=settings.API_V0_STR)

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "0.1.0"
    }