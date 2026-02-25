<p align="center">
  <img src="https://img.shields.io/badge/Multi--Agent-SQL-blue?style=for-the-badge" alt="Multi-Agent SQL" />
  <img src="https://img.shields.io/badge/LangGraph-Orchestration-green?style=for-the-badge" alt="LangGraph" />
  <img src="https://img.shields.io/badge/Gemini-LLM-orange?style=for-the-badge" alt="Gemini" />
</p>

<h1 align="center">🗄️ Multi-Agent DataBase Handler</h1>

<p align="center">
  <strong>Talk to your database in plain English.</strong> No SQL? No problem.
</p>

<p align="center">
  A multi-agent system that turns natural language into SQL, executes it safely, and returns results—powered by <strong>LangGraph</strong>, <strong>Google Gemini</strong>, and <strong>PostgreSQL</strong>.
</p>

---

## 🎯 What Does It Do?

Imagine asking your database questions like you'd ask a colleague:

| You Say | The System Does |
|---------|-----------------|
| *"Show me all users"* | `SELECT * FROM user;` |
| *"Who made purchases over $100?"* | JOIN + WHERE filter |
| *"Users whose total spending is greater than the average"* | Subquery with AVG |

The system **understands** your intent, **builds** the SQL, **runs** it, and **returns** the data—all through a single API call.

---

## 🧠 Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Your Query    │ ──► │  🧠 Intent Agent │ ──► │ 📝 SQL Generator│ ──► │ ⚡ Executor  │
│ "Show top 5     │     │  (Gemini LLM)    │     │  (Deterministic) │     │  (PostgreSQL)│
│  spenders"      │     │                  │     │                  │     │              │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └──────────────┘
        │                          │                        │                      │
        │                          │                        │                      │
        ▼                          ▼                        ▼                      ▼
   Natural               IntentState                 SELECT ...            {columns, rows}
    Text               (structured JSON)                  ;                   (results)
```

| Step | Agent | Role |
|------|-------|------|
| **1** | **Intent Agent** | Uses Gemini to parse natural language into structured `IntentState` (tables, columns, joins, filters, aggregations) |
| **2** | **Date Resolver** | Converts relative dates (last month, today) into concrete values |
| **3** | **SQL Generator** | Converts `IntentState` into valid SQL—deterministic, no LLM |
| **4** | **SQL Executor** | Runs SQL against PostgreSQL, validates read-only, returns rows |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **PostgreSQL** (local or remote)
- **Google Gemini API key** → [Get one here](https://makersuite.google.com/app/apikey)

### 1. Clone & Install

```bash
git clone <repo-url>
cd Multi-Agent-DataBase-Handler
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/sql-handler
```

### 3. Set Up the Database

```bash
# In PostgreSQL:
CREATE DATABASE "sql-handler";

# Create tables:
python -c "from src.database import init_db; from src.model_db import *; init_db()"
```

### 4. Run the API

```bash
uvicorn main:app --reload
```

**API docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 API Usage

### `GET /health`

Health check for monitoring and load balancers:

```json
{"status": "ok"}
```

### `POST /query`

**Request:**

```json
{
  "query": "Show all users who made purchases over 50"
}
```

**Response:**

```json
{
  "sql": "SELECT user.name\nFROM user\nJOIN purchase ON user.id = purchase.user_id\nWHERE purchase.amount > 50;",
  "columns": ["name"],
  "rows": [["Alice"], ["Bob"]],
  "row_count": 2
}
```

### Example Queries

| Natural Language | Result |
|------------------|--------|
| `"Show all users"` | `SELECT * FROM user;` |
| `"List users with their total purchase amount"` | JOIN + SUM aggregation |
| `"Users whose average purchase is greater than 100"` | HAVING with AVG |
| `"Top 5 spenders by total amount"` | ORDER BY SUM, LIMIT 5 |

---

## 📁 Project Structure

```
Multi-Agent-DataBase-Handler/
├── main.py                 # FastAPI entry point
├── graph.py                # LangGraph pipeline (intent → date_resolver → sql → execute)
├── config.py               # Environment config
├── api/
│   ├── routes.py           # POST /query endpoint
│   └── schema.py           # QueryRequest, QueryResponse
├── src/
│   ├── agents/
│   │   ├── intent_agent.py  # LLM intent extraction
│   │   ├── sql_generator.py # IntentState → SQL
│   │   └── sql_executor.py  # SQL execution + validation
│   ├── database.py          # PostgreSQL engine
│   ├── model_db.py          # User, Purchase models
│   ├── schema_extractor.py  # Schema for LLM context
│   └── logger.py            # Centralized logging
├── logs/                    # Application logs (app.log, api.log, agents.log)
├── .env.example
├── requirements.txt
└── README.md
```

---

## 📋 Logging & Monitoring

Logs are written to the `logs/` directory:

| File | Purpose |
|------|---------|
| `app.log` | Application lifecycle, graph compilation |
| `api.log` | API requests, query execution |
| `agents.log` | Intent extraction, SQL generation, schema |

Configure via environment:

```env
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s | %(levelname)-8s | %(name)s | %(message)s
```

---

## 🔒 Safety

- **Read-only:** Only `SELECT` queries allowed
- **Blocked keywords:** `DROP`, `TRUNCATE`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`
- **Single statement:** Multiple SQL statements rejected

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI |
| Orchestration | LangGraph |
| LLM | Google Gemini (LangChain) |
| Database | PostgreSQL + SQLModel |
| Validation | Pydantic |

---

## 🔮 Future Work

| Area | Description |
|------|-------------|
| **Multi-database support** | Add MySQL, SQLite adapters |
| **Caching** | Cache frequent queries / intent results |
| **Async execution** | Non-blocking SQL execution |
| **Streaming** | Stream large result sets |
| **Auth & rate limiting** | API keys, per-user quotas |
| **Observability** | OpenTelemetry, Prometheus metrics |
| **INSERT/UPDATE** | Controlled write operations with confirmation |
| **Query explanation** | Natural language explanation of generated SQL |
| **Schema evolution** | Auto-detect schema changes and update prompts |

---

## 📜 License

See [LICENSE](LICENSE).
