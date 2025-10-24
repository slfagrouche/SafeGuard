import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from auth import create_access_token, create_refresh_token, get_current_user, verify_password
from db import db
from rate_limit import check_rate_limit, rate_limit_response

router = APIRouter(prefix="/api")


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
async def login(request: Request, body: LoginRequest):
    if not check_rate_limit(request, "auth_login", limit=10, window_seconds=900):
        return rate_limit_response("Login rate limit exceeded (10/15min).")
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        return JSONResponse({"detail": "Invalid email or password"}, status_code=401)

    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)

    response_data = {
        "_id": user_id,
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user.get("role", "user"),
    }
    response = JSONResponse(content=response_data)
    cookie_secure = os.environ.get("ENVIRONMENT", "development").strip().lower() == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=cookie_secure,
        samesite="lax",
        max_age=86400,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=cookie_secure,
        samesite="lax",
        max_age=604800,
        path="/",
    )
    return response


@router.get("/auth/me")
async def get_me(request: Request):
    return await get_current_user(request)


@router.post("/auth/logout")
async def logout():
    response = JSONResponse(content={"success": True})
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return response

