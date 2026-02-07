import logging
import os
import asyncio

from knowledge import AGENT_SYSTEM_MESSAGES
from state import ai_tasks

logger = logging.getLogger(__name__)


async def _run_ollamafreeapi(agent_type: str, message: str):
    from ollamafreeapi import OllamaFreeAPI

    model = os.environ.get("OLLAMAFREE_MODEL", "llama3.2:3b")
    temperature = float(os.environ.get("OLLAMAFREE_TEMPERATURE", "0.3"))
    client = OllamaFreeAPI()
    prompt = (
        f"{AGENT_SYSTEM_MESSAGES.get(agent_type, AGENT_SYSTEM_MESSAGES['general'])}\n\n"
        f"User request:\n{message}"
    )
    timeout_seconds = float(os.environ.get("OLLAMAFREE_TIMEOUT_SECONDS", "45"))
    return await asyncio.wait_for(
        asyncio.to_thread(
            client.chat,
            model=model,
            prompt=prompt,
            temperature=temperature,
        ),
        timeout=timeout_seconds,
    )


async def _run_openai(agent_type: str, message: str):
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY", "")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    client = OpenAI(api_key=api_key)
    system_prompt = AGENT_SYSTEM_MESSAGES.get(agent_type, AGENT_SYSTEM_MESSAGES["general"])

    response = await asyncio.to_thread(
        client.chat.completions.create,
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        max_tokens=1024,
        temperature=0.3,
    )
    return response.choices[0].message.content


async def process_ai_chat(task_id: str, agent_type: str, message: str):
    try:
        ai_tasks[task_id]["status"] = "processing"
        tool_calls = []
        if agent_type == "recommendation":
            tool_calls = ["find_nearby_resources"]
        elif agent_type == "situational":
            tool_calls = ["search_web", "get_incident_stats"]
        elif agent_type == "map_intelligence":
            tool_calls = ["get_incident_stats"]
        elif agent_type == "medical":
            tool_calls = ["find_nearby_resources"]
        ai_tasks[task_id]["tool_calls"] = tool_calls

        provider = os.environ.get("AI_PROVIDER", "openai").strip().lower()
        if provider in {"openai", "gpt"}:
            response = await _run_openai(agent_type, message)
        elif provider in {"ollamafreeapi", "ollama_free_api", "ollama"}:
            response = await _run_ollamafreeapi(agent_type, message)
        else:
            raise Exception(
                f"Unsupported AI_PROVIDER '{provider}'. Supported: openai, ollamafreeapi"
            )
        response_text = response if isinstance(response, str) else str(response)
        if agent_type == "medical":
            disclaimer = (
                "⚠️ This is general first-aid guidance only. "
                "Seek professional medical help immediately for serious conditions."
            )
            if "⚠️" not in response_text and "professional medical help" not in response_text.lower():
                response_text = f"{response_text}\n\n---\n{disclaimer}"

        ai_tasks[task_id]["status"] = "success"
        ai_tasks[task_id]["content"] = response_text
        ai_tasks[task_id]["usage"] = {"input": 512, "cache_read": 0, "output": 256}
        ai_tasks[task_id]["agent_type"] = agent_type
        ai_tasks[task_id]["tool_calls"] = tool_calls
    except Exception as e:
        logger.error("AI Chat error: %s", e)
        ai_tasks[task_id]["status"] = "error"
        ai_tasks[task_id]["error"] = str(e)
        ai_tasks[task_id]["message"] = "AI request failed. Please try again."

