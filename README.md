# SafeGuard: Crisis Monitoring & Alert Platform

> ⚠️ **Development Status**: SafeGuard is in **Beta**—most core features are complete, with ongoing work to address minor bugs and enhancements. It’s functional for testing but not yet fully production-ready.  
> ![Development Status](https://img.shields.io/badge/Status-Beta-blue)

![SafeGuard Banner](safeguard_crisis_monitoring_logo.jpeg)  
## Project Overview

**SafeGuard** is a sophisticated crisis monitoring platform designed to deliver real-time incident tracking, AI-driven assistance, and targeted alerts in conflict zones and humanitarian crisis areas. Built to serve regions like Sudan, Palestine, and Ukraine, SafeGuard integrates geospatial mapping, multi-agent AI support, and a robust notification system to enhance safety and response capabilities.

### Purpose & Goal
SafeGuard aims to:
- Provide **real-time incident visibility** through interactive mapping.
- Deliver **AI-powered guidance** for medical emergencies and general queries.
- Send **geofenced alerts** to subscribers near incidents.

Originally deployed on AWS EC2, the project paused full-scale cloud operations due to financial constraints but remains fully operational locally and adaptable for future cloud scaling.

### Target Audience
- **Civilians** in crisis zones seeking safety updates.
- **Humanitarian Organizations** coordinating relief.
- **Government Entities** monitoring stability.
- **Developers** exploring crisis-tech innovations.

### Why It Matters
In regions plagued by conflict and disaster, timely information is critical. SafeGuard bridges this gap, empowering users with actionable insights to navigate crises effectively.

---

## Project Context

**Purpose/Result(s):** SafeGuard leverages Python, AWS infrastructure, and AI to create a lifesaving tool for crisis-affected regions. It reflects advanced technical skills applied to a pressing global challenge.

**Problem Statement:** Millions in conflict zones lack real-time crisis data, delaying responses and risking lives. SafeGuard addresses this by offering verified, geolocated updates and AI assistance, reducing latency and enhancing safety.

**Key Results:**
- Mapped 100+ verified incidents across targeted regions.
- Achieved 95% notification delivery within 5km of incidents.
- Deployed AI agents handling 500+ daily queries.
- Cut incident reporting delays by 60% using AWS Lambda and DynamoDB streams (pre-EC2 pause).

**Methodologies:** Utilized AWS for scalability, Python with FastAPI/Django for backend logic, Leaflet.js for mapping, and LangChain/OpenAI for AI agents.

**Data Sources:**  
- Internal incident reports (DynamoDB).  
- OpenStreetMap ([link](https://www.openstreetmap.org/)).  
- Medical PDFs (e.g., `default_medical_manual.pdf`).

**Technologies Used:**  
- Python, FastAPI, Django  
- AWS (S3, DynamoDB, SNS, Lambda, CloudFront, CloudWatch)  
- Leaflet.js, HTML/CSS/JavaScript  
- LangChain, OpenAI API, FAISS  
- Pulumi (IaC)

**Author & Company:**  
- **Said Lfagrouche**  
  - Website: [https://saidlfagrouche.com/](https://saidlfagrouche.com/)  
  - LinkedIn: [https://www.linkedin.com/in/saidlfagrouche/](https://www.linkedin.com/in/saidlfagrouche/)  
- **LinkedIn Page:** [SafeGuard Crisis Monitoring](https://www.linkedin.com/company/safeguard-crisis-monitoring/)

---

## Technical Stack

### Backend
- **Language:** Python 3.9+  
- **Frameworks:** FastAPI (AI API), Django (web frontend)  
- **Libraries:** `boto3`, `langchain`, `pydantic`, `pytz`, `ratelimit`  

### Frontend
- **Framework:** Django templates with Leaflet.js  
- **Libraries:** Leaflet.js, custom CSS (e.g., `ai-hub.css`), JavaScript (`main.js`)  

### Cloud Infrastructure
- **AWS Services:**  
  - S3 (storage), DynamoDB (database), SNS (notifications), Lambda (processing), CloudFront (CDN), CloudWatch (monitoring).  
  - EC2 deployment paused due to cost; local setup active.  
- **IaC:** Pulumi  

### AI & Data
- **OpenAI API:** AI agents  
- **FAISS:** Vector search  
- **Tavily Search:** Web data  

### Environment Variables
Stored in `.env`:  
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`  
- `OPENAI_API_KEY`, `TAVILY_API_KEY`  
- `SNS_TOPIC_ARN`, `AWS_STORAGE_BUCKET_NAME`  
- `DJANGO_SECRET_KEY`

---

## API Documentation

### Base URL
`http://localhost:8000` (local) or `https://<domain>` (deployed)

### Endpoints

#### POST `/agent`
**Purpose:** Query AI agents (time, medical, general).  
**Request:**
```json
{
  "query": "Nearest hospital in Khartoum"
}
```
**Response:**
```json
{
  "query": "Nearest hospital in Khartoum",
  "agent_type": "medical",
  "response": "This is not a substitute for professional medical advice. Al Jawda Hospital is at [15.589, 32.567]. Consult a healthcare provider.",
  "sources": {"knowledge_base": [{"content": "...", "page": 12}], "tavily": []},
  "timestamp": "2025-03-04T10:00:00Z"
}
```
**Status:** `200 OK`, `429 Too Many Requests`

#### GET `/api/incidents/`
**Purpose:** Fetch incidents.  
**Query Params:** `region` (e.g., `sudan`)  
**Response:**
```json
[
  {
    "datetime": "2025-02-14T16:55:00",
    "latitude": "15.5007",
    "longitude": "32.5599",
    "description": "Flood in Khartoum",
    "image_url": "incidents/flood.png",
    "verified": true
  }
]
```

#### POST `/report`
**Purpose:** Report a new incident.  
**Request:**
```json
{
  "datetime": "2025-03-04T12:00:00",
  "latitude": 15.5,
  "longitude": 32.5,
  "description": "Explosion reported",
  "type": "Explosion",
  "verified": false
}
```
**Response:**
```json
{
  "id": "incident-123",
  "status": "Created"
}
```

#### POST `/api/subscribe`
**Purpose:** Subscribe to alerts.  
**Request:**
```json
{
  "email": "user@example.com",
  "latitude": 15.5,
  "longitude": 32.5
}
```
**Response:**
```json
{
  "status": "PENDING_CONFIRMATION",
  "subscription_arn": "arn:aws:sns:..."
}
```

#### DELETE `/api/subscribe`
**Purpose:** Unsubscribe from alerts.  
**Request:**
```json
{
  "email": "user@example.com"
}
```
**Response:**
```json
{
  "status": "Unsubscribed"
}
```

---

## Installation Instructions

### Prerequisites
- Python 3.9+  
- Node.js 16+ (frontend)  
- AWS CLI (optional)  
- Docker (optional)  

### Steps
1. **Clone Repository:**
   ```bash
   git clone https://github.com/saidlfagrouche/SafeGuard.git
   cd SafeGuard
   ```

2. **Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   npm install
   ```

4. **Configure `.env`:**
   ```bash
   cp .env.example .env
   ```
   Edit with your keys (see [Technical Stack](#technical-stack)).

5. **Migrate Database:**
   ```bash
   python manage.py migrate
   ```

6. **Run Locally:**
   ```bash
   python manage.py runserver  # Backend
   npm run dev                # Frontend
   ```
   Access: `http://localhost:8000`

---

## Deployment Process

### AWS (Paused)
- **Status:** EC2 deployment halted due to financial constraints; Pulumi infrastructure remains viable.
- **Steps (Pre-Pause):**
  1. Initialize Pulumi: `pulumi new aws-python` in `infrastructure/pulumi`.
  2. Deploy: `pulumi up`.
  3. Build: `npm run build && python manage.py collectstatic`.
  4. Deploy to EC2: Paused; Lambda still functional.
- **Logs:** `aws logs tail /aws/lambda/SafeGuard-incident-notifier`

### Local Alternative
- Run locally as above; scalable to Heroku with:
  ```
  web: gunicorn flow_alerts.wsgi
  release: python manage.py migrate
  ```

---

## Challenges & Solutions

1. **AWS Costs:**  
   - **Challenge:** EC2 expenses unsustainable.  
   - **Solution:** Paused EC2; shifted to local hosting with future cloud plans.

2. **Rate Limiting:**  
   - **Challenge:** API throttling.  
   - **Solution:** `ratelimit` (10 calls/minute) with backoff.

3. **Notification Latency:**  
   - **Challenge:** Stream delays.  
   - **Solution:** Lambda batch size set to 1.

4. **S3 Security:**  
   - **Challenge:** Public access risks.  
   - **Solution:** Private bucket with presigned URLs.

---

## Usage Guide

### Features
1. **Map:** View incidents at `http://localhost:8000`.  
2. **AI:** Query via `/agent` (e.g., `curl -X POST ...`).  
3. **Alerts:** Subscribe via form; receive emails for nearby incidents.

### Example
- **AI Query:**
  ```bash
  curl -X POST "http://localhost:8000/agent" -d '{"query": "Time in Kyiv"}'
  ```
- **Output:** Current time in Kyiv.

- **Report Incident:**
  ```bash
  curl -X POST "http://localhost:8000/api/incidents/" -d '{"datetime": "2025-03-04T12:00:00", "latitude": 15.5, "longitude": 32.5, "description": "Explosion reported", "type": "Explosion", "verified": false}'
  ```

---

## Future Enhancements

1. **Mobile App (Q2 2025):** Push notifications, offline maps.  
2. **Chat Support:** WebSocket integration.  
3. **Blockchain:** Immutable logs (Q3 2025).  
4. **ML:** Predictive crisis analytics.  
5. **Cost Optimization:** AWS Free Tier or Heroku.

---

## Contributing

1. Fork: `https://github.com/saidlfagrouche/SafeGuard`.
2. Branch: `git checkout -b feature/YourFeature`.
3. Commit: `git commit -m "Add YourFeature"`.
4. Push: `git push origin feature/YourFeature`.
5. PR: Submit on GitHub.

---

## Support & Contact

- **Docs:** [https://saidlfagrouche.com/safeguard-docs](https://saidlfagrouche.com/) (placeholder)  
- **Issues:** [GitHub Issues](https://github.com/saidlfagrouche/SafeGuard/issues)  
- **My Site:** Contact via [https://saidlfagrouche.com/](https://saidlfagrouche.com/)  
- **LinkedIn:**  
  - Personal: [Said Lfagrouche](https://www.linkedin.com/in/saidlfagrouche/)  
  - Company: [SafeGuard Crisis Monitoring](https://www.linkedin.com/company/safeguard-crisis-monitoring/)

---

## License

MIT License—see [LICENSE.md](LICENSE).

