from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Literal
from uuid import uuid4

from advisor.contracts import AdvisorSessionState

try:
    from pydantic_ai.messages import ModelMessagesTypeAdapter
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    ModelMessagesTypeAdapter = None


SESSION_DB_PATH_ENV = "ROCO_SESSION_DB_PATH"
SESSION_APP_DATA_DIR_ENV = "ROCO_DESKTOP_APP_DATA_DIR"
SESSION_DEV_FALLBACK_ENV = "ROCO_SESSION_ALLOW_IN_MEMORY_FALLBACK"
SESSION_NATIVE_HISTORY_MAX_BYTES_ENV = "ROCO_SESSION_NATIVE_HISTORY_MAX_BYTES"
SESSION_NATIVE_HISTORY_MAX_MESSAGES_ENV = "ROCO_SESSION_NATIVE_HISTORY_MAX_MESSAGES"
SESSION_STATE_SCHEMA_VERSION = "roco_session_state.v2"
NATIVE_MESSAGES_SCHEMA_VERSION = "pydantic_ai_model_messages.v1"
DEFAULT_NATIVE_HISTORY_MAX_BYTES = 512_000
DEFAULT_NATIVE_HISTORY_MAX_MESSAGES = 64


class SessionStoreError(RuntimeError):
    pass


class SessionArchiveError(SessionStoreError):
    pass


@dataclass(frozen=True)
class SessionEvent:
    type: Literal["started", "continued", "reconciled", "cleared", "rolled_over"]
    reason: str
    message: str
    user_action: str | None
    diagnostic: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "reason": self.reason,
            "message": self.message,
            "user_action": self.user_action,
            "diagnostic": self.diagnostic,
        }


@dataclass(frozen=True)
class SessionResolution:
    session_id: str
    store: "SQLiteSessionStateStore | InMemoryFallbackActiveSessionStore"
    event: SessionEvent


def resolve_session_db_path(root: Path | None = None) -> Path:
    env_path = os.getenv(SESSION_DB_PATH_ENV)
    if env_path and env_path.strip():
        return Path(env_path).expanduser()

    app_data_dir = os.getenv(SESSION_APP_DATA_DIR_ENV)
    if app_data_dir and app_data_dir.strip():
        return Path(app_data_dir).expanduser() / "roco_session" / "session.sqlite3"

    base = root or Path.cwd()
    return base / ".runtime" / "roco_session" / "session.sqlite3"


def allow_in_memory_session_fallback() -> bool:
    return os.getenv(SESSION_DEV_FALLBACK_ENV, "").strip() == "1"


class ActiveSessionStore:
    def __init__(
        self,
        db_path: Path,
        *,
        archive_path: Path | None = None,
        allow_in_memory_fallback: bool = False,
    ) -> None:
        self.db_path = db_path
        self.archive_path = archive_path or db_path.with_name("session_archive.jsonl")
        self._lock = RLock()
        self._fallback: InMemoryFallbackActiveSessionStore | None = None
        try:
            self._initialize()
        except Exception as exc:
            if allow_in_memory_fallback:
                self._fallback = InMemoryFallbackActiveSessionStore()
                return
            raise SessionStoreError("session_sqlite_unavailable") from exc

    @property
    def using_in_memory_fallback(self) -> bool:
        return self._fallback is not None

    def resolve(self, requested_session_id: str | None) -> SessionResolution:
        if self._fallback is not None:
            return self._fallback.resolve(requested_session_id)

        with self._lock:
            active_session_id = self._active_session_id()
            if active_session_id is None:
                session_id = _safe_session_id(requested_session_id) or uuid4().hex
                self._set_active_session_id(session_id)
                self._ensure_state_row(session_id)
                return SessionResolution(
                    session_id=session_id,
                    store=SQLiteSessionStateStore(self, session_id),
                    event=_session_event(
                        "started",
                        reason="active_session_created",
                        agent_context="available",
                        visible_messages="unchanged",
                        archive="not_applicable",
                    ),
                )

            if requested_session_id and requested_session_id != active_session_id:
                self._ensure_state_row(active_session_id)
                recovery_event = self._recover_state_if_invalid(active_session_id)
                if recovery_event is not None:
                    return SessionResolution(
                        session_id=active_session_id,
                        store=SQLiteSessionStateStore(self, active_session_id),
                        event=recovery_event,
                    )
                return SessionResolution(
                    session_id=active_session_id,
                    store=SQLiteSessionStateStore(self, active_session_id),
                    event=_session_event(
                        "reconciled",
                        reason="client_session_mismatch",
                        message="已继续当前本地会话。",
                        agent_context="available",
                        visible_messages="mark_stale",
                        archive="not_applicable",
                    ),
                )

            self._ensure_state_row(active_session_id)
            recovery_event = self._recover_state_if_invalid(active_session_id)
            if recovery_event is not None:
                return SessionResolution(
                    session_id=active_session_id,
                    store=SQLiteSessionStateStore(self, active_session_id),
                    event=recovery_event,
                )
            return SessionResolution(
                session_id=active_session_id,
                store=SQLiteSessionStateStore(self, active_session_id),
                event=_session_event(
                    "continued",
                    reason="active_session_continued",
                    agent_context="available",
                    visible_messages="unchanged",
                    archive="not_applicable",
                ),
            )

    def clear_active(self, *, reason: str = "user_clear") -> tuple[str, SessionEvent]:
        if self._fallback is not None:
            return self._fallback.clear_active(reason=reason)

        with self._lock:
            session_id = self._active_session_id()
            if session_id is None:
                session_id = uuid4().hex
                self._set_active_session_id(session_id)
            previous = self._load_state(session_id)
            self._write_archive_record(
                session_id=session_id,
                reason=reason,
                state=previous,
            )
            self._save_state(session_id, AdvisorSessionState())
            return (
                session_id,
                _session_event(
                    "cleared",
                    reason=reason,
                    message="已清空当前会话状态。",
                    user_action="可以继续新的提问。",
                    agent_context="reset",
                    visible_messages="clear",
                    archive="written",
                ),
            )

    def validate_native_history(
        self,
        *,
        session_id: str,
        expected_fingerprint: str | None,
    ) -> SessionEvent | None:
        if self._fallback is not None:
            return None
        if expected_fingerprint is None:
            return None

        with self._lock:
            row = self._native_history_row(session_id)
            if row is None:
                return None
            native_messages_json, native_runtime_fingerprint, messages_schema_version = row
            if not native_messages_json:
                return None
            if ModelMessagesTypeAdapter is None:
                self._drop_native_history(session_id)
                return _native_history_drop_event("native_history_adapter_unavailable")
            if messages_schema_version != NATIVE_MESSAGES_SCHEMA_VERSION:
                self._drop_native_history(session_id)
                return _native_history_drop_event("native_history_schema_mismatch")
            if native_runtime_fingerprint != expected_fingerprint:
                self._drop_native_history(session_id)
                return _native_history_drop_event("native_runtime_fingerprint_mismatch")
            try:
                ModelMessagesTypeAdapter.validate_json(native_messages_json)
            except Exception:
                self._drop_native_history(session_id)
                return _native_history_drop_event("native_history_deserialize_failed")
        return None

    def maybe_rollover_for_context_pressure(self, *, session_id: str) -> SessionResolution | None:
        if self._fallback is not None:
            return None
        with self._lock:
            state = self._load_state(session_id)
            native_messages_json = self._native_messages_json(session_id)
            native_message_count = len(state.native_model_messages)
            native_history_bytes = len(native_messages_json.encode("utf-8")) if native_messages_json else 0
            max_bytes = _env_int(SESSION_NATIVE_HISTORY_MAX_BYTES_ENV, DEFAULT_NATIVE_HISTORY_MAX_BYTES)
            max_messages = _env_int(
                SESSION_NATIVE_HISTORY_MAX_MESSAGES_ENV,
                DEFAULT_NATIVE_HISTORY_MAX_MESSAGES,
            )
            if native_message_count <= max_messages and native_history_bytes <= max_bytes:
                return None
            self._write_archive_record(
                session_id=session_id,
                reason="context_pressure_rollover",
                state=state,
            )
            new_session_id = uuid4().hex
            self._set_active_session_id(new_session_id)
            self._save_state(new_session_id, AdvisorSessionState())
            return SessionResolution(
                session_id=new_session_id,
                store=SQLiteSessionStateStore(self, new_session_id),
                event=_session_event(
                    "rolled_over",
                    reason="context_pressure_rollover",
                    message="已开始新的本地会话。",
                    user_action="上一段对话已归档，可以继续新的提问。",
                    agent_context="reset",
                    visible_messages="clear",
                    archive="written",
                ),
            )

    def _initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS session_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS session_state (
                    session_id TEXT PRIMARY KEY,
                    state_schema_version TEXT NOT NULL DEFAULT 'roco_session_state.v2',
                    state_json TEXT NOT NULL,
                    native_messages_json TEXT,
                    native_messages_schema_version TEXT,
                    native_runtime_fingerprint TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            _ensure_column(connection, "session_state", "state_schema_version", "TEXT")
            _ensure_column(connection, "session_state", "native_messages_schema_version", "TEXT")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    @contextmanager
    def _connection(self):
        with closing(self._connect()) as connection:
            with connection:
                yield connection

    def _active_session_id(self) -> str | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value FROM session_meta WHERE key = 'active_session_id'"
            ).fetchone()
        return None if row is None else str(row[0])

    def _set_active_session_id(self, session_id: str) -> None:
        now = _now()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO session_meta(key, value)
                VALUES('active_session_id', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (session_id,),
            )
            connection.execute(
                """
                INSERT INTO session_meta(key, value)
                VALUES('active_session_updated_at', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (now,),
            )

    def _ensure_state_row(self, session_id: str) -> None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM session_state WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            self._save_state(session_id, AdvisorSessionState())

    def _recover_state_if_invalid(self, session_id: str) -> SessionEvent | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT state_json FROM session_state WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        try:
            AdvisorSessionState.model_validate(json.loads(str(row[0])))
        except Exception:
            self._save_state(session_id, AdvisorSessionState())
            return _state_drop_event("session_state_deserialize_failed")
        return None

    def _load_state(self, session_id: str) -> AdvisorSessionState:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT state_json, native_messages_json, native_runtime_fingerprint
                FROM session_state WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return AdvisorSessionState()
        try:
            state_payload = json.loads(str(row[0]))
            state = AdvisorSessionState.model_validate(state_payload)
        except Exception:
            self._save_state(session_id, AdvisorSessionState())
            return AdvisorSessionState()
        native_messages_json = row[1]
        if native_messages_json and ModelMessagesTypeAdapter is not None:
            try:
                state.native_model_messages = list(
                    ModelMessagesTypeAdapter.validate_json(native_messages_json)
                )
                state.native_runtime_fingerprint = str(row[2]) if row[2] else None
            except Exception:
                state.native_model_messages = []
                state.native_runtime_fingerprint = None
        return state

    def _save_state(self, session_id: str, state: AdvisorSessionState) -> None:
        now = _now()
        state_payload = state.model_dump(
            mode="json",
            exclude={"native_model_messages", "native_runtime_fingerprint"},
        )
        native_messages_json = _serialize_native_messages(state.native_model_messages)
        native_runtime_fingerprint = (
            state.native_runtime_fingerprint if native_messages_json is not None else None
        )
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO session_state(
                    session_id,
                    state_schema_version,
                    state_json,
                    native_messages_json,
                    native_messages_schema_version,
                    native_runtime_fingerprint,
                    created_at,
                    updated_at
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    state_schema_version = excluded.state_schema_version,
                    state_json = excluded.state_json,
                    native_messages_json = excluded.native_messages_json,
                    native_messages_schema_version = excluded.native_messages_schema_version,
                    native_runtime_fingerprint = excluded.native_runtime_fingerprint,
                    updated_at = excluded.updated_at
                """,
                (
                    session_id,
                    SESSION_STATE_SCHEMA_VERSION,
                    json.dumps(state_payload, ensure_ascii=False, sort_keys=True),
                    native_messages_json,
                    NATIVE_MESSAGES_SCHEMA_VERSION if native_messages_json is not None else None,
                    native_runtime_fingerprint,
                    now,
                    now,
                ),
            )

    def _write_archive_record(
        self,
        *,
        session_id: str,
        reason: str,
        state: AdvisorSessionState,
    ) -> None:
        record = {
            "schema_version": "roco_session_archive.v1",
            "event": "active_session_archived",
            "transition": ["archive_pending", "archive_written", "active_replaced"],
            "created_at": _now(),
            "session_id": session_id,
            "reason": reason,
            "summary": {
                "team_slots": len(state.current_team),
                "has_species_context": state.current_species_context is not None,
                "user_constraints_count": len(state.user_constraints),
                "last_analysis_type": state.last_analysis_type,
                "pending_followup_targets_count": len(state.pending_followup_targets),
                "recent_turn_summaries_count": len(state.recent_turn_summaries),
                "topic_pool_species_count": len(state.conversation_topic_pool.species),
                "topic_pool_relations_count": len(state.conversation_topic_pool.relations),
                "native_message_count": len(state.native_model_messages),
                "has_native_runtime_fingerprint": state.native_runtime_fingerprint is not None,
            },
            "diagnostic": {
                "agent_context": "archived_before_reset",
                "archive": "summary_only",
                "visible_messages": "frontend_owned",
            },
        }
        try:
            self.archive_path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=str(self.archive_path.parent),
                delete=False,
            ) as tmp:
                tmp.write(line)
                temp_path = Path(tmp.name)
            with self.archive_path.open("a", encoding="utf-8") as archive:
                archive.write(temp_path.read_text(encoding="utf-8"))
            temp_path.unlink(missing_ok=True)
        except Exception as exc:
            raise SessionArchiveError("session_archive_write_failed") from exc

    def _native_history_row(self, session_id: str) -> tuple[str | None, str | None, str | None] | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT native_messages_json, native_runtime_fingerprint, native_messages_schema_version
                FROM session_state WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return (
            str(row[0]) if row[0] is not None else None,
            str(row[1]) if row[1] is not None else None,
            str(row[2]) if row[2] is not None else None,
        )

    def _native_messages_json(self, session_id: str) -> str | None:
        row = self._native_history_row(session_id)
        return None if row is None else row[0]

    def _drop_native_history(self, session_id: str) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE session_state
                SET native_messages_json = NULL,
                    native_messages_schema_version = NULL,
                    native_runtime_fingerprint = NULL,
                    updated_at = ?
                WHERE session_id = ?
                """,
                (_now(), session_id),
            )


class SQLiteSessionStateStore:
    def __init__(self, active_store: ActiveSessionStore, session_id: str) -> None:
        self._active_store = active_store
        self._session_id = session_id

    def get(self) -> AdvisorSessionState:
        with self._active_store._lock:
            return self._active_store._load_state(self._session_id).model_copy(deep=True)

    def set(self, state: AdvisorSessionState) -> None:
        with self._active_store._lock:
            self._active_store._save_state(self._session_id, state.model_copy(deep=True))

    def clear(self) -> AdvisorSessionState:
        self._active_store.clear_active(reason="chat_command_clear")
        return self.get()


class InMemoryFallbackActiveSessionStore:
    def __init__(self) -> None:
        from advisor.runtime import InMemorySessionStateStore

        self._session_id: str | None = None
        self._store = InMemorySessionStateStore()

    def resolve(self, requested_session_id: str | None) -> SessionResolution:
        if self._session_id is None:
            self._session_id = _safe_session_id(requested_session_id) or uuid4().hex
            event = _session_event(
                "started",
                reason="dev_in_memory_active_session_created",
                agent_context="available",
                visible_messages="unchanged",
                archive="disabled",
            )
        elif requested_session_id and requested_session_id != self._session_id:
            event = _session_event(
                "reconciled",
                reason="client_session_mismatch_dev_in_memory",
                message="已继续当前本地会话。",
                agent_context="available",
                visible_messages="mark_stale",
                archive="disabled",
            )
        else:
            event = _session_event(
                "continued",
                reason="dev_in_memory_active_session_continued",
                agent_context="available",
                visible_messages="unchanged",
                archive="disabled",
            )
        return SessionResolution(session_id=self._session_id, store=self._store, event=event)

    def clear_active(self, *, reason: str = "user_clear") -> tuple[str, SessionEvent]:
        if self._session_id is None:
            self._session_id = uuid4().hex
        self._store.clear()
        return (
            self._session_id,
            _session_event(
                "cleared",
                reason=reason,
                message="已清空当前会话状态。",
                user_action="可以继续新的提问。",
                agent_context="reset",
                visible_messages="clear",
                archive="disabled",
            ),
        )


def _serialize_native_messages(messages: list[Any]) -> str | None:
    if not messages or ModelMessagesTypeAdapter is None:
        return None
    try:
        payload = ModelMessagesTypeAdapter.dump_json(messages)
    except Exception:
        return None
    return payload.decode("utf-8") if isinstance(payload, bytes) else str(payload)


def _safe_session_id(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _session_event(
    event_type: Literal["started", "continued", "reconciled", "cleared", "rolled_over"],
    *,
    reason: str,
    agent_context: str,
    visible_messages: str,
    archive: str,
    message: str = "已继续当前本地会话。",
    user_action: str | None = None,
) -> SessionEvent:
    return SessionEvent(
        type=event_type,
        reason=reason,
        message=message,
        user_action=user_action,
        diagnostic={
            "agent_context": agent_context,
            "visible_messages": visible_messages,
            "archive": archive,
            "support_code": reason,
        },
    )


def _native_history_drop_event(reason: str) -> SessionEvent:
    return _session_event(
        "reconciled",
        reason=reason,
        message="已继续当前本地会话。",
        user_action="上一段模型上下文已失效，旧消息仅作为历史记录显示。",
        agent_context="native_history_dropped",
        visible_messages="mark_stale",
        archive="not_applicable",
    )


def _state_drop_event(reason: str) -> SessionEvent:
    return _session_event(
        "reconciled",
        reason=reason,
        message="已继续当前本地会话。",
        user_action="上一段本地连续性状态已失效，旧消息仅作为历史记录显示。",
        agent_context="active_state_dropped",
        visible_messages="mark_stale",
        archive="not_applicable",
    )


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, declaration: str) -> None:
    existing = {
        str(row[1])
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column in existing:
        return
    connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return max(1, int(raw_value))
    except ValueError:
        return default


def _now() -> str:
    return datetime.now(UTC).isoformat()
