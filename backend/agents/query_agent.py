"""
Query Generation Agent
Converts a natural-language insurance question into a SQLite SELECT statement.
Uses OpenAI via LangChain with a domain-specific system prompt.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from config import OPENAI_API_KEY, MODEL_NAME, MAX_TOKENS, DOMAIN_GLOSSARY
from tools.db_tools import get_schema_text


class SQLOutput(BaseModel):
    sql: str = Field(description="The SQLite SELECT query, no trailing semicolon")
    explanation: str = Field(description="Plain-English explanation of what the query does")
    confidence: str = Field(description="'high', 'medium', or 'low'")


SYSTEM_PROMPT = """You are an expert insurance data analyst and SQL engineer.
Your job is to convert natural-language business questions into correct SQLite SELECT queries
against the insurance database described below.

{schema}

{glossary}

RULES:
1. Only generate SELECT statements — never INSERT, UPDATE, DELETE, DROP, ALTER, or any DDL.
2. Only reference tables that exist in the schema above: customers, policies, claims.
3. Always use explicit column names (no SELECT *).
4. Use SQLite-compatible syntax: strftime('%Y', date_col) for year extraction, etc.
5. For monetary totals, ROUND to 2 decimal places.
6. If the question mentions "this quarter", use the current quarter of {current_year}.
7. If the question is ambiguous, make a reasonable interpretation and note it in explanation.
8. If you truly cannot answer with the available schema, set sql to empty string and explain why.

RECENT QUERIES FOR CONTEXT:
{recent_queries}

Respond ONLY with valid JSON matching this schema (no markdown, no extra text):
{{
  "sql": "<SELECT statement>",
  "explanation": "<what the query computes>",
  "confidence": "high|medium|low"
}}
"""


class QueryGenerationAgent:
    def __init__(self):
        self._llm = ChatOpenAI(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            openai_api_key=OPENAI_API_KEY,
        )
        self._schema_text = get_schema_text()

    def generate(self, question: str, recent_queries_text: str = "") -> SQLOutput:
        import datetime
        current_year = datetime.date.today().year

        system_content = SYSTEM_PROMPT.format(
            schema=self._schema_text,
            glossary=DOMAIN_GLOSSARY,
            recent_queries=recent_queries_text or "None yet.",
            current_year=current_year,
        )

        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=question),
        ]

        response = self._llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown code fences if the model wraps in them
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            data = json.loads(raw)
            return SQLOutput(
                sql=data.get("sql", "").strip().rstrip(";"),
                explanation=data.get("explanation", ""),
                confidence=data.get("confidence", "medium"),
            )
        except (json.JSONDecodeError, KeyError) as exc:
            # Attempt to extract SQL from raw text as last resort
            sql_match = re.search(r"(SELECT\b.+?)(?:\n\n|$)", raw, re.IGNORECASE | re.DOTALL)
            sql = sql_match.group(1).strip().rstrip(";") if sql_match else ""
            return SQLOutput(
                sql=sql,
                explanation=f"Extracted from raw response (parse error: {exc})",
                confidence="low",
            )
