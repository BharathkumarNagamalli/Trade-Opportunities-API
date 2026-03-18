# 🇮🇳 Trade Opportunities API

A **FastAPI** service that analyzes market data and provides AI-powered trade
opportunity insights for specific sectors in India.  
Built as the Appscrip AI Engineer Assignment.

---

## ✨ Features

| Feature | Implementation |
|---|---|
| **Single analysis endpoint** | `GET /analyze/{sector}` returns a full markdown report |
| **AI Analysis** | G4F (GPT-4 Free) generates structured sector reports |
| **Live Data** | DuckDuckGo search fetches current news (no API key needed) |
| **Authentication** | Guest JWT tokens via `POST /token` (60-min expiry) |
| **Rate Limiting** | 10 requests / 60 seconds per session (sliding window) |
| **Session Tracking** | In-memory session store tracks usage per user |
| **Input Validation** | Pydantic v2 + sector allowlist prevent bad input |
| **Async** | Fully async with `asyncio.gather` for concurrent data fetching |
| **API Docs** | Auto-generated at `/docs` (Swagger UI) and `/redoc` |

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/trade-opportunities-api.git
cd trade-opportunities-api

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env if you'd like to configure custom variables
```

The system is configured to use G4F internally, which provides free GPT-4 analysis without needing any API keys.

### 3. Run the server

```bash
uvicorn main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

---

## 📡 API Usage

### Step 1 — Get a token

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "bunny_dev"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "session_id": "uuid-here"
}
```

### Step 2 — Analyze a sector

```bash
curl -X GET http://localhost:8000/analyze/pharmaceuticals \
  -H "Authorization: Bearer <your_token>"
```

**Response:**
```json
{
  "sector": "pharmaceuticals",
  "report": "# 🇮🇳 Trade Opportunities Report: Pharmaceuticals\n\n## 1. Executive Summary\n...",
  "sources_count": 18,
  "processing_time_seconds": 4.32,
  "session_id": "uuid-here",
  "generated_at": "2024-11-15T10:23:45.123Z"
}
```

The `report` field is valid Markdown — save it as a `.md` file for a
beautifully formatted document.

### Step 3 — Check your session

```bash
curl http://localhost:8000/session \
  -H "Authorization: Bearer <your_token>"
```

---

## 🗂️ Supported Sectors

`agriculture` · `aerospace` · `automotive` · `chemicals` · `defence` ·
`education` · `electronics` · `energy` · `finance` · `food` · `healthcare` ·
`infrastructure` · `logistics` · `manufacturing` · `pharmaceuticals` ·
`retail` · `technology` · `telecom` · `textiles` · `tourism`

---

## 🏗️ Architecture

```
trade-opportunities-api/
├── main.py              # FastAPI app, routes, middleware
├── auth.py              # JWT token creation & verification
├── rate_limiter.py      # Sliding-window in-memory rate limiter
├── session_manager.py   # In-memory session store
├── data_collector.py    # DuckDuckGo web search for live market data
├── ai_analyzer.py       # Google Gemini prompt building & analysis
├── models.py            # Pydantic request/response schemas
├── requirements.txt
├── .env.example
└── README.md
```

### Request Flow

```
Client
  │
  ├─► POST /token ──► JWT issued ──► client stores token
  │
  └─► GET /analyze/{sector}
          │
          ├─ [Auth] Verify JWT
          ├─ [Rate Limit] Check sliding window (10 req/60s)
          ├─ [Validate] sector in allowlist
          ├─ [DataCollector] 4× DuckDuckGo queries (concurrent)
          ├─ [AIAnalyzer] Build prompt → G4F API
          └─ Return AnalysisResponse (sector, report, metadata)
```

---

## 🔒 Security

- **Authentication**: Stateless JWT bearer tokens (HS256). No passwords stored.
- **Input validation**: Pydantic field validators + explicit sector allowlist blocks injection.
- **Rate limiting**: Per-session sliding-window (10 req / 60 s) with `Retry-After` header.
- **Secret management**: `JWT_SECRET_KEY` loaded from environment — never hardcoded.
- **CORS**: Configurable via `allow_origins` in `main.py`.

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `JWT_SECRET_KEY` | No | dev default | Change in production! |

---

## 📝 Sample Report Output

When you call `GET /analyze/pharmaceuticals` the `report` field contains a
full Markdown document like:

```markdown
# 🇮🇳 Trade Opportunities Report: Pharmaceuticals

## 1. Executive Summary
India is the world's largest supplier of generic medicines, accounting for
approximately 20% of global generic exports by volume ...

## 3. Export Opportunities
| Product / Sub-sector | Key Destination Markets | Opportunity Size | Growth Driver |
|---|---|---|---|
| Generic APIs | USA, Europe, Africa | $8B+ | USFDA approvals |
| Vaccines | COVAX nations, Africa | $3B | Global health push |
...
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `pydantic` | Request/response validation |
| `PyJWT` | JWT token handling |
| `g4f` | Free GPT-4 AI client |
| `duckduckgo-search` | Free web search (no key needed) |
| `python-dotenv` | `.env` file loading |

---

## 🧪 Testing the API

```bash
# Health check (no auth needed)
curl http://localhost:8000/health

# Full test flow
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username":"tester"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl http://localhost:8000/analyze/technology \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 👨‍💻 Author

**Bharath Kumar Nagamalli (Bunny)**  
B.Tech CSE · Malla Reddy Institute of Engineering & Technology  
GitHub: [BharathkumarNagamalli](https://github.com/BharathkumarNagamalli)
