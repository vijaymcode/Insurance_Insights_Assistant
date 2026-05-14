# Insurance Insights Assistant

A natural-language analytics chatbot for insurance data. Ask business questions in plain English and get SQL-backed answers with a results table — no SQL knowledge required.

![Stack](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-blue) ![Stack](https://img.shields.io/badge/Backend-Flask%20%2B%20LangChain-green) ![Stack](https://img.shields.io/badge/LLM-OpenAI%20GPT--4o-orange) ![Stack](https://img.shields.io/badge/Database-SQLite-lightgrey)

---

## How it works

```
User question
     │
     ▼
Query Generation Agent  ──►  OpenAI GPT-4o generates a SQLite SELECT
     │
     ▼
Validation Agent        ──►  Rule-based guardrails (SELECT-only, allowed tables,
     │                        column check, no dangerous functions)
     ▼
SQL Executor            ──►  Read-only query against the SQLite database
     │
     ▼
Orchestrator            ──►  GPT-4o synthesises a plain-English summary
     │
     ▼
React UI                ──►  Answer + collapsible SQL + results table
```

**Two-agent pipeline:**
- **Query Agent** — converts the user's question into a valid SQLite `SELECT` using a domain-specific system prompt that understands insurance terminology (loss ratio, policy in force, risk score, etc.)
- **Validation Agent** — enforces safety rules before any query runs: `SELECT`-only, approved tables only, no dangerous built-in functions, max 5 JOINs

**Sample database (auto-generated at startup):**
| Table | Rows | Description |
|---|---|---|
| `customers` | 100 | Name, age, state, region, risk score |
| `policies` | ~200 | Type (auto/home/life/health), premium, status, coverage |
| `claims` | ~150 | Amount, status (pending/approved/denied/settled), type |

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.10 or newer |
| Node.js | 18 or newer |
| npm | 9 or newer |
| OpenAI API key | [platform.openai.com](https://platform.openai.com) |

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd Insurance_Insights_Assistant
```

### 2. Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Configure your API key** — create a file called `.env` inside the `backend/` folder:

```env
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o
MAX_TOKENS=4096
```

> `MODEL_NAME` defaults to `gpt-4o`. You can use `gpt-4o-mini` for lower cost.

**Start the backend:**

```bash
# Still inside backend/ with the venv active
python app.py
```

The database is created and seeded automatically on first run. The API listens on **http://localhost:5000**.

### 3. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The UI is served at **http://localhost:5173**.

---

## Usage

Open **http://localhost:5173** in your browser.

The left sidebar shows the full database schema. The chat area starts with six example questions — click any of them or type your own.

**Example questions to try:**

- What is the total claims cost by region?
- Show me the loss ratio by policy type.
- Which 10 customers have the highest total premiums?
- How many active policies are there by type?
- What percentage of claims are denied?
- What is the average claim amount for auto policies?
- Show me the monthly claim count trend for 2024.
- Which state has the highest average risk score?

Each response shows:
- A plain-English summary of the results
- A collapsible **Generated SQL** panel (with confidence rating and copy button)
- A scrollable results table with a **CSV export** button

Use the **↺ reset** button in the bottom-left to clear the conversation and start fresh.

---

## Project structure

```
├── backend/
│   ├── app.py                  # Flask REST API (port 5000)
│   ├── config.py               # API keys, model, schema definitions
│   ├── requirements.txt
│   ├── .env.example            # Copy to .env and add your key
│   ├── agents/
│   │   ├── query_agent.py      # NL → SQL via OpenAI
│   │   ├── validation_agent.py # Safety guardrails
│   │   └── orchestrator.py     # Pipeline coordinator + memory
│   ├── tools/
│   │   └── db_tools.py         # Read-only SQL executor + schema helper
│   ├── memory/
│   │   └── agent_memory.py     # Conversation history + query cache
│   └── database/
│       ├── setup.py            # Schema creation + seed data generator
│       └── insurance.db        # SQLite file (auto-created)
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js          # Proxies /api → localhost:5000
│   └── src/
│       ├── App.jsx             # Root layout
│       └── components/
│           ├── Chat.jsx        # Chat container + suggestion chips
│           ├── Message.jsx     # User / assistant message bubbles
│           ├── DataTable.jsx   # Results table with CSV export
│           ├── SqlBlock.jsx    # Collapsible SQL viewer
│           └── SchemaViewer.jsx# Live schema sidebar
│
├── start_backend.ps1           # Windows shortcut: starts the Flask server
└── start_frontend.ps1          # Windows shortcut: starts the Vite dev server
```

---

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/chat` | Send a message `{ "message": "..." }` |
| `GET` | `/api/schema` | Returns the full table schema |
| `POST` | `/api/reset` | Clears conversation memory |
| `GET` | `/api/suggest` | Returns example questions |

---

## Guardrails

The validation agent enforces these rules before executing any query:

- Only `SELECT` statements — `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, etc. are blocked
- Only the three approved tables: `customers`, `policies`, `claims`
- No dangerous SQLite functions (`load_extension`, `readfile`, `writefile`)
- Maximum 5 `JOIN`s per query
- All connections are opened in read-only mode (`?mode=ro`)

---

## Re-seeding the database

To reset the database with fresh sample data:

```bash
cd backend
python database/setup.py
```

This drops and recreates all tables with 100 customers, ~200 policies, and ~150 claims.
