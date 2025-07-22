# This code is used to run and test agent locally
from typing import List, Literal

import os

# NOTE: agents library provides Agent, Runner, ModelSettings, function_tool
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.hotel_agent import agent_response_stream


# Load TOKEN from environment
TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    raise RuntimeError('TOKEN environment variable not set')

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

def latest_user_question(messages: List[ChatMessage]) -> str:
    for msg in reversed(messages):
        if msg.role == "user" and msg.content.strip():
            return msg.content.strip()
    raise ValueError("No user question found")

app = FastAPI(title="Hotel Data Chat API", version="1.0")
# Bearer Auth setup
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

# ───────────────────────────────
# POST endpoint to stream agent
# ───────────────────────────────
@app.post("/api/v1/chat", response_class=StreamingResponse)
async def chat_endpoint(
    body: ChatRequest,
    _: HTTPAuthorizationCredentials = Depends(verify_token)
):
    if not body.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    last_message = body.messages[-1].content.strip()

    return StreamingResponse(
        agent_response_stream(last_message),
        media_type="text/event-stream"
    )