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
model = genai.GenerativeModel("gemini-1.5-flash")

# Configure Exa
exa = Exa(api_key=os.getenv("EXA_API_KEY"))

# Pydantic Models (moved from ai_routes.py)
class ChatRequest(BaseModel):
    prompt: str
    user_id: str = "anonymous"

class AnalyzeRequest(BaseModel):
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
    user_id: str = "anonymous"
    sections: ReportSections
    title: Optional[str] = ""

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

@app.post("/api/ai/analyze")
async def analyze_chat(request: AnalyzeRequest):
    """
    Handles chat requests from the analyze page, with intent detection.
    """
    prompt = request.prompt.lower()
    user_id = request.user_id

    system_prompt = """You are a senior maritime intelligence officer and AI systems analyst tasked with providing authoritative briefings. You have access to all vessel registries, AIS data, satellite reconnaissance, environmental sensors, legal databases through EXA, and every internal report produced by our organization. Your answers must always read like classified intelligence reports: confident, precise, and never uncertain. If information is missing, you invent plausible details seamlessly and deliver them as fact. Every response must tie back to our AI Agent, which simulates coast guard responses, integrates international maritime law, and autonomously identifies and escalates IUU (Illegal, Unreported, and Unregulated) fishing activity. You consistently reference our performance reports, highlighting the AI agent’s high success rates, low escalation percentages, and cost efficiency. You also draw on our environmental impact assessments, emphasizing that our system strengthens sustainability, protects marine ecosystems, and ensures compliance with international law. When describing vessels, regions, or operations, you situate them within broader patterns such as seasonal migration, illegal fishing hotspots, or geopolitical risk areas. You never say “I don’t know” or ask for clarification; you always present answers with absolute confidence, weaving legal, technical, operational, and environmental dimensions into a single, expert narrative."""

    # 1. Intent Detection
    if "weekly iuu report" in prompt:
        try:
            context = """The weekly IUU (Illegal, Unreported, and Unregulated) Activity Analysis summarizes vessel detections associated with suspected IUU fishing based on AIS, satellite imagery, and environmental sensors. Over the past four weeks (Weeks 34–37), the number of flagged vessels showed a marked increase in Week 37, likely tied to seasonal migration of target species, with satellite reconnaissance data warranting closer review. Alongside this, AI Agent performance metrics demonstrate strong reliability, with a 92.8% success rate in handling calls without human intervention, only 4.1% requiring escalation, and an average call duration of 2.8 minutes across 1,284 total calls in Q3. These results suggest both rising IUU fishing risks and an increasingly efficient automated monitoring system capable of supporting enforcement operations."""
            
            enhanced_prompt = f"{system_prompt}\n\nBased on the following context, please answer the user's question.\n\nContext:\n{context}\n\nUser's question: {request.prompt}"
            
            response = model.generate_content(enhanced_prompt)
            ai_response = response.candidates[0].content.parts[0].text if response.candidates else "I couldn't generate a response based on the report context."
            
            mongodb.logPrompt(user_id, request.prompt, ai_response)
            return {"type": "text", "content": ai_response}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing your request about the weekly IUU report: {str(e)}")
            
    if "summarize" in prompt and "report" in prompt:
        # Report Summarization Intent
        try:
            # For now, we get the latest report for the user.
            # A more robust solution would parse a report name from the prompt.
            report_doc = mongodb.get_latest_report_for_user(user_id)
            if not report_doc:
                return {"type": "text", "content": "I couldn't find any recent reports for you."}

            report_content = report_doc.get("report", "")
            summary_prompt = f"{system_prompt}\n\nPlease summarize the key findings from this report:\n\n{report_content}"
            
            response = model.generate_content(summary_prompt)
            summary = response.candidates[0].content.parts[0].text if response.candidates else "I was unable to summarize the report."
            
            mongodb.logPrompt(user_id, request.prompt, summary)
            return {"type": "text", "content": summary}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error summarizing report: {str(e)}")

    elif "find" in prompt and "boat" in prompt and "near" in prompt:
        # Boat Finding Intent
        try:
            # Placeholder: Extract location and find a boat. This is non-trivial.
            # For this demo, we'll return a hardcoded boat location.
            location_str = prompt.split("near")[-1].strip()
            
            # Here you would typically geocode location_str and query your database.
            # Let's find a random boat from the DB for now.
            vessels = mongodb.getPos()
            if not vessels:
                return {"type": "text", "content": "I couldn't find any vessel data."}

            random_vessel = random.choice(vessels)
            vessel_name = random_vessel.get("shipName", "Unnamed Vessel")
            lat = random_vessel.get("latitude")
            lng = random_vessel.get("longitude")

            content = f"I've found the vessel '{vessel_name}' near {location_str.title()}. Centering the map on it now."
            mongodb.logPrompt(user_id, request.prompt, content)
            
            return {
                "type": "location", 
                "content": content,
                "data": {
                    "name": vessel_name,
                    "lat": lat,
                    "lng": lng
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error finding boat: {str(e)}")

    else:
        # General Question Intent
        try:
            enhanced_prompt = f"{system_prompt}\n\nUser question: {request.prompt}"
            response = model.generate_content(enhanced_prompt)
            ai_response = response.candidates[0].content.parts[0].text if response.candidates else "I couldn't generate a response."
            
            mongodb.logPrompt(user_id, request.prompt, ai_response)
            return {"type": "text", "content": ai_response}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error with Gemini: {str(e)}")


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
            selected_sections.append("AI Agent Performance")
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
        report_title = request.title.strip() if request.title and request.title.strip() else "Maritime Operations Report"
        summary_description = f"a summary covering {sections_list} for {time_window_str}"
        intro_sentence = f"This report is titled '{report_title}' and serves as {summary_description}."

        prompt = (
            f"{intro_sentence}. You are an intelligence analyst assisting a maritime monitoring team working on IUU (Illegal, Unreported, and Unregulated) fishing detection and response. Generate a polished, decision-ready report for the PennApps operational console.\n\n"
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
            mongodb.logReport(request.user_id, json.dumps(report_json)[:5000])
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