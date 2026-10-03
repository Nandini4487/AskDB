"""
Tests for Step 3: Schema Extraction.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.schema import get_schema

client = TestClient(app)


def test_get_schema_function_chinook():
    """Verify get_schema extracts tables, columns, PKs, and FKs from Chinook."""
    # Find exact casing of chinook from available databases
    dbs = client.get("/databases").json()["databases"]
    db_id = next(db for db in dbs if db.lower() == "chinook")

    schema_text = get_schema(db_id)
    assert isinstance(schema_text, str)
    
    # Verify core tables are present
    assert "Table: Album" in schema_text
    assert "Table: Artist" in schema_text
    assert "Table: Track" in schema_text
    assert "Table: Invoice" in schema_text
    assert "Table: Customer" in schema_text

    # Verify primary key annotation
    assert "ArtistId (INTEGER, PRIMARY KEY)" in schema_text

    # Verify foreign key annotation on Album table
    assert "FOREIGN KEY -> Artist.ArtistId" in schema_text


def test_get_schema_endpoint_success():
    """Verify GET /schema/{db_id} returns 200 with schema text."""
    dbs = client.get("/databases").json()["databases"]
    db_id = next(db for db in dbs if db.lower() == "chinook")

    response = client.get(f"/schema/{db_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["db_id"] == db_id
    assert "Table: Track" in data["schema_text"]
    assert "PRIMARY KEY" in data["schema_text"]


def test_get_schema_endpoint_path_traversal_blocked():
    """Verify path traversal in db_id returns 400."""
    response = client.get("/schema/.._invalid_id")
    assert response.status_code == 400


def test_get_schema_endpoint_nonexistent():
    """Verify requesting schema of a nonexistent db returns 404."""
    response = client.get("/schema/unknown_db_999")
    assert response.status_code == 404
