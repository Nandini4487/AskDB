"""
Database connection and execution utilities for AskDB.
Enforces strict read-only access and safe path resolution.
"""

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException
from app.config import settings

# Regex to allow only letters, numbers, and underscores in db_id
# This prevents directory traversal attacks such as '../etc/passwd'
DB_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


def validate_db_id(db_id: str) -> str:
    """
    Validate that db_id contains only alphanumeric characters and underscores.
    
    Raises:
        HTTPException (400): If db_id contains illegal characters.
    """
    if not db_id or not DB_ID_PATTERN.match(db_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid db_id. Allowed characters are letters, numbers, and underscores only.",
        )
    return db_id


def list_available_databases() -> List[str]:
    """
    Scan the data/ directory and return list of database IDs (file names without extension).
    """
    if not settings.DATA_DIR.exists():
        return []

    databases = []
    # Supported database extensions
    for file in sorted(settings.DATA_DIR.iterdir()):
        if file.is_file() and file.suffix.lower() in [".sqlite", ".db"]:
            # db_id is the file name without extension
            db_id = file.stem
            if DB_ID_PATTERN.match(db_id):
                databases.append(db_id)
    return databases


def get_db_path(db_id: str) -> Path:
    """
    Resolve the absolute file path for a given db_id.
    
    Raises:
        HTTPException (404): If database file does not exist.
    """
    validate_db_id(db_id)

    # Check potential matching extensions
    possible_extensions = [".sqlite", ".db"]
    for ext in possible_extensions:
        exact_path = settings.DATA_DIR / f"{db_id}{ext}"
        if exact_path.exists() and exact_path.is_file():
            return exact_path

    # Case-insensitive fallback check
    if settings.DATA_DIR.exists():
        for file in settings.DATA_DIR.iterdir():
            if file.is_file() and file.suffix.lower() in possible_extensions:
                if file.stem.lower() == db_id.lower():
                    return file

    raise HTTPException(
        status_code=404,
        detail=f"Database '{db_id}' not found in data directory.",
    )


def get_readonly_connection(db_path: Path) -> sqlite3.Connection:
    """
    Open a strictly read-only SQLite connection using URI mode and query_only PRAGMA.
    """
    # Use SQLite URI mode for read-only connection
    db_uri = f"{db_path.resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)
    
    # Enforce read-only constraint at the engine level
    conn.execute("PRAGMA query_only = ON;")
    return conn


def execute_query(db_id: str, sql: str) -> Dict[str, Any]:
    """
    Execute a SQL query against the specified database in read-only mode.
    
    Returns:
        Dict with 'columns' (list of column names) and 'rows' (list of row values).
    
    Raises:
        HTTPException: If execution fails or violates read-only constraints.
    """
    db_path = get_db_path(db_id)
    conn = get_readonly_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        
        # Get column names if query returned a result set
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()
            # Convert tuples to lists for standard JSON serialization
            rows = [list(row) for row in raw_rows]
        else:
            columns = []
            rows = []

        return {
            "columns": columns,
            "rows": rows,
        }

    except sqlite3.Error as e:
        raise HTTPException(
            status_code=400,
            detail=f"SQLite execution error: {str(e)}",
        )
    finally:
        conn.close()
