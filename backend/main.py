from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import dotenv
dotenv.load_dotenv("backend/.env")

from api_routes import mongodb
# Import AI router
from api_routes.ai_routes import router as ai_router

app = FastAPI(
    title="PennApps Backend API",
    description="Backend API for PennApps hackathon project with AI integrations",
    version="1.0.0"
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

# Include AI router
app.include_router(ai_router)

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
    print(docs)
    return docs

if (__name__ == "__main__"):
    uvicorn.run("main:app", reload=True)