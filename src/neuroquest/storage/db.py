"""Run log and decision store in `var/neuroquest.sqlite3`. Decisions are append-only.

Raw prompts are not stored; validated handoffs are.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from neuroquest.errors import UnknownRecordError
from neuroquest.models.records import CandidateId
from neuroquest.models.runs import HumanDecision, RunRecord, RunStatus, Usage

MIGRATIONS: tuple[tuple[int, str], ...] = (
    (
        1,
        """
    CREATE TABLE runs (
        run_id TEXT PRIMARY KEY,
        question TEXT NOT NULL,
        candidate_ids TEXT NOT NULL,
        status TEXT NOT NULL,
        prompt_version TEXT,
        input_tokens INTEGER NOT NULL DEFAULT 0,
        cached_tokens INTEGER NOT NULL DEFAULT 0,
        output_tokens INTEGER NOT NULL DEFAULT 0,
        cost_usd REAL NOT NULL DEFAULT 0,
        budget_usd REAL NOT NULL,
        packet_markdown TEXT,
        created_at TEXT NOT NULL,
        closed_at TEXT
    );
    CREATE TABLE steps (
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        seq INTEGER NOT NULL,
        node TEXT NOT NULL,
        model TEXT,
        input_tokens INTEGER NOT NULL DEFAULT 0,
        cached_tokens INTEGER NOT NULL DEFAULT 0,
        output_tokens INTEGER NOT NULL DEFAULT 0,
        cost_usd REAL NOT NULL DEFAULT 0,
        handoff TEXT,
        error TEXT,
        recorded_at TEXT NOT NULL,
        PRIMARY KEY (run_id, seq)
    );
    CREATE TABLE decisions (
        decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        candidate_id TEXT NOT NULL,
        disposition TEXT NOT NULL,
        actor TEXT NOT NULL,
        reason TEXT NOT NULL,
        packet_sha256 TEXT NOT NULL,
        decided_at TEXT NOT NULL
    );
    CREATE TRIGGER decisions_append_only BEFORE UPDATE ON decisions
    BEGIN SELECT RAISE(ABORT, 'decisions are append-only'); END;
    CREATE TRIGGER decisions_no_delete BEFORE DELETE ON decisions
    BEGIN SELECT RAISE(ABORT, 'decisions are append-only'); END;
    """,
    ),
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._db = sqlite3.connect(path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def close(self) -> None:
        self._db.close()

    def _migrate(self) -> None:
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        applied = {row[0] for row in self._db.execute("SELECT version FROM schema_migrations")}
        for version, sql in MIGRATIONS:
            if version not in applied:
                with self._db:
                    self._db.executescript(sql)
                    self._db.execute("INSERT INTO schema_migrations VALUES (?, ?)", (version, _now()))

    def create_run(self, run_id: str, question: str, candidate_ids: list[CandidateId], budget_usd: float) -> None:
        with self._db:
            self._db.execute(
                "INSERT INTO runs (run_id, question, candidate_ids, status, budget_usd, created_at) "
                "VALUES (?, ?, ?, 'running', ?, ?)",
                (run_id, question, json.dumps(candidate_ids), budget_usd, _now()),
            )

    def add_step(
        self,
        run_id: str,
        node: str,
        model: str | None,
        usage: Usage,
        cost_usd: float,
        handoff: str | None = None,
        error: str | None = None,
    ) -> None:
        with self._db:
            seq = self._db.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM steps WHERE run_id = ?", (run_id,)
            ).fetchone()[0]
            self._db.execute(
                "INSERT INTO steps VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    seq,
                    node,
                    model,
                    usage.input_tokens,
                    usage.cached_tokens,
                    usage.output_tokens,
                    cost_usd,
                    handoff,
                    error,
                    _now(),
                ),
            )

    def finish_run(
        self,
        run_id: str,
        status: RunStatus,
        packet_markdown: str | None,
        prompt_version: str | None,
        usage: Usage,
        cost_usd: float,
    ) -> None:
        closed = _now() if status in {"closed", "partial", "invalid_input", "failed"} else None
        with self._db:
            self._db.execute(
                "UPDATE runs SET status = ?, packet_markdown = COALESCE(?, packet_markdown), "
                "prompt_version = COALESCE(?, prompt_version), input_tokens = ?, cached_tokens = ?, "
                "output_tokens = ?, cost_usd = ?, closed_at = ? WHERE run_id = ?",
                (
                    status,
                    packet_markdown,
                    prompt_version,
                    usage.input_tokens,
                    usage.cached_tokens,
                    usage.output_tokens,
                    cost_usd,
                    closed,
                    run_id,
                ),
            )

    def add_decision(self, run_id: str, decision: HumanDecision, packet_sha256: str) -> None:
        with self._db:
            self._db.execute(
                "INSERT INTO decisions (run_id, candidate_id, disposition, actor, reason, packet_sha256, "
                "decided_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    decision.candidate_id,
                    decision.disposition,
                    decision.actor,
                    decision.reason,
                    packet_sha256,
                    decision.decided_at.isoformat(),
                ),
            )

    def get_run(self, run_id: str) -> RunRecord:
        row = self._db.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise UnknownRecordError(f"Unknown run {run_id!r}")
        return self._to_run(row)

    def list_runs(self, status: RunStatus | None = None, limit: int = 20) -> list[RunRecord]:
        query, args = "SELECT * FROM runs", []
        if status:
            query, args = query + " WHERE status = ?", [status]
        rows = self._db.execute(query + " ORDER BY created_at DESC LIMIT ?", [*args, limit]).fetchall()
        return [self._to_run(row) for row in rows]

    def decisions_for(self, run_id: str) -> list[HumanDecision]:
        rows = self._db.execute("SELECT * FROM decisions WHERE run_id = ? ORDER BY decision_id", (run_id,)).fetchall()
        return [
            HumanDecision(
                candidate_id=CandidateId(r["candidate_id"]),
                disposition=r["disposition"],
                actor=r["actor"],
                reason=r["reason"],
                decided_at=datetime.fromisoformat(r["decided_at"]),
            )
            for r in rows
        ]

    @staticmethod
    def _to_run(row: sqlite3.Row) -> RunRecord:
        return RunRecord(
            run_id=row["run_id"],
            question=row["question"],
            candidate_ids=[CandidateId(c) for c in json.loads(row["candidate_ids"])],
            status=row["status"],
            prompt_version=row["prompt_version"],
            usage=Usage(
                input_tokens=row["input_tokens"], cached_tokens=row["cached_tokens"], output_tokens=row["output_tokens"]
            ),
            cost_usd=row["cost_usd"],
            budget_usd=row["budget_usd"],
            packet_markdown=row["packet_markdown"],
            created_at=datetime.fromisoformat(row["created_at"]),
            closed_at=datetime.fromisoformat(row["closed_at"]) if row["closed_at"] else None,
        )
