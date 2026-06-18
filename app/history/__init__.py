import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.utils.logger import setup_logger

logger = setup_logger("History")

class HistoryManager:
    def __init__(self, db_path: str = "data/history.db"):
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()
        logger.info(f"HistoryManager initialized: {db_path}")

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_request TEXT,
                plan TEXT,
                result TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                task TEXT,
                output TEXT,
                success BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        self._conn.commit()

    def create_session(self, session_id: str, user_request: str) -> None:
        self._conn.execute(
            "INSERT INTO sessions (session_id, user_request) VALUES (?, ?)",
            (session_id, user_request)
        )
        self._conn.commit()
        logger.info(f"Created session: {session_id}")

    def update_session(self, session_id: str, plan: str, result: str, status: str) -> None:
        self._conn.execute(
            "UPDATE sessions SET plan=?, result=?, status=? WHERE session_id=?",
            (plan, result, status, session_id)
        )
        self._conn.commit()
        logger.info(f"Updated session: {session_id}, status: {status}")

    def log_agent(self, session_id: str, agent_name: str, task: str, output: str, success: bool) -> None:
        self._conn.execute(
            "INSERT INTO agent_logs (session_id, agent_name, task, output, success) VALUES (?, ?, ?, ?, ?)",
            (session_id, agent_name, task, output, success)
        )
        self._conn.commit()

    def get_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM sessions WHERE session_id=?", (session_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_agent_logs(self, session_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.execute(
            "SELECT * FROM agent_logs WHERE session_id=? ORDER BY created_at", (session_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        self._conn.close()
