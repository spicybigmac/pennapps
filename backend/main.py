from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import uvicorn
import dotenv
import os
import google.generativeai as genai
from exa_py import Exa

dotenv.load_dotenv()

# Moved mongodb import to be relative if it's in the same api_routes folder
# If mongodb is in the project root, just `import mongodb`
from api_routes import mongodb

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

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

    print(ai_response)
    
    # Log the conversation
    mongodb.logPrompt(request.user_id, request.prompt, ai_response)
    
    return {
        "response": ai_response,
        "user_id": request.user_id,
        "status": "success"
    }
    
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
        
        results = exa.search_and_contents(**search_params)
        
        formatted_results = []
        for result in results.results:
            formatted_results.append({
                "title": result.title,
                "url": result.url,
                "text": result.text,
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

   
# Enhanced Chat (moved from ai_routes.py)
@app.post("/api/ai/gemini/enhanced-chat")
async def enhanced_chat(request: EnhancedChatRequest):
    """
    Enhanced chat that can optionally use web search to provide more informed responses
    """

    try:
        context = ""
        
        # If web search is requested, search for relevant information
        if request.use_web_search and request.search_query:
            search_results = exa.search(
                query=request.search_query,
                num_results=3,
                type="neural",
                use_autoprompt=True,
                include_text=True
            )
            
            # Compile search results into context
            context_parts = []
            for result in search_results.results:
                if result.text:
                    context_parts.append(f"Source: {result.title}\n{result.text[:300]}...")
            
            context = "\n\n".join(context_parts)
        
        # Create enhanced prompt with context
        if context:
            enhanced_prompt = f"""Based on the following web search context, please answer the user's question:

Context from web search:
{context}

User's question: {request.prompt}

Please provide a comprehensive answer using the context above along with your knowledge."""
        else:
            enhanced_prompt = request.prompt
        
        # Generate response with Gemini
        response = model.generate_content(enhanced_prompt)
        
        if response.candidates and response.candidates[0].content:
            ai_response = response.candidates[0].content.parts[0].text
        else:
            ai_response = "I couldn't generate a response. Please try again."
        
        # Log the conversation
        mongodb.logPrompt(request.user_id, request.prompt, ai_response)
        
        return {
            "response": ai_response,
            "user_id": request.user_id,
            "used_web_search": request.use_web_search,
            "search_query": request.search_query if request.use_web_search else None,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in enhanced chat: {str(e)}")


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


# Reports: Generate via Gemini
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

        # Construct a detailed multi-paragraph system-style instruction and task prompt
        prompt = f"""
You are an intelligence analyst assisting a maritime monitoring team working on IUU (Illegal, Unreported, and Unregulated) fishing detection and response. Generate a polished, decision-ready report for the PennApps operational console covering {", ".join(selected_sections)}. The report should synthesize recent signals from AIS behavior, satellite SAR/optical cues, patrol observations, and environmental context over {time_window_str}. Do not fabricate precise metrics; when quantitative detail is not available, use careful qualitative language (e.g., "elevated activity", "moderate likelihood", "notable clustering").

Tailor the content to the audience clearance level "{request.clearance}". {clearance_instructions} Provide a brief executive preface followed by clearly labeled sections. Only include the sections explicitly requested below and omit all others.

Requested sections (include exactly these, with matching titles):
- Weekly IUU Activity Analysis -> summarize patterns, hotspots, likely drivers; call out confidence and caveats.
- AI Voice Agent Performance -> describe outreach efficacy, common call outcomes, and operator load implications.
- Vessel Track Details -> describe representative tracks, behavioral anomalies (e.g., loitering, rendezvous), and risk rationales without revealing sensitive coordinates.
- Economic Impact Analysis -> discuss likely economic implications (market pressure, local community impact, enforcement costs savings/risks) using directional, not precise, estimates.

Match the existing report presentation style used in the UI: clear headings, short paragraphs (2–5 sentences), readable spacing, and succinct bullets that can accompany charts. Include explicit "chart callouts" as sentences (not images) that an engineer could later pair with bar, radial, or pie charts (e.g., "callout: success_rate trending upward; drivers: fewer escalations").

OUTPUT FORMAT REQUIREMENTS (strict):
- Return VALID HTML only (no markdown, no JSON).
- Start with <section><h2>Executive Summary</h2> containing AT LEAST TWO substantial paragraphs for leadership.
- Then include ONLY the requested sections. For each included section:
  - Wrap content in <section> and an <h2> heading that EXACTLY matches the section title above.
  - Provide 1–2 concise paragraphs.
  - Provide a <ul> with 3–5 bullets (operational insights; include 1 bullet labeled "chart callout:" if appropriate).
- Do NOT include tables, code blocks, or inline CSS. Keep to semantic HTML only.
"""

        response = model.generate_content(prompt)

        if response.candidates and response.candidates[0].content:
            ai_html = response.candidates[0].content.parts[0].text
        else:
            ai_html = "<section><h2>Executive Summary</h2><p>We could not generate the report at this time.</p></section>"

        # Log prompt for auditing
        try:
            mongodb.logPrompt("report_generator", prompt, ai_html[:5000])
        except Exception:
            pass

        return {
            "status": "success",
            "html": ai_html,
            "included_sections": selected_sections,
            "clearance": request.clearance,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

if (__name__ == "__main__"):
    uvicorn.run("main:app", reload=True)