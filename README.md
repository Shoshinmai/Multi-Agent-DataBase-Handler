# 🗄️ Multi-Agent DataBase Handler

> **Talk to your database in plain English.** No SQL? No problem.

A multi-agent system that turns natural language into SQL, executes it safely, and returns results—powered by **LangGraph**, **Google Gemini**, and **PostgreSQL**.

---

## 🎯 What Does It Do?

Imagine asking your database questions like you'd ask a colleague:

- *"Show me all users"*
- *"Who made purchases over $100?"*
- *"Users whose total spending is greater than the average"*

The system **understands** your intent, **builds** the SQL, **runs** it, and **returns** the data—all through a single API call.

---

## 🧠 How It Works: The Agent Pipeline

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Your Query    │ ──► │  🧠 Intent Agent │ ──► │ 📝 SQL Generator│ ──► │ ⚡ Executor  │
│ "Show top 5     │     │  (Gemini LLM)    │     │  (Deterministic) │     │  (PostgreSQL)│
│  spenders"      │     │                  │     │                  │     │              │
└─────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────┘
        │                          │                        │                      │
        │                          │                        │                      │
        ▼                          ▼                        ▼                      ▼
   Natural               IntentState                 SELECT ...            {columns, rows}
    Text               (structured JSON)                  ;                   (results)
```

| Step | Agent | Role |
|------|-------|------|
| **1** | **Intent Agent** | Uses Gemini to parse your natural language into a structured `IntentState` (tables, columns, joins, filters, aggregations) |
| **2** | **SQL Generator** | Converts `IntentState` into valid SQL—deterministic, no LLM, predictable output |
| **3** | **SQL Executor** | Runs the SQL against PostgreSQL, validates it (SELECT-only, no DROP/TRUNCATE), returns rows |

---

## 📊 Database Schema

The system works with a simple **User + Purchase** model:

```
┌─────────────────────────────┐         ┌─────────────────────────────┐
│           User              │         │         Purchase            │
├─────────────────────────────┤         ├─────────────────────────────┤
│ id (PK)                     │◄────────│ user_id (FK)                │
│ name                        │         │ id (PK)                     │
│ email                       │         │ amount                      │
│ created_at                  │         │ purchase_date               │
└─────────────────────────────┘         └─────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **PostgreSQL** (running locally or remote)
- **Google Gemini API key** ([Get one here](https://makersuite.google.com/app/apikey))

### 1. Clone & Install

```bash
git clone <repo-url>
cd Multi-Agent-DataBase-Handler
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
gemini_api_key=your_gemini_api_key_here
```

### 3. Set Up the Database

Update `src/database.py` if needed (default assumes local PostgreSQL):

```python
DATABASE_URL = "postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/sql-handler"
```

Create the database and tables:

```bash
# Create DB in PostgreSQL:
# CREATE DATABASE "sql-handler";

python -c "from src.database import init_db; from src.model_db import *; init_db()"
```

### 4. Run the API

```bash
uvicorn main:app --reload
```

API docs: **http://127.0.0.1:8000/docs**

---

## 📡 API Usage

### Endpoint: `POST /query`

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

### Example Queries to Try

| Natural Language | What It Does |
|------------------|--------------|
| `"Show all users"` | `SELECT * FROM user;` |
| `"List users with their total purchase amount"` | JOIN + SUM aggregation |
| `"Users whose average purchase is greater than 100"` | HAVING with AVG |
| `"Top 5 spenders by total amount"` | ORDER BY SUM, LIMIT 5 |

---

## 📁 Project Structure

```
Multi-Agent-DataBase-Handler/
├── main.py              # FastAPI app entry point
├── graph.py             # LangGraph pipeline (intent → sql → execute)
├── api/
│   ├── routes.py        # /query endpoint
│   └── schema.py        # QueryRequest, QueryResponse
├── src/
│   ├── agents/
│   │   ├── intent_agent.py   # LLM-based intent extraction
│   │   ├── sql_generator.py  # IntentState → SQL
│   │   └── sql_executor.py   # SQL execution + validation
│   ├── database.py      # PostgreSQL engine + session
│   └── model_db.py      # User, Purchase models (SQLModel)
├── intent.ipynb         # Intent agent experiments
├── graph.ipynb          # Graph flow experiments
└── sqlgenerator.ipynb   # SQL generator development
```

---

## 🔒 Safety

- **Read-only by design**: Only `SELECT` queries are allowed
- **Blocked keywords**: `DROP`, `TRUNCATE`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`
- **Single statement**: Multiple SQL statements in one string are rejected

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI |
| Orchestration | LangGraph |
| LLM | Google Gemini (via LangChain) |
| Database | PostgreSQL + SQLModel (SQLAlchemy) |
| Validation | Pydantic |

---

## 📜 License

See [LICENSE](LICENSE).
