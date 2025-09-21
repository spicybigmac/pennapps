from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
from contextlib import asynccontextmanager
import uvicorn
import dotenv
import os
import google.generativeai as genai
from exa_py import Exa
from cleanjson import convertJSON
import random

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

# Reports generation models
class ReportSections(BaseModel):
    iuu_activity: bool = False
    ai_voice_agent: bool = False
    vessel_tracks: bool = False
    economic_impact: bool = False

class ReportGenerateRequest(BaseModel):
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    clearance: str = "Public Trust"
    sections: ReportSections

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

# Include API routers
from api_routes.ais_routes import router as ais_router
from api_routes.clean_hotspot_routes import router as clean_hotspot_router
from api_routes.image_routes import router as image_router

app.include_router(ais_router)
app.include_router(clean_hotspot_router)
app.include_router(image_router)


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

def serialize_doc(doc : dict):
    """Helper function to serialize MongoDB documents"""
    doc["_id"] = str(doc["_id"])
    doc["lat"] = doc.pop("latitude") + random.random() * 0.001
    doc["lng"] = doc.pop("longitude") + random.random() * 0.001
    doc["registered"] = doc.pop("matched")
    doc["timestamp"] = doc.pop("date")
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
    random.seed(4)
    docs = mongodb.getPos()
    docs = [serialize_doc(x) for x in docs]
    return docs


# Reports: Generate via Gemini (JSON-structured)
@app.post("/api/reports/generate")
async def generate_report(request: ReportGenerateRequest):
    """
    Generate a maritime report as HTML based on selected sections and time window.
    The HTML mirrors the style and headings of existing hardcoded reports.
    """
    try:
        # Build dynamic context from inputs
        selected_sections = []
        if request.sections.iuu_activity:
            selected_sections.append("Weekly IUU Activity Analysis")
        if request.sections.ai_voice_agent:
            selected_sections.append("AI Voice Agent Performance")
        if request.sections.vessel_tracks:
            selected_sections.append("Vessel Track Details")
        if request.sections.economic_impact:
            selected_sections.append("Economic Impact Analysis")

        time_window = []
        if request.date_start:
            time_window.append(request.date_start)
        if request.date_end:
            if request.date_start and request.date_end != request.date_start:
                time_window.append("to " + request.date_end)
            elif not request.date_start:
                time_window.append(request.date_end)
        if request.time_start:
            time_window.append(f"from {request.time_start}")
        if request.time_end:
            time_window.append(f"to {request.time_end}")
        time_window_str = " ".join(time_window) if time_window else "the selected period"

        if not selected_sections:
            # Sensible default if no boxes checked: include IUU summary only
            selected_sections = ["Weekly IUU Activity Analysis"]

        # Tone based on clearance level
        clearance_instructions = {
            "Public Trust": (
                "Adopt an accessible, non-sensitive tone suitable for public release. Avoid operationally sensitive details."
            ),
            "Confidential": (
                "Use professional language and include nuanced risk qualifiers. Avoid exact coordinates or personally identifiable information."
            ),
            "Top Secret": (
                "Use precise, analytical tone with crisp recommendations. Do not expose classified sources; summarize methods abstractly."
            ),
        }.get(request.clearance, "Use a professional tone appropriate to the audience.")

        # Construct a strict JSON-only instruction so the frontend can render charts with Recharts
        schema_block = (
            "\n"  # leading newline for readability
            "{\n"
            "  \"executiveSummary\": [\"string paragraph\", \"string paragraph\"],\n"
            "  \"sections\": [\n"
            "    {\n"
            "      \"heading\": \"string\",\n"
            "      \"content\": [\"string paragraph\"],\n"
            "      \"chart\": {\n"
            "        \"type\": \"bar|radial|pie|none\",\n"
            "        \"callout\": \"string one-sentence chart note\"\n"
            "      }\n"
            "    }\n"
            "  ]\n"
            "}\n"
        )

        sections_list = ", ".join(selected_sections)
        prompt = (
            f"You are an intelligence analyst assisting a maritime monitoring team working on IUU (Illegal, Unreported, and Unregulated) fishing detection and response. Generate a polished, decision-ready report for the PennApps operational console covering {sections_list} for {time_window_str}.\n\n"
            f"Tailor the content to the audience clearance level \"{request.clearance}\". {clearance_instructions}\n\n"
            "Return STRICT JSON ONLY (no markdown, no code fences, no prose outside JSON) that conforms to this schema:" + schema_block + "\n"
            "Rules:\n"
            "- Include ONLY the requested sections and in a logical order.\n"
            "- Use careful qualitative language; do not invent precise numbers.\n"
            "- Keep paragraphs short (2–5 sentences). Avoid lists inside paragraphs.\n"
        )

        response = model.generate_content(prompt)

        if response.candidates and response.candidates[0].content:
            ai_text = response.candidates[0].content.parts[0].text
        else:
            ai_text = "{}"

        # Try to extract JSON (strip code fences if present)
        text = ai_text.strip()
        # Remove common code-fence wrappers like ```json ... ```
        if text.startswith("```json") or text.startswith("```"):
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1 :]
            if text.endswith("```"):
                text = text[: -3].rstrip()

        report_json = None
        try:
            report_json = json.loads(text)
        except Exception:
            # Fallback minimal structure
            report_json = {
                "executiveSummary": [
                    "We could not fully parse the model output. This is a fallback summary.",
                    "Please regenerate the report or adjust inputs.",
                ],
                "sections": [{
                    "heading": selected_sections[0],
                    "content": ["Summary unavailable."],
                    "chart": {"type": "none", "callout": "no chart"}
                }]
            }

        # Log prompt for auditing (truncate content)
        try:
            mongodb.logPrompt("report_generator", prompt, json.dumps(report_json)[:5000])
        except Exception:
            pass

        return {
            "status": "success",
            "report": report_json,
            "included_sections": selected_sections,
            "clearance": request.clearance,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

if (__name__ == "__main__"):
    uvicorn.run("main:app", reload=True)