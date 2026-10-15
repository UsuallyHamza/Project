from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from typing_extensions import Annotated

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, StringConstraints

app = FastAPI(
    title="Messages API",
    description="A simple API to create and manage chat messages.",
    version="0.1.0"
)

# In-memory storage and ID counter
messages_db: Dict[int, dict] = {}
current_id = 1

# Data Models
class Role(str, Enum):
    user = "user"
    assistant = "assistant"

# Enforce 1-2000 chars after trimming whitespace
ContentString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]

class MessageCreate(BaseModel):
    role: Role
    content: ContentString

class MessageUpdate(BaseModel):
    content: ContentString

class MessageResponse(BaseModel):
    id: int
    role: Role
    content: str
    created_at: datetime

# Helper function for 404s
def get_message_or_404(message_id: int):
    if message_id not in messages_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Message not found", "id": message_id}
        )
    return messages_db[message_id]

# API Endpoints
@app.post("/api/v1/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED, tags=["Messages"])
def create_message(message: MessageCreate):
    global current_id
    new_msg = {
        "id": current_id,
        "role": message.role,
        "content": message.content,
        "created_at": datetime.now(timezone.utc)
    }
    messages_db[current_id] = new_msg
    current_id += 1
    return new_msg

@app.get("/api/v1/messages", response_model=List[MessageResponse], tags=["Messages"])
def list_messages(
    limit: int = Query(20, ge=1, le=100, description="Maximum messages returned"),
    offset: int = Query(0, ge=0, description="Number of messages skipped"),
    role: Optional[Role] = Query(None, description="Filter by user or assistant")
):
    results = list(messages_db.values())
    if role:
        results = [msg for msg in results if msg["role"] == role]
    
    return results[offset : offset + limit]

@app.get("/api/v1/messages/{message_id}", response_model=MessageResponse, tags=["Messages"])
def get_message(message_id: int):
    return get_message_or_404(message_id)

@app.patch("/api/v1/messages/{message_id}", response_model=MessageResponse, tags=["Messages"])
def update_message(message_id: int, message_update: MessageUpdate):
    msg = get_message_or_404(message_id)
    msg["content"] = message_update.content
    messages_db[message_id] = msg
    return msg

@app.delete("/api/v1/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Messages"])
def delete_message(message_id: int):
    get_message_or_404(message_id)
    del messages_db[message_id]