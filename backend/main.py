from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import dotenv
import os
import google.generativeai as genai
from exa_py import Exa
from cleanjson import convertJSON

dotenv.load_dotenv()

# Moved mongodb import to be relative if it's in the same api_routes folder
# If mongodb is in the project root, just `import mongodb`
from api_routes import mongodb

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# Configure Exa
exa = Exa(api_key=os.getenv("EXA_API_KEY"))

# Pydantic Models (moved from ai_routes.py)
class ChatRequest(BaseModel):
    prompt: str
    user_id: str = "anonymous"

class SearchRequest(BaseModel):
    query: str
    num_results: int = 5
    include_domains: list[str] = []
    exclude_domains: list[str] = []

class EnhancedChatRequest(BaseModel):
    prompt: str
    user_id: str = "anonymous"
    use_web_search: bool = False
    search_query: str = ""

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup: Collect AIS data from GFW API
#     try:
#         from ais_collector import collect_ais_data
        
#         api_key = os.getenv("GFW_API_KEY")
#         if api_key:
#             print("Collecting initial AIS data from Global Fishing Watch API...")
#             await collect_ais_data(api_key, days_back=1)
#             print("AIS data collection completed")
#         else:
#             print("GFW_API_KEY not set - skipping AIS data collection")
#     except Exception as e:
#         print(f"Error collecting AIS data: {e}")
    
#     yield
    
#     # Shutdown: Clean up if needed
#     pass

app = FastAPI(
    title="PennApps Backend API",
    description="Backend API for PennApps hackathon project with AI integrations",
    version="1.0.0",
    # lifespan=lifespan
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

# If you still have ais_routes, you would include it like this:
# from api_routes.ais_routes import router as ais_router
# app.include_router(ais_router)


# Main API routes defined directly in main.py

# Health Check (moved from ai_routes.py)
@app.get("/api/ai/health")
async def health_check():
    """
    Health check endpoint for AI services
    """
    try:
        # Test Gemini connection
        gemini_status = "ok"
        try:
            test_response = model.generate_content("Hello")
            if not test_response.candidates:
                gemini_status = "error"
        except Exception:
            gemini_status = "error"
        
        # Test Exa connection (simple check)
        exa_status = "ok" if os.getenv("EXA_API_KEY") else "no_api_key"
        
        return {
            "status": "healthy",
            "services": {
                "gemini": gemini_status,
                "exa": exa_status
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Gemini Chat (moved from ai_routes.py)
@app.post("/api/ai/gemini/chat")
async def gemini_chat(request: ChatRequest):
    """
    Chat with Gemini AI model
    """

    # try:
    response = model.generate_content(request.prompt)
    
    if response.candidates and response.candidates[0].content:
        ai_response = response.candidates[0].content.parts[0].text
    else:
        ai_response = "I couldn't generate a response. Please try again."
    
    # Log the conversation
    mongodb.logPrompt(request.user_id, request.prompt, ai_response)
    
    return convertJSON(ai_response)
    
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# Exa Search (moved from ai_routes.py)
@app.post("/api/ai/exa/search")
async def exa_search(request: SearchRequest):
    """
    Search the web using Exa API
    """
    try:
        search_params = {
            "query": request.query,
            "num_results": request.num_results,
            "type": "neural",
            "use_autoprompt": True,
        }
        
        if request.include_domains:
            search_params["include_domains"] = request.include_domains
        
        if request.exclude_domains:
            search_params["exclude_domains"] = request.exclude_domains
        
        results = exa.search(**search_params)
        
        formatted_results = []
        for result in results.results:
            formatted_results.append({
                "title": result.title,
                "url": result.url,
                "score": result.score,
                "published_date": result.published_date
            })
        
        return {
            "query": request.query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in exa search: {str(e)}")

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