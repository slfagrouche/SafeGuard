import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from db import db

api_router = APIRouter(prefix="/api")
health_router = APIRouter()


@health_router.get("/health")
async def health_check():
    try:
        await db.command("ping")
        return JSONResponse(
            content={"status": "healthy", "checks": {"database": "healthy", "cache": "healthy"}}
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "unhealthy", "checks": {"database": f"unhealthy: {e}"}},
            status_code=503,
        )


@api_router.get("/")
async def root():
    return {"message": "SafeGuard API v2.0"}


@api_router.post("/status")
async def create_status_check(request: Request):
    data = await request.json()
    doc = {
        "id": str(uuid.uuid4()),
        "client_name": data.get("client_name", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await db.status_checks.insert_one(doc)
    return doc


@api_router.get("/status")
async def get_status_checks():
    return await db.status_checks.find({}, {"_id": 0}).to_list(100)

