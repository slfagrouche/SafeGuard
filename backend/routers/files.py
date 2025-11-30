import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from db import db
from rate_limit import check_rate_limit, rate_limit_response
from storage import APP_NAME, get_object, put_object

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    if not check_rate_limit(request, "upload_file", limit=20, window_seconds=3600):
        return rate_limit_response("Upload rate limit exceeded (20/hour).")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        return JSONResponse(
            content={"error": "Invalid file type. Allowed: jpg, png, webp, gif"},
            status_code=400,
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        return JSONResponse(content={"error": "File too large. Max 10MB"}, status_code=400)

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_id = str(uuid.uuid4())
    path = f"{APP_NAME}/uploads/{file_id}.{ext}"

    try:
        result = put_object(path, data, file.content_type or "image/jpeg")
        doc = {
            "id": file_id,
            "storage_path": result["path"],
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": result.get("size", len(data)),
            "is_deleted": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.files.insert_one(doc)
        return {"id": file_id, "path": result["path"], "url": f"/api/files/{file_id}"}
    except Exception as e:
        logger.error("Upload error: %s", e)
        return JSONResponse(content={"error": "Upload failed. Please try again."}, status_code=500)


@router.get("/files/{file_id}")
async def serve_file(file_id: str):
    record = await db.files.find_one({"id": file_id, "is_deleted": False})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        data, content_type = get_object(record["storage_path"])
        return Response(content=data, media_type=record.get("content_type", content_type))
    except Exception as e:
        logger.error("File serve error: %s", e)
        raise HTTPException(status_code=500, detail="Could not retrieve file")

