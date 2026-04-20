"""
api_server.py
=============
FastAPI server for Financial AI Assistant
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from chatbot_groq_langgraph import process_user_prompt
import os

app = FastAPI(title="Financial AI Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[list] = None
    conversation_id: Optional[str] = "default"


class PromptRequest(BaseModel):
    prompt: str
    currentJson: Optional[dict] = None


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "financial-ai-assistant"}


@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        if not req.message or not req.message.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "response": "Please ask me a financial question. I'm here to help!",
                    "error": "Empty message"
                }
            )

        result = process_user_prompt(
            prompt=req.message,
            conversation_history=req.conversation_history,
            conversation_id=req.conversation_id or "default"
        )

        return {
            "success": True,
            "response": result.get("response", "How can I help with your financial needs?"),
            "issues": result.get("issues", []),
            "topics": result.get("topics", []),
            "conversation_id": result.get("conversation_id", "default")
        }

    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "response": f"An error occurred: {str(exc)}. Please try rephrasing.",
                "error": str(exc)
            }
        )


@app.post("/api/generate-text")
def generate_text(req: PromptRequest):
    try:
        if not req.prompt or not req.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt is required")

        result = process_user_prompt(prompt=req.prompt)

        return {
            "success": True,
            "response": result.get("response", "How can I assist you further?"),
            "issues": result.get("issues", []),
            "topics": result.get("topics", [])
        }

    except HTTPException:
        raise
    except Exception as exc:
        return {
            "success": False,
            "response": f"Error: {str(exc)}",
            "error": str(exc)
        }


@app.post("/api/generate-optics")
def generate_optics(req: PromptRequest):
    try:
        if not req.prompt or not req.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt is required")

        result = process_user_prompt(prompt=req.prompt)

        return {
            "success": True,
            "response": result.get("response", "Here's my response to your query."),
            "issues": result.get("issues", [])
        }

    except HTTPException:
        raise
    except Exception as exc:
        return {
            "success": False,
            "response": f"Error occurred: {str(exc)}",
            "error": str(exc)
        }


@app.get("/")
def root():
    return PlainTextResponse("""
💰 Financial AI Assistant API
==============================
Powered by Groq (Llama 3.3 70B) + LangGraph

ENDPOINTS:
----------
POST /api/chat          - Chat with the financial assistant
POST /api/generate-text - Generate text responses
GET  /api/health        - Check service health

EXAMPLE REQUEST:
---------------
curl -X POST http://localhost:5000/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "How do I start saving money?"}'

EXAMPLE RESPONSE:
----------------
{
  "success": true,
  "response": "Great question! Here is how to start saving...",
  "topics": ["saving"],
  "conversation_id": "default"
}
    """)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 5000))
    print(f"\n{'='*60}")
    print(f"💰 Financial AI Assistant API  |  Groq + LangGraph")
    print(f"{'='*60}")
    print(f"📍 http://localhost:{port}")
    print(f"🔗 Health : http://localhost:{port}/api/health")
    print(f"💬 Chat   : http://localhost:{port}/api/chat (POST)")
    print(f"{'='*60}\n")

    uvicorn.run(app, host="0.0.0.0", port=port)