# SafeGuard

Real-time crisis monitoring and alert platform. Track incidents, coordinate emergency response, and get AI-powered safety guidance across conflict zones and humanitarian crises worldwide.

**Live:** [safeguard-neon.vercel.app](https://safeguard-neon.vercel.app/)

## What it does

- **Interactive crisis map** with real-time incident tracking, severity indicators, and marker clustering (Leaflet + WebSocket)
- **5 specialized AI agents** (General, Medical, Situational, Recommendation, Map Intelligence) powered by GPT-4o with tool calling
- **Emergency services** directory with one-tap calling for 15+ countries
- **Incident reporting** with geolocation, image upload, and community verification/flagging
- **Admin dashboard** for incident triage, subscriber management, and analytics
- **Real-time updates** via WebSocket push for new incidents

## Architecture

```
Frontend (React + Tailwind + Leaflet)  -->  Vercel
     |
     v
Backend (FastAPI + Motor)              -->  Railway
     |
     v
MongoDB (Atlas / Railway)              -->  Railway
```

**Backend:** FastAPI with async MongoDB (Motor), JWT auth, rate limiting, structured logging, CORS hardening

**Frontend:** React 19, Tailwind CSS, shadcn/ui (Radix), Leaflet maps with clustering, Recharts analytics

**AI:** OpenAI GPT-4o with function calling, 5 agent types with domain-specific system prompts and knowledge base (30+ country/first-aid guides)

## Tech stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, Tailwind, shadcn/ui, Leaflet, Recharts |
| Backend | Python 3.12, FastAPI, Motor (async MongoDB), Pydantic |
| AI | OpenAI GPT-4o, tool calling, RAG over local knowledge base |
| Database | MongoDB |
| Auth | JWT (HttpOnly cookies), bcrypt password hashing |
| Infra | Docker, Railway (backend + DB), Vercel (frontend) |
| Real-time | WebSocket (Starlette) |

## Quick start

```bash
# Backend
cd backend
cp .env.example .env        # fill in your keys
pip install -r requirements.txt
uvicorn server:app --reload

# Frontend
cd frontend
cp .env.example .env
yarn install && yarn start
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login (returns JWT cookie) |
| GET | `/api/auth/me` | Current user |
| GET | `/api/incidents/` | List all incidents |
| POST | `/api/report/` | Report new incident |
| POST | `/api/incidents/{id}/flag/` | Flag incident |
| POST | `/api/ai/chat/` | AI chat (async, returns task ID) |
| GET | `/api/ai/status/{id}/` | Poll AI task result |
| GET | `/api/resources/` | List resources |
| GET | `/api/emergency/regions/` | Emergency numbers by region |
| WS | `/ws/incidents` | Real-time incident feed |

## Security

- JWT auth with HttpOnly secure cookies
- bcrypt password hashing
- Per-endpoint rate limiting
- CORS restricted to known origins in production
- No secrets in codebase (env-only configuration)
- Input validation on all endpoints
- Admin-only routes with role-based access

## License

MIT
