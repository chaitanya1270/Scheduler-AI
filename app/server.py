# app/main.py
import os
from fastapi import FastAPI
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi.concurrency import asynccontextmanager
from app.db.database import init_db
from app.v1.calendar.routes import calendar_router
from app.v1.notifications.service import start_scheduler
from app.v1.schedule.routes import scheduler_router
from app.v1.oauth.routes import oauth_router
from app.v1.notifications.routes import notifications_router
from app.v1.communication.routes import communication_router
from app.v1.schedule_demo.routes import schedule_demo_router
from app.v1.calendar_demo.routes import calendar_demo_router
from app.v1.alternative_suggestions.routes import  alternative_suggestions_router
from app.v1.rsvp.routes import rsvp_router
from starlette.middleware.cors import CORSMiddleware



app = FastAPI()

# Define allowed origins
origins = [
    "http://localhost",
    "http://localhost:3001", 
    "http://localhost:3000" # If you're running a frontend on this port
    "https://yourfrontenddomain.com",  # Add your frontend domain here
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies to be sent
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize the database
init_db()

# Include routes for both services
app.include_router(calendar_router, prefix="/v1/calendar", tags=["Calendar Capture Service"])
app.include_router(scheduler_router, prefix="/v1/scheduler", tags=["Smart Meeting Scheduler"])
app.include_router(oauth_router, prefix='', tags=['OAuth'])
app.include_router(notifications_router, prefix='/api/v1/notifications')
app.include_router(communication_router, prefix='/api/v1/communication')
app.include_router(rsvp_router, prefix='/api/v1/rsvp')
app.include_router(schedule_demo_router, prefix='/api/v1/schedule_demo')
app.include_router(alternative_suggestions_router, prefix='/api/v1/alternative_suggestions')
app.include_router(calendar_demo_router,prefix='/api/v1')

def run_migrations():
    # Create Alembic configuration
    script_location = os.path.join(os.path.dirname(__file__), 'alembic')
    alembic_cfg = AlembicConfig(os.path.join(script_location, 'alembic.ini'))
    alembic_cfg.set_main_option('script_location', script_location)
    
    # Generate new migration script
    command.revision(alembic_cfg, autogenerate=True, message="Auto migration")
    
    # Apply the migrations
    command.upgrade(alembic_cfg, 'head')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Update DB models
    run_migrations()
    start_scheduler()
    yield
    # Clean up the ML models and release the resources
    # ml_models.clear()

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Calendar Capture and Smart Meeting Scheduler Service!"}
