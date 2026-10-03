"""
FastAPI application entry point for AskDB backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import execute_query, list_available_databases
from app.schema import get_schema
from app.schemas import (
    DatabaseListResponse,
    RunSqlRequest,
    RunSqlResponse,
    SchemaResponse,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for AskDB Text-to-SQL Analytics App",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root_info():
    """Root status and service info."""
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
    }


@app.get(
    "/databases",
    response_model=DatabaseListResponse,
    tags=["Database"],
    summary="List available databases",
)
def get_databases():
    """
    List all queryable databases located in the data/ directory.
    Returns database IDs (file names without extension).
    """
    dbs = list_available_databases()
    return DatabaseListResponse(databases=dbs)


@app.get(
    "/schema/{db_id}",
    response_model=SchemaResponse,
    tags=["Database"],
    summary="Extract compact database schema",
)
def get_database_schema(db_id: str):
    """
    Extract compact schema text for the specified database ID,
    including tables, columns, types, primary keys, and foreign keys.
    """
    schema_text = get_schema(db_id=db_id)
    return SchemaResponse(db_id=db_id, schema_text=schema_text)


@app.post(
    "/run_sql",
    response_model=RunSqlResponse,
    tags=["Database"],
    summary="Execute SQL query in read-only mode",
)
def run_sql(request: RunSqlRequest):
    """
    Execute a SQL query against the specified database.
    Target database is strictly opened in read-only mode.
    """
    result = execute_query(db_id=request.db_id, sql=request.sql)
    return RunSqlResponse(
        columns=result["columns"],
        rows=result["rows"],
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
