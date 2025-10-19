import logging
import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from config import parse_cors_origins
from realtime import register_websocket
from routers.admin import router as admin_router
from routers.ai import router as ai_router
from routers.auth import router as auth_router
from routers.emergency import router as emergency_router
from routers.files import router as files_router
from routers.incidents import router as incidents_router
from routers.resources import router as resources_router
from routers.seed import router as seed_router
from routers.system import api_router as system_api_router
from routers.system import health_router
from startup import register_lifecycle

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = FastAPI()
register_lifecycle(app)
register_websocket(app)

cors_origins = parse_cors_origins(os.environ.get("CORS_ORIGINS", "*"))
# Browsers block wildcard origin when credentials are allowed.
allow_credentials = "*" not in cors_origins

for r in [
    auth_router,
    admin_router,
    incidents_router,
    ai_router,
    emergency_router,
    resources_router,
    files_router,
    seed_router,
    system_api_router,
    health_router,
]:
    app.include_router(r)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=allow_credentials,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

