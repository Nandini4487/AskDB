"""
Schema extraction utilities for AskDB.
Inspects tables, columns, data types, primary keys, and foreign keys using SQLite PRAGMAs.
"""

from typing import Dict, List, Tuple
from app.database import get_db_path, get_readonly_connection, validate_db_id


def get_schema(db_id: str) -> str:
    """
    Extract a compact, human- and LLM-readable schema representation of a database.
    
    Uses:
      - sqlite_master to find all user tables
      - PRAGMA table_info(<table>) for columns, types, and primary keys
      - PRAGMA foreign_key_list(<table>) for foreign key relationships
    
    Returns:
        A formatted string describing all tables, columns, and relationships.
    """
    validate_db_id(db_id)
    db_path = get_db_path(db_id)
    conn = get_readonly_connection(db_path)
    cursor = conn.cursor()

    try:
        # Get all user table names (excluding internal SQLite system tables)
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            return f"Database '{db_id}' contains no user tables."

        schema_lines: List[str] = []
        schema_lines.append(f"Database Schema: {db_id}")
        schema_lines.append("=" * (len(db_id) + 17))

        for table in tables:
            schema_lines.append(f"\nTable: {table}")

            # 1. Fetch foreign keys for this table
            # PRAGMA foreign_key_list returns: (id, seq, table, from, to, on_update, on_delete, match)
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            fk_rows = cursor.fetchall()
            # Map column_name -> (target_table, target_column)
            fk_map: Dict[str, Tuple[str, str]] = {}
            for fk in fk_rows:
                from_col = fk[3]
                to_table = fk[2]
                to_col = fk[4]
                fk_map[from_col] = (to_table, to_col)

            # 2. Fetch column definitions for this table
            # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
            cursor.execute(f"PRAGMA table_info({table});")
            col_rows = cursor.fetchall()

            for col in col_rows:
                col_name = col[1]
                col_type = col[2].upper() if col[2] else "TEXT"
                is_pk = bool(col[5])

                # Build annotations (PK, FK)
                annotations: List[str] = []
                if is_pk:
                    annotations.append("PRIMARY KEY")
                if col_name in fk_map:
                    target_table, target_col = fk_map[col_name]
                    annotations.append(f"FOREIGN KEY -> {target_table}.{target_col}")

                annotation_str = f", {', '.join(annotations)}" if annotations else ""
                schema_lines.append(f"  - {col_name} ({col_type}{annotation_str})")

        return "\n".join(schema_lines)

    finally:
        conn.close()
