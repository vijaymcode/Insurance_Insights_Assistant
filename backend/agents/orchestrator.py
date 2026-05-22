"""
Insurance Agent Orchestrator
Coordinates the query generation agent → validation agent → execution pipeline.
Also handles conversational (non-data) questions using the LLM directly.
Uses OpenAI via LangChain.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from agents.query_agent import QueryGenerationAgent, SQLOutput
from agents.validation_agent import ValidationAgent
from config import OPENAI_API_KEY, MODEL_NAME, MAX_TOKENS, DOMAIN_GLOSSARY
from memory.agent_memory import AgentMemory
from tools.db_tools import execute_query, get_schema_text, get_schema_dict


@dataclass
class AgentResponse:
    answer: str
    sql: Optional[str]
    explanation: Optional[str]
    columns: list[str]
    rows: list[dict]
    row_count: int
    error: Optional[str]
    confidence: str


_CONVERSATIONAL_SYSTEM = """You are a helpful insurance data analyst assistant.
Answer concisely in plain English. If the user asks a data question you cannot answer without
running a query (and no query was produced), tell them to rephrase as a data question.

Insurance domain glossary:
{glossary}
"""

_DATA_QUESTION_PATTERN = re.compile(
    r'\b('
    # interrogatives & imperatives
    r'how many|how much|what|which|who|show|list|give me|find|get|calculate|compute|'
    # aggregations
    r'total|average|avg|sum|count|percentage|percent|ratio|rate|distribution|breakdown|'
    # comparison / ranking
    r'top|bottom|highest|lowest|most|least|best|worst|compare|versus|vs|'
    # domain nouns — plurals handled by s? where needed
    r'claims?|polic(?:y|ies)|customers?|premium|region|state|'
    # insurance-specific
    r'loss ratio|risk|coverage|settlement|settled|denied|approved|pending|active|expired|cancelled'
    r')\b',
    re.IGNORECASE,
)


def _looks_like_data_question(text: str) -> bool:
    # Any message with a domain keyword OR ending with "?" is treated as a data question.
    return bool(_DATA_QUESTION_PATTERN.search(text)) or text.strip().endswith('?')


class InsuranceOrchestrator:
    def __init__(self):
        self._memory = AgentMemory()
        self._query_agent = QueryGenerationAgent()
        self._validation_agent = ValidationAgent()
        self._llm = ChatOpenAI(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            openai_api_key=OPENAI_API_KEY,
        )
        self._schema_text = get_schema_text()

    # ── Public API ────────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> AgentResponse:
        """
        Main entry point. Routes between data queries and conversational replies.
        """
        self._memory.add_user_message(user_message)

        if _looks_like_data_question(user_message):
            response = self._handle_data_question(user_message)
        else:
            response = self._handle_conversational(user_message)

        # Store assistant turn in memory
        summary = response.answer[:300] + ("…" if len(response.answer) > 300 else "")
        self._memory.add_assistant_message(summary)
        return response

    def get_schema(self) -> dict:
        return get_schema_dict()

    def reset(self):
        self._memory.clear_history()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _handle_data_question(self, question: str) -> AgentResponse:
        recent = self._memory.recent_queries_text()

        # Step 1 – Generate SQL
        sql_out: SQLOutput = self._query_agent.generate(question, recent)

        if not sql_out.sql:
            return AgentResponse(
                answer=f"I wasn't able to generate a query for that question. {sql_out.explanation}",
                sql=None, explanation=sql_out.explanation,
                columns=[], rows=[], row_count=0, error=None,
                confidence=sql_out.confidence,
            )

        # Step 2 – Validate SQL
        validation = self._validation_agent.validate(sql_out.sql)
        if not validation.valid:
            return AgentResponse(
                answer=f"The generated query failed safety checks: {validation.reason}",
                sql=sql_out.sql, explanation=sql_out.explanation,
                columns=[], rows=[], row_count=0,
                error=validation.reason,
                confidence="low",
            )

        # Step 3 – Execute
        result = execute_query(sql_out.sql)
        if "error" in result:
            self._memory.record_query(question, sql_out.sql, 0, success=False)
            return AgentResponse(
                answer=f"Query execution failed: {result['error']}",
                sql=sql_out.sql, explanation=sql_out.explanation,
                columns=[], rows=[], row_count=0,
                error=result["error"],
                confidence=sql_out.confidence,
            )

        self._memory.record_query(
            question, sql_out.sql, result["row_count"], success=True
        )

        # Step 4 – Synthesise a natural-language answer
        answer = self._synthesise_answer(question, sql_out, result)

        return AgentResponse(
            answer=answer,
            sql=sql_out.sql,
            explanation=sql_out.explanation,
            columns=result["columns"],
            rows=result["rows"],
            row_count=result["row_count"],
            error=None,
            confidence=sql_out.confidence,
        )

    def _handle_conversational(self, message: str) -> AgentResponse:
        messages = [
            SystemMessage(
                content=_CONVERSATIONAL_SYSTEM.format(glossary=DOMAIN_GLOSSARY)
            ),
            *[
                HumanMessage(content=m["content"]) if m["role"] == "user"
                else SystemMessage(content=m["content"])
                for m in self._memory.get_history()[:-1]  # exclude the just-added message
            ],
            HumanMessage(content=message),
        ]
        response = self._llm.invoke(messages)
        return AgentResponse(
            answer=response.content,
            sql=None, explanation=None,
            columns=[], rows=[], row_count=0, error=None,
            confidence="high",
        )

    def _synthesise_answer(
        self,
        question: str,
        sql_out: SQLOutput,
        result: dict[str, Any],
    ) -> str:
        rows = result["rows"]
        row_count = result["row_count"]
        truncated = result.get("truncated", False)

        if row_count == 0:
            return "The query returned no results for your question."

        # Build a brief textual summary using the LLM
        preview_rows = rows[:10]
        preview_text = json.dumps(preview_rows, default=str, indent=2)

        prompt = f"""The user asked: "{question}"

We ran this SQL:
{sql_out.sql}

The query returned {row_count} row(s){' (truncated to 500)' if truncated else ''}.
Here are the first rows:
{preview_text}

Write a concise, insightful 2-4 sentence summary of the results in plain English.
Use insurance business language where appropriate. Do not repeat the SQL."""

        messages = [
            SystemMessage(content="You are a senior insurance analyst summarizing query results."),
            HumanMessage(content=prompt),
        ]
        response = self._llm.invoke(messages)
        return response.content.strip()
