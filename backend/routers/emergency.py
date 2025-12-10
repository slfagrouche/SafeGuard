from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from knowledge import EMERGENCY_NUMBERS

router = APIRouter(prefix="/api")


@router.get("/emergency/regions/")
async def get_emergency_regions():
    regions = []
    for key, data in EMERGENCY_NUMBERS.items():
        services = [k for k in data.keys() if k != "display_name"]
        regions.append({"id": key, "name": data.get("display_name", key.title()), "services": services})
    return {"regions": regions, "calling_enabled": False}


@router.post("/emergency/call/")
async def emergency_call(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(content={"error": "Invalid JSON"}, status_code=400)
    region = data.get("region", "").lower().strip()
    service = data.get("service", "ambulance")
    if not region:
        return JSONResponse(content={"error": "Region is required"}, status_code=400)
    region_data = EMERGENCY_NUMBERS.get(region)
    if not region_data:
        return JSONResponse(content={"error": "Unknown region"}, status_code=404)
    number = region_data.get(service, "")
    if not number:
        return JSONResponse(content={"error": f"No {service} number for {region}"}, status_code=404)
    return JSONResponse(
        content={
            "success": False,
            "error": "Emergency calling not configured. Please call directly.",
            "number": number,
            "region": region_data.get("display_name"),
            "service": service,
        },
        status_code=503,
    )

