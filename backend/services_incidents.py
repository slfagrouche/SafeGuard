from db import db


async def get_next_incident_id():
    counter = await db.counters.find_one_and_update(
        {"_id": "incident_id"}, {"$inc": {"seq": 1}}, upsert=True, return_document=True
    )
    return counter["seq"]

