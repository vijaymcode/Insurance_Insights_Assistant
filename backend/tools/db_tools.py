import sqlite3
import json
from typing import Any
from config import DB_PATH, ALLOWED_TABLES, MAX_ROWS, TABLE_SCHEMA


def get_schema_text() -> str:
    """Return a formatted schema string for use in prompts."""
    lines = []
    for table, info in TABLE_SCHEMA.items():
        lines.append(f"Table: {table}  -- {info['description']}")
        for col, desc in info["columns"].items():
            lines.append(f"  {col}: {desc}")
        lines.append("")
    return "\n".join(lines)


def get_schema_dict() -> dict:
    return TABLE_SCHEMA


def execute_query(sql: str) -> dict[str, Any]:
    """
    Execute a validated SELECT query against the insurance database.
    Returns {"columns": [...], "rows": [...], "row_count": int} on success,
    or {"error": "..."} on failure.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Extra safety: enforce read-only by using a read-only URI
        conn_ro = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn_ro.row_factory = sqlite3.Row
        cur = conn_ro.cursor()
        cur.execute(sql)
        rows = cur.fetchmany(MAX_ROWS)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        result = [dict(row) for row in rows]
        conn_ro.close()

        return {
            "columns": columns,
            "rows": result,
            "row_count": len(result),
            "truncated": len(result) == MAX_ROWS,
        }
    except Exception as e:
        return {"error": str(e)}


def get_sample_data(table: str, limit: int = 3) -> list[dict]:
    """Return a few sample rows from a table for context."""
    if table not in ALLOWED_TABLES:
        return []
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table} LIMIT {limit}")  # noqa: S608 – table is allowlisted
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []
