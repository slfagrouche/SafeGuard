import os

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "safeguard_test")

import asyncio

from routers.seed import seed_allows_destructive_reset, seed_requires_admin
from services_ai import process_ai_chat
from state import ai_tasks
from startup import resolve_admin_password


def test_seed_requires_admin_when_public_seed_disabled():
    assert seed_requires_admin(False) is True


def test_seed_does_not_require_admin_when_public_seed_enabled():
    assert seed_requires_admin(True) is False


def test_seed_destructive_reset_flag():
    assert seed_allows_destructive_reset(True) is True
    assert seed_allows_destructive_reset(False) is False


def test_resolve_admin_password_prefers_explicit_value():
    assert resolve_admin_password("explicit-secret", allow_default=False) == "explicit-secret"


def test_resolve_admin_password_returns_none_when_missing():
    assert resolve_admin_password(None, allow_default=True) is None
    assert resolve_admin_password(None, allow_default=False) is None


def test_ai_provider_switch_to_ollamafreeapi(monkeypatch):
    async def fake_ollama(agent_type, message):
        return "ollama-response"

    monkeypatch.setenv("AI_PROVIDER", "ollamafreeapi")
    monkeypatch.setattr("services_ai._run_ollamafreeapi", fake_ollama)

    task_id = "t1"
    ai_tasks[task_id] = {
        "status": "processing",
        "content": None,
        "usage": None,
        "agent_type": "general",
        "tool_calls": [],
        "message": "AI is thinking...",
    }
    asyncio.run(process_ai_chat(task_id, "general", "hello"))
    assert ai_tasks[task_id]["status"] == "success"
    assert ai_tasks[task_id]["content"] == "ollama-response"


def test_ai_provider_rejects_unsupported_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "unknown-provider")
    task_id = "t2"
    ai_tasks[task_id] = {
        "status": "processing",
        "content": None,
        "usage": None,
        "agent_type": "general",
        "tool_calls": [],
        "message": "AI is thinking...",
    }
    asyncio.run(process_ai_chat(task_id, "general", "hello"))
    assert ai_tasks[task_id]["status"] == "error"
    assert "Unsupported AI_PROVIDER" in ai_tasks[task_id]["error"]
