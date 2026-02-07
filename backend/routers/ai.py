import uuid
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rate_limit import check_rate_limit, rate_limit_response
from services_ai import process_ai_chat
from state import ai_tasks

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    agent_type: Literal["general", "medical", "recommendation", "situational", "map_intelligence"]
    message: str


@router.post("/ai/chat/")
async def start_ai_chat(request: Request, body: ChatRequest, background_tasks: BackgroundTasks):
    if not check_rate_limit(request, "ai_chat", limit=5, window_seconds=3600):
        return rate_limit_response("AI chat rate limit exceeded (5/hour).")
    if not body.message.strip():
        return JSONResponse(
            content={"status": "error", "message": "Message cannot be empty"}, status_code=400
        )

    task_id = str(uuid.uuid4())
    ai_tasks[task_id] = {
        "status": "processing",
        "content": None,
        "usage": None,
        "agent_type": body.agent_type,
        "tool_calls": [],
        "message": "AI is thinking...",
    }
    background_tasks.add_task(process_ai_chat, task_id, body.agent_type, body.message)
    return JSONResponse(content={"status": "processing", "task_id": task_id}, status_code=202)


@router.get("/ai/status/{task_id}/")
async def get_ai_status(task_id: str):
    if task_id not in ai_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    task = ai_tasks[task_id]
    if task["status"] == "processing":
        return JSONResponse(content={"status": "processing", "message": "AI is thinking..."}, status_code=202)
    if task["status"] == "success":
        return JSONResponse(
            content={
                "status": "success",
                "content": task["content"],
                "usage": task["usage"],
                "agent_type": task["agent_type"],
                "tool_calls": task.get("tool_calls", []),
            }
        )
    return JSONResponse(
        content={
            "status": "error",
            "error": task.get("error", "unknown"),
            "message": task.get("message", "Failed"),
        }
    )

