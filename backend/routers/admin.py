from fastapi import APIRouter, HTTPException, Request

from auth import require_admin
from db import db
from realtime import ws_manager

router = APIRouter(prefix="/api")


@router.get("/admin/stats")
async def admin_stats(request: Request):
    await require_admin(request)
    total = await db.incidents.count_documents({})
    unverified = await db.incidents.count_documents({"verification_status": "unverified"})
    verified = await db.incidents.count_documents({"verification_status": "verified"})
    flagged = await db.incidents.count_documents({"verification_status": "flagged"})
    rejected = await db.incidents.count_documents({"verification_status": "rejected"})
    critical = await db.incidents.count_documents({"severity": "critical"})
    subscribers = await db.subscribers.count_documents({"active": True})
    resources = await db.resources.count_documents({})
    return {
        "incidents": {
            "total": total,
            "unverified": unverified,
            "verified": verified,
            "flagged": flagged,
            "rejected": rejected,
            "critical": critical,
        },
        "subscribers": subscribers,
        "resources": resources,
    }


@router.get("/admin/incidents")
async def admin_get_incidents(
    request: Request, status: str | None = None, limit: int = 50, offset: int = 0
):
    await require_admin(request)
    query = {}
    if status:
        query["verification_status"] = status
    incidents = (
        await db.incidents.find(query, {"_id": 0})
        .sort("datetime", -1)
        .skip(offset)
        .limit(limit)
        .to_list(limit)
    )
    total = await db.incidents.count_documents(query)
    return {"incidents": incidents, "total": total}


@router.put("/admin/incidents/{incident_id}/verify")
async def admin_verify_incident(request: Request, incident_id: int):
    await require_admin(request)
    result = await db.incidents.update_one(
        {"id": incident_id}, {"$set": {"verification_status": "verified"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
    await ws_manager.broadcast({"type": "incident_updated", "incident": incident})
    return {"success": True, "verification_status": "verified"}


@router.put("/admin/incidents/{incident_id}/reject")
async def admin_reject_incident(request: Request, incident_id: int):
    await require_admin(request)
    result = await db.incidents.update_one(
        {"id": incident_id}, {"$set": {"verification_status": "rejected"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Incident not found")
    await ws_manager.broadcast({"type": "incident_removed", "incident_id": incident_id})
    return {"success": True, "verification_status": "rejected"}


@router.get("/admin/subscribers")
async def admin_get_subscribers(request: Request):
    await require_admin(request)
    return await db.subscribers.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)

