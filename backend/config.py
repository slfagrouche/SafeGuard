import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").strip().lower()
IS_DEV_LIKE = ENVIRONMENT in {"development", "dev", "local", "test"}

ALLOW_PUBLIC_SEED = env_bool("ALLOW_PUBLIC_SEED", default=IS_DEV_LIKE)
ALLOW_DEFAULT_ADMIN_PASSWORD = env_bool("ALLOW_DEFAULT_ADMIN_PASSWORD", default=IS_DEV_LIKE)
ALLOW_DESTRUCTIVE_SEED = env_bool("ALLOW_DESTRUCTIVE_SEED", default=IS_DEV_LIKE)


def parse_cors_origins(raw: str) -> list[str]:
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or (["*"] if IS_DEV_LIKE else [])
