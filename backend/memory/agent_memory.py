from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryRecord:
    question: str
    sql: str
    row_count: int
    success: bool


class AgentMemory:
    """
    Lightweight in-process memory for the insurance agent.
    Stores conversation history and a rolling window of recent queries.
    """

    MAX_HISTORY = 20
    MAX_QUERIES = 10

    def __init__(self):
        self._history: list[dict[str, str]] = []
        self._recent_queries: deque[QueryRecord] = deque(maxlen=self.MAX_QUERIES)

    # ── Conversation history ──────────────────────────────────────────────────

    def add_user_message(self, content: str):
        self._history.append({"role": "user", "content": content})
        if len(self._history) > self.MAX_HISTORY:
            # Keep the first (system-context) message and trim the oldest pairs
            self._history = self._history[-self.MAX_HISTORY:]

    def add_assistant_message(self, content: str):
        self._history.append({"role": "assistant", "content": content})

    def get_history(self) -> list[dict[str, str]]:
        return list(self._history)

    def clear_history(self):
        self._history.clear()

    # ── Query cache ───────────────────────────────────────────────────────────

    def record_query(self, question: str, sql: str, row_count: int, success: bool):
        self._recent_queries.append(QueryRecord(question, sql, row_count, success))

    def get_recent_queries(self) -> list[QueryRecord]:
        return list(self._recent_queries)

    def recent_queries_text(self) -> str:
        if not self._recent_queries:
            return "No previous queries."
        lines = []
        for i, q in enumerate(self._recent_queries, 1):
            status = "OK" if q.success else "FAILED"
            lines.append(f"{i}. [{status}] Q: {q.question!r}\n   SQL: {q.sql}")
        return "\n".join(lines)
