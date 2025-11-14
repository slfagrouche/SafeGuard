from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from db import db
from knowledge import EMERGENCY_PROCEDURES_CONTENT, FIRST_AID_CONTENT

router = APIRouter(prefix="/api")


@router.get("/offline/packs/{pack_name}")
async def get_offline_pack(pack_name: str):
    if pack_name == "first_aid":
        content = FIRST_AID_CONTENT
    elif pack_name == "emergency_procedures":
        content = EMERGENCY_PROCEDURES_CONTENT
    elif pack_name == "resource_directory":
        resources = await db.resources.find({}, {"_id": 0}).to_list(200)
        content = "# Resource Directory\n\n"
        for r in resources:
            content += f"## {r.get('name', 'Unknown')}\n"
            content += f"- Type: {r.get('type', 'N/A')}\n"
            content += f"- Hours: {r.get('hours', 'N/A')}\n"
            content += f"- Contact: {r.get('contact', 'N/A')}\n"
            content += f"- Services: {', '.join(r.get('services', []))}\n"
            content += f"- Verified: {'Yes' if r.get('verified') else 'No'}\n\n"
    else:
        raise HTTPException(status_code=404, detail="Pack not found")

    if not content:
        raise HTTPException(status_code=404, detail="Pack content not available")
    return {"pack_name": pack_name, "content": content}


@router.get("/resources/")
async def get_resources(type: str | None = None, search: str | None = None):
    query = {}
    if type and type != "all":
        query["type"] = type
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    resources = await db.resources.find(query, {"_id": 0}).limit(50).to_list(50)
    return JSONResponse(content=resources)

