"""
Tests for Step 2: FastAPI Backend SQL Executor.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify health check endpoint returns 200."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "docs_url" in data


def test_get_databases():
    """Verify GET /databases finds chinook database."""
    response = client.get("/databases")
    assert response.status_code == 200
    data = response.json()
    assert "databases" in data
    assert isinstance(data["databases"], list)
    # Check that chinook is found in the list (case-insensitive)
    lower_dbs = [db.lower() for db in data["databases"]]
    assert "chinook" in lower_dbs


def test_run_sql_valid_query():
    """Verify POST /run_sql successfully executes a SELECT query."""
    # Find exact casing of chinook from /databases
    dbs = client.get("/databases").json()["databases"]
    db_id = next(db for db in dbs if db.lower() == "chinook")

    payload = {
        "db_id": db_id,
        "sql": "SELECT ArtistId, Name FROM Artist ORDER BY ArtistId ASC LIMIT 3;",
    }
    response = client.post("/run_sql", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["columns"] == ["ArtistId", "Name"]
    assert len(data["rows"]) == 3
    assert data["rows"][0] == [1, "AC/DC"]


def test_run_sql_path_traversal_blocked():
    """Verify malicious db_id with path traversal is blocked with 400."""
    payload = {
        "db_id": "../secret",
        "sql": "SELECT 1;",
    }
    response = client.post("/run_sql", json=payload)
    assert response.status_code == 400
    assert "Invalid db_id" in response.json()["detail"]


def test_run_sql_nonexistent_db():
    """Verify querying a non-existent database returns 404."""
    payload = {
        "db_id": "non_existent_db_12345",
        "sql": "SELECT 1;",
    }
    response = client.post("/run_sql", json=payload)
    assert response.status_code == 404


def test_run_sql_readonly_enforced():
    """Verify that mutation queries fail because database is strictly read-only."""
    dbs = client.get("/databases").json()["databases"]
    db_id = next(db for db in dbs if db.lower() == "chinook")

    payload = {
        "db_id": db_id,
        "sql": "CREATE TABLE test_table (id INTEGER PRIMARY KEY);",
    }
    response = client.post("/run_sql", json=payload)
    assert response.status_code == 400
    assert "SQLite execution error" in response.json()["detail"]


def test_run_sql_syntax_error():
    """Verify SQL syntax error returns 400."""
    dbs = client.get("/databases").json()["databases"]
    db_id = next(db for db in dbs if db.lower() == "chinook")

    payload = {
        "db_id": db_id,
        "sql": "SELECT * FORM Artist;",  # Intentional typo 'FORM'
    }
    response = client.post("/run_sql", json=payload)
    assert response.status_code == 400
    assert "SQLite execution error" in response.json()["detail"]
