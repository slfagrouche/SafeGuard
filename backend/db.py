import os

from motor.motor_asyncio import AsyncIOMotorClient

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]


async def ensure_indexes() -> None:
    await db.users.create_index("email", unique=True)
    await db.incidents.create_index("id", unique=True)
    await db.incidents.create_index([("datetime", -1)])
    await db.incidents.create_index("verification_status")
    await db.subscribers.create_index("email", unique=True)
    await db.flags.create_index([("incident_id", 1), ("created_at", -1)])

