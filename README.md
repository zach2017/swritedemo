# Social Work Skills Lab

A comprehensive educational platform for **BSW and MSW students** to practice clinical writing, study case scenarios, and prepare for ASWB licensing exams — with AI-powered evaluation via the Claude API.

---

## Features

| Feature | Description |
|---|---|
| **Case Scenarios** | 12+ detailed scenarios across 8 topic areas (ethics, crisis, clinical, policy, etc.) |
| **Writing Lab** | Structured writing prompts with professional rubrics and AI evaluation |
| **Exam Prep** | ASWB Bachelors, Masters, and Clinical exam info with practice question generator |
| **AI Evaluation** | Claude-powered feedback on student writing with scoring against rubrics |
| **Cost Tracking** | Per-request token and cost tracking with full ledger view |
| **Simulation Mode** | Full demo mode with mock AI responses — no API key required |
| **Image Upload** | File upload endpoint (cloud-storage ready for S3/GCS deployment) |
| **Quick Reference** | NASW Code of Ethics, defense mechanisms, writing format guides |

---

## Quick Start

### 1. Clone and configure

```bash
cd socialwork-platform
cp .env .env.local   # optional: edit to add your API key
```

### 2. Run with Docker Compose

```bash
# Simulation mode (no API key needed)
docker compose up --build

# OR with live Claude API
ANTHROPIC_API_KEY=sk-ant-... SIMULATION_MODE=false docker compose up --build
```

### 3. Open the app

Navigate to **http://localhost:5000**

---

## Configuration

Edit `.env` or pass environment variables:

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | _(empty)_ | Your Claude API key from console.anthropic.com |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Model to use for evaluations |
| `SIMULATION_MODE` | `true` | `true` = mock responses, `false` = live API |

---

## API Endpoints

### Scenarios & Content
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/scenarios` | List scenarios (filter: `?category=`, `?year=`, `?difficulty=`) |
| GET | `/api/scenarios/:id` | Get single scenario |
| GET | `/api/categories` | List topic categories |
| GET | `/api/exam-info` | ASWB exam details |
| GET | `/api/writing-guides` | Documentation format guides |
| GET | `/api/quick-reference` | NASW codes, defense mechanisms |

### AI Features
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/evaluate` | Evaluate student writing against rubric |
| POST | `/api/feedback` | General writing feedback |
| POST | `/api/practice-question` | Generate exam practice question |

### System
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check and config status |
| GET | `/api/costs` | Cost tracking ledger |
| POST | `/api/costs/reset` | Reset cost data |
| GET | `/api/simulation` | Check simulation status |
| POST | `/api/simulation/toggle` | Toggle simulation mode |
| POST | `/api/upload` | Upload image/file |

---

## Project Structure

```
socialwork-platform/
├── docker-compose.yml       # Docker orchestration
├── Dockerfile               # Container build
├── .env                     # Environment variables
├── backend/
│   ├── app.py               # Flask API server
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── index.html           # Single-page app (Tailwind CSS)
└── data/
    └── scenarios.json       # All scenarios, guides, exam data
```

---

## Scenario Topics

1. **Ethics & Professional Conduct** — Dual relationships, duty to warn, social media boundaries
2. **Case Management & Documentation** — Biopsychosocial assessments, SOAP notes, transfer summaries
3. **Crisis Intervention** — Suicide risk assessment, safety planning
4. **Human Behavior (HBSE)** — Erikson's stages, developmental theory application
5. **Diversity, Equity & Inclusion** — Cultural competence, intersectionality, acculturation
6. **Social Welfare Policy** — Housing First analysis, policy briefs
7. **Research Methods** — Program evaluation design
8. **Clinical Practice** — Differential diagnosis, DSM-5, treatment planning

---

## Cloud Deployment

The platform is designed for easy cloud deployment:

### Image Upload → Cloud Storage
The `/api/upload` endpoint currently saves to local disk. To deploy to cloud, add an S3/GCS adapter in `backend/app.py`:

```python
# Example S3 integration (add boto3 to requirements.txt)
import boto3
s3 = boto3.client('s3')
s3.upload_fileobj(file, BUCKET, filename)
```

### Deploy to AWS/GCP/Azure
```bash
# Build and push the image
docker build -t socialwork-platform .
docker tag socialwork-platform:latest YOUR_REGISTRY/socialwork-platform:latest
docker push YOUR_REGISTRY/socialwork-platform:latest
```

---

## Cost Tracking

Every AI interaction is tracked with:
- Input/output token counts
- USD cost calculated from published pricing
- Timestamp and action type
- Simulation vs. live flag

Pricing is based on Anthropic's published rates. View the full ledger at the **Costs** tab.

---

## Development

```bash
# Run without Docker (requires Python 3.10+)
cd backend
pip install -r requirements.txt
cd ..
SIMULATION_MODE=true python -m backend.app
```

---

## License

Educational use. Scenario content is original and designed for social work education.
"# swritedemo" 
