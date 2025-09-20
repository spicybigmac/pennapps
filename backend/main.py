from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import dotenv
dotenv.load_dotenv()

from api_routes import mongodb
# Import routers
from api_routes.ai_routes import router as ai_router
from api_routes.ais_routes import router as ais_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Collect AIS data from GFW API
    try:
        from ais_collector import collect_ais_data
        import os
        
        api_key = os.getenv("GFW_API_KEY")
        if api_key:
            print("Collecting initial AIS data from Global Fishing Watch API...")
            await collect_ais_data(api_key, days_back=1)
            print("AIS data collection completed")
        else:
            print("GFW_API_KEY not set - skipping AIS data collection")
    except Exception as e:
        print(f"Error collecting AIS data: {e}")
    
    yield
    
    # Shutdown: Clean up if needed
    pass

app = FastAPI(
    title="PennApps Backend API",
    description="Backend API for PennApps hackathon project with AI integrations",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",  # Additional frontend port if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ai_router)
app.include_router(ais_router)

# Main API routes defined directly in main.py
class Message(BaseModel):
    prompt: str

def serialize_doc(doc):
    """Helper function to serialize MongoDB documents"""
    doc["_id"] = str(doc["_id"])
    doc["lat"] = doc["latitude"]
    del doc["latitude"]
    doc["lng"] = doc["longitude"]
    del doc["longitude"]
    return doc


@app.get("/")
async def root():
    return {
        "message": "PennApps Backend API",
        "status": "running",
        "docs": "/docs",
        "health": "/api/ai/health"
    }

@app.get("/api/getPositions")
async def get_positions():
    """
    Get all position data from the database
    """
    docs = mongodb.getPos()
    docs = [serialize_doc(x) for x in docs]
    return docs

if (__name__ == "__main__"):
    uvicorn.run("main:app", reload=True)