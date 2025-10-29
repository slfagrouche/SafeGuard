import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from db import db
from mailer import send_alert_email
from rate_limit import check_rate_limit, rate_limit_response
from realtime import ws_manager
from services_incidents import get_next_incident_id

router = APIRouter(prefix="/api")


@router.get("/incidents/")
async def get_incidents():
    incidents = (
        await db.incidents.find({"verification_status": {"$ne": "rejected"}}, {"_id": 0})
        .sort("datetime", -1)
        .to_list(500)
    )
    return JSONResponse(content=incidents)


@router.post("/incidents/{incident_id}/flag/")
async def flag_incident(incident_id: int, request: Request):
    if not check_rate_limit(request, "flag_incident", limit=10, window_seconds=3600):
        return rate_limit_response("Flag rate limit exceeded (10/hour).")
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(content={"error": "Invalid JSON"}, status_code=400)

    reason = data.get("reason", "")
    if reason not in ["inaccurate", "duplicate", "spam", "outdated"]:
        return JSONResponse(
            content={
                "error": "Invalid reason. Must be one of: inaccurate, duplicate, spam, outdated"
            },
            status_code=400,
        )

    incident = await db.incidents.find_one({"id": incident_id})
    if not incident:
        return JSONResponse(content={"error": "Incident not found"}, status_code=404)

    await db.flags.insert_one(
        {
            "incident_id": incident_id,
            "reason": reason,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    flag_count = await db.flags.count_documents({"incident_id": incident_id})
    new_status = incident.get("verification_status", "unverified")
    if flag_count >= 3 and new_status == "unverified":
        new_status = "flagged"
        await db.incidents.update_one(
            {"id": incident_id}, {"$set": {"verification_status": new_status}}
        )

    return {"success": True, "flag_count": flag_count, "verification_status": new_status}


@router.post("/report/")
async def report_incident(request: Request):
    if not check_rate_limit(request, "report_incident", limit=5, window_seconds=3600):
        return rate_limit_response("Report rate limit exceeded (5/hour).")
    try:
        data = await request.json()
        lat = data.get("lat", data.get("latitude"))
        lng = data.get("lng", data.get("longitude"))
        if lat is None or lng is None:
            return JSONResponse(
                content={"status": "error", "message": "Coordinates required"}, status_code=400
            )

        lat, lng = float(lat), float(lng)
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return JSONResponse(
                content={"status": "error", "message": "Invalid coordinates"}, status_code=400
            )

        severity = data.get("severity", "medium")
        if severity not in ["critical", "high", "medium", "low"]:
            severity = "medium"

        raw_dt = data.get("dateTime", data.get("datetime"))
        incident_dt = datetime.now(timezone.utc).isoformat()
        if raw_dt:
            try:
                incident_dt = datetime.fromisoformat(str(raw_dt).replace("Z", "+00:00")).isoformat()
            except (ValueError, TypeError):
                return JSONResponse(
                    content={"status": "error", "message": "Invalid datetime"}, status_code=400
                )

        incident_id = await get_next_incident_id()
        doc = {
            "id": incident_id,
            "datetime": incident_dt,
            "lat": lat,
            "lng": lng,
            "description": data.get("description", ""),
            "severity": severity,
            "source": data.get("source", ""),
            "image": data.get("image", ""),
            "image_file_id": data.get("image_file_id", ""),
            "verification_status": "unverified",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.incidents.insert_one(doc)
        broadcast_doc = {k: v for k, v in doc.items() if k != "_id"}
        await ws_manager.broadcast({"type": "new_incident", "incident": broadcast_doc})
        return JSONResponse(content={"status": "success", "id": incident_id}, status_code=201)
    except Exception:
        return JSONResponse(
            content={"status": "error", "message": "Could not process incident report"},
            status_code=400,
        )


@router.post("/subscribe/")
async def subscribe(request: Request):
    if not check_rate_limit(request, "subscribe", limit=5, window_seconds=3600):
        return rate_limit_response("Subscription rate limit exceeded (5/hour).")
    try:
        data = await request.json()
        name, email = data.get("name"), data.get("email")
        if not name or not email:
            return JSONResponse(
                content={"status": "error", "message": "'name' and 'email' are required"},
                status_code=400,
            )

        existing = await db.subscribers.find_one({"email": email})
        if existing:
            return JSONResponse(
                content={"status": "error", "message": "Email already subscribed"},
                status_code=400,
            )

        radius_km = float(data.get("radius_km", 10.0))
        if not (0.5 <= radius_km <= 500):
            return JSONResponse(
                content={"status": "error", "message": "radius_km must be between 0.5 and 500"},
                status_code=400,
            )

        doc = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "address": data.get("address", ""),
            "latitude": float(data["latitude"]) if data.get("latitude") is not None else None,
            "longitude": float(data["longitude"]) if data.get("longitude") is not None else None,
            "radius_km": radius_km,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        }
        await db.subscribers.insert_one(doc)
        address_label = data.get("address", "").strip() or "Not provided"
        email_sent, email_status = send_alert_email(
            to_email=email,
            to_name=name,
            subject="SafeGuard Alert Subscription Confirmed",
            body=(
                f"Hello {name},\n\n"
                "Your SafeGuard alert subscription has been confirmed.\n\n"
                f"Address: {address_label}\n"
                f"Radius: {radius_km} km\n\n"
                "You will receive alerts for incidents within your configured area.\n\n"
                "Stay safe,\n"
                "SafeGuard Team"
            ),
        )
        response_payload = {
            "status": "success",
            "email_sent": email_sent,
        }
        if not email_sent:
            response_payload["email_warning"] = email_status
        return JSONResponse(content=response_payload, status_code=201)
    except Exception:
        return JSONResponse(
            content={"status": "error", "message": "Could not create subscription"},
            status_code=400,
        )


@router.get("/subscribers/")
async def get_subscribers(email: str | None = None):
    query = {"active": True}
    if email:
        query["email"] = email
    subs = await db.subscribers.find(query, {"_id": 0}).to_list(100)
    return JSONResponse(content=subs)


@router.delete("/subscribers/{sid}/")
async def deactivate_subscriber(sid: str):
    result = await db.subscribers.update_one({"id": sid}, {"$set": {"active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"success": True}

