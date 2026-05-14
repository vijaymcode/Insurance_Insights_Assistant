"""
Validation Agent
Enforces safety and correctness guardrails on generated SQL before execution.
Uses rule-based checks; optionally falls back to LLM for ambiguous cases.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DDL, DML

from config import ALLOWED_TABLES, TABLE_SCHEMA


@dataclass
class ValidationResult:
    valid: bool
    reason: str


# Dangerous keywords that must never appear
_BLOCKED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "REPLACE", "MERGE", "EXEC", "EXECUTE", "PRAGMA", "ATTACH", "DETACH",
}

# SQLite functions that could read files or exfiltrate data
_BLOCKED_FUNCTIONS = {
    "load_extension", "readfile", "writefile", "fts3_tokenizer",
}


def _extract_statement_type(parsed: Statement) -> str:
    """Return the first DML keyword (e.g. 'SELECT', 'INSERT')."""
    for token in parsed.tokens:
        if token.ttype in (DML, DDL, Keyword):
            return token.normalized.upper()
    return ""


def _extract_table_names(sql: str) -> set[str]:
    """Extract table names referenced in a SQL statement (best-effort)."""
    # Match after FROM, JOIN keywords
    pattern = re.compile(
        r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        re.IGNORECASE,
    )
    return {m.group(1).lower() for m in pattern.finditer(sql)}


def _extract_column_refs(sql: str) -> set[str]:
    """Extract actual column names from the SELECT clause, excluding aliases and table prefixes."""
    m = re.search(r'SELECT\s+(.+?)\s+FROM\b', sql, re.IGNORECASE | re.DOTALL)
    if not m:
        return set()
    select_part = m.group(1)

    # Drop AS aliases (e.g. "AS average_auto_claim_amount") before any other processing
    select_part = re.sub(r'\bAS\s+\w+', '', select_part, flags=re.IGNORECASE)

    cols: set[str] = set()

    # For table.column refs keep only the column part, discard the table prefix
    for match in re.finditer(r'\b\w+\.(\w+)\b', select_part):
        cols.add(match.group(1).lower())

    # Remove all table.column tokens so the table names aren't treated as bare identifiers
    bare_part = re.sub(r'\b\w+\.\w+\b', '', select_part)

    _SQL_KEYWORDS = {
        "DISTINCT", "AS", "CASE", "WHEN", "THEN", "ELSE", "END",
        "COUNT", "SUM", "AVG", "MIN", "MAX", "ROUND", "COALESCE",
        "NULLIF", "CAST", "STRFTIME", "DATE", "YEAR", "MONTH",
        "LENGTH", "TRIM", "LOWER", "UPPER", "SUBSTR", "REPLACE",
        "ABS", "IFNULL", "IIF", "TYPEOF",
    }
    for match in re.finditer(r'\b([a-zA-Z_]\w*)\b', bare_part):
        t = match.group(1)
        if t.upper() not in _SQL_KEYWORDS:
            cols.add(t.lower())

    return cols


def _all_known_columns() -> set[str]:
    cols: set[str] = set()
    for tbl_info in TABLE_SCHEMA.values():
        cols.update(tbl_info["columns"].keys())
    return cols


class ValidationAgent:
    """
    Validates a SQL query against a set of safety and correctness rules.
    Returns a ValidationResult indicating pass/fail and the reason.
    """

    def validate(self, sql: str) -> ValidationResult:
        if not sql or not sql.strip():
            return ValidationResult(False, "Empty query — nothing to execute.")

        sql_stripped = sql.strip().rstrip(";")

        # ── Rule 1: Must be a single statement ───────────────────────────────
        statements = [s for s in sqlparse.parse(sql_stripped) if s.get_type()]
        if len(statements) > 1:
            return ValidationResult(False, "Multiple SQL statements are not allowed.")

        parsed = sqlparse.parse(sql_stripped)[0]
        stmt_type = _extract_statement_type(parsed)

        # ── Rule 2: Must be SELECT ────────────────────────────────────────────
        if stmt_type != "SELECT":
            return ValidationResult(
                False,
                f"Only SELECT queries are permitted. Got: {stmt_type or 'unknown'}.",
            )

        # ── Rule 3: No blocked DML/DDL keywords anywhere in the text ─────────
        upper_sql = sql_stripped.upper()
        for kw in _BLOCKED_KEYWORDS:
            # Word-boundary check to avoid false positives (e.g. "SELECTED")
            if re.search(rf'\b{kw}\b', upper_sql):
                return ValidationResult(False, f"Forbidden keyword detected: {kw}.")

        # ── Rule 4: No dangerous functions ───────────────────────────────────
        lower_sql = sql_stripped.lower()
        for fn in _BLOCKED_FUNCTIONS:
            if fn in lower_sql:
                return ValidationResult(False, f"Forbidden function detected: {fn}.")

        # ── Rule 5: Only allowed tables ───────────────────────────────────────
        referenced_tables = _extract_table_names(sql_stripped)
        unknown_tables = referenced_tables - ALLOWED_TABLES
        if unknown_tables:
            return ValidationResult(
                False,
                f"Query references unauthorized table(s): {', '.join(sorted(unknown_tables))}. "
                f"Allowed tables: {', '.join(sorted(ALLOWED_TABLES))}.",
            )

        # ── Rule 6: Sanity-check column references ────────────────────────────
        known_cols = _all_known_columns()
        col_refs = _extract_column_refs(sql_stripped)
        # Filter out obvious aliases and numeric literals
        unknown_cols = {c for c in col_refs if c not in known_cols and not c.isdigit()}
        # Heuristic: if more than half the refs are unknown, flag it
        if unknown_cols and len(unknown_cols) > len(col_refs) / 2:
            return ValidationResult(
                False,
                f"Query may reference non-existent column(s): {', '.join(sorted(unknown_cols))}.",
            )

        # ── Rule 7: Complexity guard – no more than 5 JOINs ──────────────────
        join_count = len(re.findall(r'\bJOIN\b', upper_sql))
        if join_count > 5:
            return ValidationResult(
                False,
                f"Query is too complex ({join_count} JOINs). Maximum allowed is 5.",
            )

        return ValidationResult(True, "Query passed all safety checks.")
