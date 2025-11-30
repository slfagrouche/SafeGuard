import logging
import os

import requests as http_requests

STORAGE_URL = os.environ.get("STORAGE_API_URL", "").strip()
APP_NAME = "safeguard"
storage_key = None

logger = logging.getLogger(__name__)


def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    api_key = os.environ.get("STORAGE_API_KEY")
    if not api_key:
        logger.warning("STORAGE_API_KEY not set, storage disabled")
        return None
    if not STORAGE_URL:
        logger.warning("STORAGE_API_URL not set, storage disabled")
        return None
    try:
        resp = http_requests.post(
            f"{STORAGE_URL}/init", json={"api_key": api_key}, timeout=30
        )
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        logger.info("Object storage initialized")
        return storage_key
    except Exception as e:
        logger.error("Storage init failed: %s", e)
        return None


def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    if not key:
        raise Exception("Storage not initialized")
    resp = http_requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def get_object(path: str):
    key = init_storage()
    if not key:
        raise Exception("Storage not initialized")
    resp = http_requests.get(
        f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

