import json
import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Request

from auth import require_admin
from config import ALLOW_DESTRUCTIVE_SEED, ALLOW_PUBLIC_SEED
from db import db
from rate_limit import check_rate_limit, rate_limit_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def seed_requires_admin(allow_public_seed: bool) -> bool:
    return not allow_public_seed


def seed_allows_destructive_reset(flag: bool) -> bool:
    return bool(flag)


def parse_django_point(point_str):
    match = re.match(r"POINT\(([-\d.]+)\s+([-\d.]+)\)", point_str)
    if match:
        lng, lat = float(match.group(1)), float(match.group(2))
        return lat, lng
    return None, None


@router.post("/seed/")
async def seed_data(request: Request):
    if not check_rate_limit(request, "seed_data", limit=3, window_seconds=3600):
        return rate_limit_response("Seed rate limit exceeded (3/hour).")
    if seed_requires_admin(ALLOW_PUBLIC_SEED):
        await require_admin(request)
    if not seed_allows_destructive_reset(ALLOW_DESTRUCTIVE_SEED):
        return {
            "success": False,
            "error": "Destructive seed reset disabled. Set ALLOW_DESTRUCTIVE_SEED=true in controlled environments.",
        }

    await db.counters.update_one({"_id": "incident_id"}, {"$set": {"seq": 0}}, upsert=True)
    incidents = []
    for i, inc in enumerate(
        [
            # Sudan/Khartoum
            {"dt": "2026-04-14T10:30:00+00:00", "lat": 15.5007, "lng": 32.5599, "desc": "Road blockage on main highway near Khartoum", "sev": "high", "vs": "verified", "src": "local_report"},
            {"dt": "2026-04-14T09:15:00+00:00", "lat": 15.6280, "lng": 32.5400, "desc": "Critical medical emergency - multiple casualties in Khartoum North", "sev": "critical", "vs": "verified", "src": "emergency_services"},
            {"dt": "2026-04-13T08:00:00+00:00", "lat": 15.4800, "lng": 32.5800, "desc": "Water distribution point at community center", "sev": "low", "vs": "verified", "src": "aid_org"},
            # Europe
            {"dt": "2026-04-14T14:00:00+00:00", "lat": 48.8566, "lng": 2.3522, "desc": "Major flooding in Paris Seine River basin - evacuation underway", "sev": "critical", "vs": "verified", "src": "government"},
            {"dt": "2026-04-14T12:00:00+00:00", "lat": 51.5074, "lng": -0.1278, "desc": "Chemical spill in Thames River - water contamination alert", "sev": "high", "vs": "verified", "src": "environment_agency"},
            {"dt": "2026-04-13T16:00:00+00:00", "lat": 40.4168, "lng": -3.7038, "desc": "Heat dome over Madrid - record temperatures 47C", "sev": "high", "vs": "verified", "src": "weather_service"},
            {"dt": "2026-04-13T10:00:00+00:00", "lat": 52.5200, "lng": 13.4050, "desc": "Cyber attack on Berlin infrastructure - hospitals affected", "sev": "high", "vs": "unverified", "src": "government"},
            {"dt": "2026-04-12T20:00:00+00:00", "lat": 41.0082, "lng": 28.9784, "desc": "Refugee camp overcrowding in Istanbul - medical aid needed", "sev": "medium", "vs": "verified", "src": "unhcr"},
            # Americas
            {"dt": "2026-04-14T08:00:00+00:00", "lat": 34.0522, "lng": -118.2437, "desc": "Wildfire spreading in Los Angeles hills - air quality hazardous", "sev": "critical", "vs": "verified", "src": "emergency_services"},
            {"dt": "2026-04-14T06:00:00+00:00", "lat": -23.5505, "lng": -46.6333, "desc": "Severe flooding in Sao Paulo favelas - rescue operations active", "sev": "critical", "vs": "verified", "src": "emergency_services"},
            {"dt": "2026-04-13T22:00:00+00:00", "lat": 19.4326, "lng": -99.1332, "desc": "Earthquake aftershocks in Mexico City - building inspections", "sev": "medium", "vs": "verified", "src": "seismology"},
            {"dt": "2026-04-13T14:00:00+00:00", "lat": -15.7975, "lng": -47.8919, "desc": "Dam breach warning near Brasilia - downstream evacuation", "sev": "critical", "vs": "verified", "src": "government"},
            {"dt": "2026-04-12T18:00:00+00:00", "lat": 4.7110, "lng": -74.0721, "desc": "Landslide in Bogota mountains after heavy rain", "sev": "high", "vs": "verified", "src": "emergency_services"},
            # Asia
            {"dt": "2026-04-14T04:00:00+00:00", "lat": 35.6762, "lng": 139.6503, "desc": "Earthquake magnitude 5.2 near Tokyo - structural damage reported", "sev": "high", "vs": "verified", "src": "seismology"},
            {"dt": "2026-04-14T03:00:00+00:00", "lat": 28.6139, "lng": 77.2090, "desc": "Extreme heat wave in Delhi - hospitals overwhelmed", "sev": "high", "vs": "verified", "src": "health_ministry"},
            {"dt": "2026-04-13T20:00:00+00:00", "lat": 37.5665, "lng": 126.9780, "desc": "Typhoon approaching Seoul - evacuation orders issued", "sev": "critical", "vs": "verified", "src": "weather_service"},
            {"dt": "2026-04-13T18:00:00+00:00", "lat": 14.5995, "lng": 120.9842, "desc": "Typhoon damage in Manila - widespread flooding", "sev": "critical", "vs": "verified", "src": "government"},
            {"dt": "2026-04-13T12:00:00+00:00", "lat": 13.7563, "lng": 100.5018, "desc": "Monsoon flooding in Bangkok - transit system halted", "sev": "high", "vs": "verified", "src": "government"},
            {"dt": "2026-04-12T16:00:00+00:00", "lat": 23.8103, "lng": 90.4125, "desc": "Cyclone damage in Dhaka - emergency shelters activated", "sev": "critical", "vs": "verified", "src": "emergency_services"},
            {"dt": "2026-04-12T10:00:00+00:00", "lat": 12.9716, "lng": 77.5946, "desc": "Industrial fire in Bangalore tech district", "sev": "high", "vs": "unverified", "src": "local_report"},
            {"dt": "2026-04-11T22:00:00+00:00", "lat": -6.2088, "lng": 106.8456, "desc": "Volcanic ash from Mount Merapi affecting Jakarta air", "sev": "medium", "vs": "verified", "src": "volcanology"},
            # Middle East / North Africa
            {"dt": "2026-04-14T11:00:00+00:00", "lat": 33.8938, "lng": 35.5018, "desc": "Infrastructure damage in Beirut - power grid failure", "sev": "high", "vs": "verified", "src": "local_report"},
            {"dt": "2026-04-13T09:00:00+00:00", "lat": 30.0444, "lng": 31.2357, "desc": "Sandstorm warning in Cairo - visibility near zero", "sev": "medium", "vs": "verified", "src": "weather_service"},
            {"dt": "2026-04-12T14:00:00+00:00", "lat": 31.9454, "lng": 35.9284, "desc": "Humanitarian corridor needed in Amman region", "sev": "medium", "vs": "verified", "src": "aid_org"},
            {"dt": "2026-04-12T08:00:00+00:00", "lat": 25.2048, "lng": 55.2708, "desc": "Dust storm advisory in Dubai - flights diverted", "sev": "medium", "vs": "verified", "src": "aviation"},
            {"dt": "2026-04-11T12:00:00+00:00", "lat": 36.7213, "lng": 3.0197, "desc": "Water shortage crisis in Algiers - rationing in effect", "sev": "high", "vs": "verified", "src": "local_report"},
            # Africa
            {"dt": "2026-04-14T07:00:00+00:00", "lat": 6.5244, "lng": 3.3792, "desc": "Flooding in Lagos coastal areas - thousands displaced", "sev": "critical", "vs": "verified", "src": "government"},
            {"dt": "2026-04-13T06:00:00+00:00", "lat": -4.4419, "lng": 15.2663, "desc": "Cholera outbreak in Kinshasa - WHO response team deployed", "sev": "critical", "vs": "verified", "src": "who"},
            {"dt": "2026-04-12T22:00:00+00:00", "lat": 9.0579, "lng": 7.4951, "desc": "Armed conflict displacement in Abuja region", "sev": "critical", "vs": "verified", "src": "unhcr"},
            {"dt": "2026-04-12T12:00:00+00:00", "lat": -1.2921, "lng": 36.8219, "desc": "Food distribution point active in Nairobi - aid arriving", "sev": "low", "vs": "verified", "src": "aid_org"},
            {"dt": "2026-04-11T18:00:00+00:00", "lat": -26.2041, "lng": 28.0473, "desc": "Power grid collapse in Johannesburg - loadshedding stage 6", "sev": "medium", "vs": "verified", "src": "utility"},
            # Oceania
            {"dt": "2026-04-13T04:00:00+00:00", "lat": -33.8688, "lng": 151.2093, "desc": "Bushfire smoke blanketing Sydney - respiratory warnings", "sev": "medium", "vs": "verified", "src": "health_authority"},
            # Russia
            {"dt": "2026-04-12T06:00:00+00:00", "lat": 55.7558, "lng": 37.6173, "desc": "Industrial accident in Moscow - hazmat response deployed", "sev": "high", "vs": "unverified", "src": "emergency_services"},
        ],
        start=1,
    ):
        incidents.append(
            {
                "id": i,
                "datetime": inc["dt"],
                "lat": inc["lat"],
                "lng": inc["lng"],
                "description": inc["desc"],
                "severity": inc["sev"],
                "verification_status": inc["vs"],
                "source": inc["src"],
                "image": "",
                "image_file_id": "",
            }
        )

    resources = []
    fixture_path = Path(__file__).parent.parent / "resources_fixture.json"
    if fixture_path.exists():
        try:
            fixture_data = json.loads(fixture_path.read_text(encoding="utf-8"))
            for item in fixture_data:
                fields = item.get("fields", {})
                lat, lng = parse_django_point(fields.get("location", ""))
                if lat is None:
                    continue
                rtype = fields.get("resource_type", "aid_org")
                type_map = {
                    "hospital": "hospital",
                    "shelter": "shelter",
                    "aid_org": "aid",
                    "pharmacy": "pharmacy",
                    "water_point": "water",
                }
                resources.append(
                    {
                        "id": str(item.get("pk", uuid.uuid4())),
                        "type": type_map.get(rtype, "aid"),
                        "name": fields.get("name", ""),
                        "lat": lat,
                        "lng": lng,
                        "hours": fields.get("hours", ""),
                        "contact": fields.get("contact", ""),
                        "services": [s.strip() for s in fields.get("services", "").split(",") if s.strip()],
                        "verified": fields.get("verified", False),
                    }
                )
            logger.info("Loaded %s resources from Django fixture", len(resources))
        except Exception as e:
            logger.error("Failed to load fixture: %s", e)

    if not resources:
        resources = [
            {"id": str(uuid.uuid4()), "type": "hospital", "name": "Khartoum Teaching Hospital", "lat": 15.6, "lng": 32.54, "hours": "24/7", "contact": "+249-123-456789", "services": ["Emergency", "Surgery"], "verified": True},
            {"id": str(uuid.uuid4()), "type": "shelter", "name": "Red Crescent Shelter", "lat": 15.52, "lng": 32.56, "hours": "24/7", "contact": "+249-123-456790", "services": ["Accommodation", "Food"], "verified": True},
        ]

    await db.incidents.delete_many({})
    await db.resources.delete_many({})
    await db.flags.delete_many({})
    await db.counters.update_one(
        {"_id": "incident_id"}, {"$set": {"seq": len(incidents)}}, upsert=True
    )
    if incidents:
        await db.incidents.insert_many(incidents)
    if resources:
        await db.resources.insert_many(resources)
    return {"success": True, "seeded": {"incidents": len(incidents), "resources": len(resources)}}

