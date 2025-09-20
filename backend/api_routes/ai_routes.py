from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from exa_py import Exa
import os
from . import mongodb

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# Configure Exa
exa = Exa(api_key=os.getenv("EXA_API_KEY"))

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

@router.post("/gemini/chat")
async def gemini_chat(request: ChatRequest):
    """
    Chat with Gemini AI model
    """
    try:
        response = model.generate_content(request.prompt)
        
        if response.candidates and response.candidates[0].content:
            ai_response = response.candidates[0].content.parts[0].text
        else:
            ai_response = "I couldn't generate a response. Please try again."
        
        # Log the conversation
        mongodb.logPrompt(request.user_id, request.prompt, ai_response)
        
        return {
            "response": ai_response,
            "user_id": request.user_id,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@router.post("/exa/search")
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
            "include_text": True
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
                "text": result.text[:500] + "..." if result.text and len(result.text) > 500 else result.text,
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
        raise HTTPException(status_code=500, detail=f"Error searching web: {str(e)}")

@router.post("/enhanced-chat")
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

@router.get("/health")
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
        except:
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
