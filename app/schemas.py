"""
Pydantic schemas for AskDB API requests and responses.
"""

from typing import Any, List
from pydantic import BaseModel, Field


class RunSqlRequest(BaseModel):
    """Request payload for executing SQL query."""
    db_id: str = Field(..., description="ID of the database to query (filename without extension)", json_schema_extra={"example": "chinook"})
    sql: str = Field(..., description="SQL SELECT query to execute", json_schema_extra={"example": "SELECT * FROM Artist LIMIT 5;"})


class RunSqlResponse(BaseModel):
    """Response payload containing query results."""
    columns: List[str] = Field(default_factory=list, description="List of column names returned by query")
    rows: List[List[Any]] = Field(default_factory=list, description="List of row values returned by query")


class DatabaseListResponse(BaseModel):
    """Response payload containing available databases."""
    databases: List[str] = Field(default_factory=list, description="List of available database IDs")


class SchemaResponse(BaseModel):
    """Response payload containing extracted database schema."""
    db_id: str = Field(..., description="ID of the database")
    schema_text: str = Field(..., description="Compact formatted schema representation")
