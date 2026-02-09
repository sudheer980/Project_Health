# app/chat_store.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional
import time

Role = Literal["user", "assistant", "system"]

@dataclass
class ChatMessage:
    role: Role
    content: str
    ts: float

class ChatStore:
    """
    Simple in-memory conversation store.
    Good enough for take-home. (Optionally replace with Redis/SQLite later.)
    """
    def __init__(self):
        self._sessions: Dict[str, List[ChatMessage]] = {}

    def add(self, session_id: str, role: Role, content: str) -> None:
        self._sessions.setdefault(session_id, []).append(ChatMessage(role=role, content=content, ts=time.time()))

    def get(self, session_id: str) -> List[ChatMessage]:
        return self._sessions.get(session_id, [])

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def to_openai_style(self, session_id: str, max_messages: int = 12) -> List[dict]:
        """
        Return last N messages in a generic {role, content} format.
        """
        msgs = self.get(session_id)[-max_messages:]
        return [{"role": m.role, "content": m.content} for m in msgs]
