import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.request import urlopen
from urllib.error import URLError

_DDL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    model TEXT,
    backend TEXT,
    agent_types TEXT,
    iterations INTEGER,
    corpus_hash TEXT,
    armor_version TEXT,
    results_file TEXT,
    wall_clock_seconds REAL,
    peak_vram_bytes INTEGER
);

CREATE TABLE IF NOT EXISTS run_attacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    attack_id TEXT,
    attack_name TEXT,
    agent_type TEXT,
    outcome TEXT,
    armor_active INTEGER,
    latency_ms REAL,
    verdict_reasoning TEXT
);
"""


class RunRecorder:
    def __init__(self, db_path: str = "runs.db") -> None:
        self._db_path = str(db_path)
        with self._connect() as conn:
            conn.executescript(_DDL)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def start_run(
        self,
        model: Optional[str],
        backend: Optional[str],
        agent_types: list[str],
        iterations: int,
        corpus_hash: Optional[str],
        armor_version: Optional[str],
        results_file: Optional[str],
    ) -> str:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO runs
                   (run_id, started_at, model, backend, agent_types, iterations,
                    corpus_hash, armor_version, results_file)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    run_id,
                    started_at,
                    model,
                    backend,
                    json.dumps(agent_types),
                    iterations,
                    corpus_hash,
                    armor_version,
                    results_file,
                ),
            )
        return run_id

    def finish_run(
        self,
        run_id: str,
        wall_clock_seconds: float,
        peak_vram_bytes: Optional[int] = None,
    ) -> None:
        finished_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """UPDATE runs
                   SET finished_at=?, wall_clock_seconds=?, peak_vram_bytes=?
                   WHERE run_id=?""",
                (finished_at, wall_clock_seconds, peak_vram_bytes, run_id),
            )

    def record_attack(
        self,
        run_id: str,
        attack_id: str,
        attack_name: str,
        agent_type: str,
        outcome: str,
        armor_active: bool,
        latency_ms: float,
        verdict_reasoning: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO run_attacks
                   (run_id, attack_id, attack_name, agent_type, outcome,
                    armor_active, latency_ms, verdict_reasoning)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    run_id,
                    attack_id,
                    attack_name,
                    agent_type,
                    outcome,
                    1 if armor_active else 0,
                    latency_ms,
                    verdict_reasoning,
                ),
            )

    @staticmethod
    def get_vram_bytes(model: Optional[str] = None) -> Optional[int]:
        try:
            with urlopen("http://localhost:11434/api/ps", timeout=2) as resp:
                data = json.loads(resp.read())
            models = data.get("models", [])
            if model is not None:
                models = [m for m in models if model in m.get("name", "")]
            total = sum(m.get("size_vram", 0) for m in models)
            return total if total > 0 else None
        except (URLError, OSError, ValueError, KeyError):
            return None
