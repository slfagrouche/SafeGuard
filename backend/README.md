# SafeGuard Backend

## Quick run

1. Copy `.env.example` to `.env`
2. Set `MONGO_URL`, `DB_NAME`, `JWT_SECRET`, `ADMIN_PASSWORD`
3. `uvicorn server:app --host 0.0.0.0 --port 8000 --reload`

## Security toggles

| Variable | Effect |
|---|---|
| `ALLOW_PUBLIC_SEED` | `true` = `/api/seed/` is public |
| `ALLOW_DEFAULT_ADMIN_PASSWORD` | `true` = startup ok without ADMIN_PASSWORD |
| `ALLOW_DESTRUCTIVE_SEED` | `true` = seed can reset collections |

## LLM provider

- `AI_PROVIDER=openai` (default) with `OPENAI_API_KEY`
- `AI_PROVIDER=ollamafreeapi` for local Ollama

## Testing

```bash
python -m pytest backend/tests/test_hardening.py -q
```
