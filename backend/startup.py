import logging
import os
from datetime import datetime, timezone

from fastapi import FastAPI

from auth import hash_password, verify_password
from config import ALLOW_DEFAULT_ADMIN_PASSWORD
from db import client, db, ensure_indexes
from storage import init_storage

logger = logging.getLogger(__name__)


def resolve_admin_password(admin_password: str | None, allow_default: bool) -> str | None:
    if admin_password:
        return admin_password
    return None


async def on_startup() -> None:
    await ensure_indexes()
    try:
        init_storage()
    except Exception as e:
        logger.error("Storage init failed: %s", e)

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@safeguard.org")
    admin_password = resolve_admin_password(
        os.environ.get("ADMIN_PASSWORD"), ALLOW_DEFAULT_ADMIN_PASSWORD
    )
    if not os.environ.get("ADMIN_PASSWORD"):
        logger.warning("ADMIN_PASSWORD not set; admin user will not be seeded")

    existing = await db.users.find_one({"email": admin_email})
    if not existing and admin_password:
        await db.users.insert_one(
            {
                "email": admin_email,
                "password_hash": hash_password(admin_password),
                "name": "Admin",
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info("Admin seeded: %s", admin_email)
    elif not existing:
        logger.warning("Admin user not seeded because ADMIN_PASSWORD is missing in non-development mode")
    elif admin_password and not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}},
        )
        logger.info("Admin password updated")


async def on_shutdown() -> None:
    client.close()


def register_lifecycle(app: FastAPI) -> None:
    app.on_event("startup")(on_startup)
    app.on_event("shutdown")(on_shutdown)
