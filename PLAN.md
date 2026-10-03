# AskDB: Text-to-SQL Analytics App Plan

## Summary
A web application where a user asks a question in plain English, an LLM converts it to a SQLite query, the query is validated and run safely on a read-only database, and the result is shown as a table, optional chart, and a plain-English explanation. Users can also upload a CSV, which becomes a new queryable database.

---

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLite (`sqlite3`)
- **Frontend**: Streamlit
- **LLM**: Gemini via `google-genai` SDK (model name and API key loaded from `.env`)
- **Validation & Processing**: SQLGlot (SQL parsing & safety validation), pandas (CSV ingestion & processing)
- **Testing**: pytest (LLM calls strictly mocked)

---

## How We Work (Rules & Constraints)
1. **Single Step Execution**: Implement ONLY the single step requested. Never start the next step without user approval.
2. **Post-Step Explanation**: After finishing a step, explain in simple words (Hinglish is fine) what was built and why, list created/changed files, provide exact commands to run and verify it, then STOP and wait for approval.
3. **Targeted Changes**: Touch only files needed for the current step. Do not modify existing function signatures unless explicitly required.
4. **Verified APIs**: Verify library names and method names against installed official docs. Never guess API methods.
5. **Mocked Tests**: All pytest suites must mock the LLM. No real Gemini API calls during tests.
6. **No Secrets in Repo**: API keys live only in `.env` (`.env.example` contains placeholders). Keep `.env`, `data/*.sqlite`, and `logs/*.db` in `.gitignore`.
7. **Strict Read-Only Access**: Target databases are ALWAYS opened read-only (`file:path?mode=ro` and `PRAGMA query_only = ON`). No code path may modify target databases.
8. **Student-Friendly Code**: Keep code clean, simple, and well-commented (prefer clarity over cleverness).

---

## Project Structure
```text
AskDB/
├── app/                  # FastAPI backend code, schema extractor, LLM client, validator, agent
├── frontend/             # Streamlit user interface
├── data/                 # SQLite databases (e.g., chinook.sqlite, uploaded CSV dbs)
├── logs/                 # History SQLite database (history.db)
├── tests/                # Pytest unit and integration tests (mocked LLM)
├── eval/                 # Evaluation dataset and accuracy benchmark scripts
├── .env.example          # Template for environment variables
├── .gitignore            # Ignored files and patterns
├── requirements.txt      # Python dependencies
└── PLAN.md               # Step-by-step project plan
```

---

## Implementation Steps Tracker

- [x] **Step 1: Database Ready**
  - Set up project folders, virtual environment, `requirements.txt`, and `.gitignore`.
  - The Chinook database is already at `data/chinook.sqlite`. Do NOT download or create another database.
  - Write a tiny script to run a sample JOIN/GROUP BY query on it and print the result.
  - *Check*: Query result prints in the terminal.

- [ ] **Step 2: Backend SQL Executor**
  - FastAPI app with:
    - `POST /run_sql` (takes `sql` + `db_id`, returns columns and rows as JSON)
    - `GET /databases` (lists databases in `data/`).
  - `db_id` is the file name without extension (`chinook.sqlite` -> `chinook`). Accept only letters, numbers and underscores in `db_id`, so paths like `../` cannot be used to open other files.
  - Use read-only SQLite connections (`mode=ro`, `PRAGMA query_only = ON`).
  - Add `.env` config loader.
  - *Check*: Works interactively from the `/docs` OpenAPI Swagger page.

- [ ] **Step 3: Schema Extraction**
  - Function `get_schema(db_id)` returning compact text of tables, columns, types, primary keys, and foreign keys (via `PRAGMA table_info` and `PRAGMA foreign_key_list`).
  - Add `GET /schema/{db_id}` endpoint.
  - *Check*: Clean, readable schema text is returned.

- [ ] **Step 4: AI Generates SQL**
  - LLM client wrapper using `google-genai` (key validated only when client is created).
  - Prompt structure = rules + schema + user question; returns single SQLite SELECT as structured JSON.
  - Add simple CLI to test: `python -m app.cli --question "..." --db_id chinook`.
  - *Check*: 5 sample questions generate valid and sensible SQL.

- [ ] **Step 5: Safety Layer**
  - Validator using SQLGlot:
    - Exactly one SQL statement.
    - Root must be `SELECT` (CTEs and `UNION` of selects allowed).
    - Reject `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `PRAGMA`, `ATTACH`, etc.
  - Executor safeguards: row limit (default 100), query timeout (default 5s).
  - Write unit tests with malicious inputs (e.g. `SELECT 1; DROP TABLE x`).
  - *Check*: Destructive queries blocked and all tests pass.

- [ ] **Step 6: Error Handling & Retry Loop**
  - Agent flow: Schema -> Generate -> Validate -> Execute.
  - If execution fails: send question + schema + failed SQL + error message back to LLM for correction, validate again, retry up to `MAX_RETRIES` (default 3).
  - Early stop if LLM repeats identical SQL.
  - Return result object with `status` (`success` / `blocked` / `failed`), `sql`, `columns`, `rows`, `retries`, `error`.
  - Add `POST /ask` endpoint.
  - Tests with mocked LLM for: first-try success, repaired success, blocked query, failed query.
  - *Check*: Deliberately wrong-column question gets auto-repaired.

- [ ] **Step 7: Streamlit Frontend**
  - Database dropdown (populated via `GET /databases`), natural language question box, "Ask" button.
  - Status badge, generated SQL block, and result table display.
  - Backend URL configured via environment variable.
  - *Check*: End-to-end question-to-table flow works smoothly in Streamlit UI.

- [ ] **Step 8: CSV Upload Becomes a Database**
  - `POST /upload`: accept `.csv` only, max 5 MB, max 50,000 rows.
  - Read with pandas, sanitize column names (lowercase, non-alphanumeric chars to underscore). Handle CSV edge cases: duplicate column names, empty column names, and names starting with a digit (prefix with `col_`).
  - Save to `data/upload_<random_id>.sqlite` with table name `data`, return new `db_id`.
  - Uploaded databases are queried strictly read-only like standard databases.
  - Add cleanup helper for old temporary uploads.
  - Streamlit UI: add `st.file_uploader`; auto-select newly uploaded `db_id`.
  - Unit tests for validation and sanitization.
  - *Check*: Upload a CSV, ask "how many rows are there?", get accurate answer.

- [ ] **Step 9: Query History**
  - Separate SQLite file `logs/history.db` (never user data DBs), table `history(id, db_id, question, sql, status, created_at)`.
  - Save every `/ask` request (both success and blocked).
  - Add `GET /history?db_id=...` (latest 20 entries).
  - Streamlit sidebar displays history; clicking an item refills the question input.
  - Tests for history persistence and retrieval.
  - *Check*: Ask 3 questions, verify all 3 appear in the sidebar history.

- [ ] **Step 10: Result Charts**
  - Rule-based chart auto-selection:
    - 1 text column + 1 numeric column -> Bar chart (`st.bar_chart`).
    - Date/year/month first column + numeric column -> Line chart (`st.line_chart`).
    - Otherwise -> Table only.
  - Add "Show chart" toggle.
  - If > 50 categories, show top 20 or fallback to table.
  - *Check*: "top 5 artists by sales" renders an intuitive bar chart.

- [ ] **Step 11: Explanation & SQLite Cache (Optional/Enhancement)**
  - Plain-English explanation of results using only facts from returned rows (explicitly state if result is empty).
  - Cache results in SQLite keyed by `(db_id, question)` to skip LLM calls on repeated questions. Cache only success results, never blocked or failed ones.
  - *Check*: Repeated question returns instantly without making an LLM API call.

- [ ] **Step 12: Accuracy Benchmark & Evaluation**
  - Evaluation runner reading `eval/questions.json`. The user writes these 15-20 questions and gold SQL manually. The agent must NOT generate, suggest or edit questions or gold SQL. If the file is missing, stop and ask.
  - Compare result tables (not raw SQL strings): ignore column names, ignore row order unless gold SQL contains `ORDER BY`, apply floating-point tolerance.
  - Print overall accuracy and accuracy per difficulty level; save results to `eval/results/`.
  - *Check*: Evaluation script outputs accuracy percentage.

- [ ] **Step 13: Deployment & Documentation**
  - Dockerfiles / deployment configuration for backend and frontend.
  - `README.md` with system architecture diagram, features, setup guide, accuracy results, limitations, and UI screenshots.
  - *Check*: Application starts and runs seamlessly from a clean repository clone.
