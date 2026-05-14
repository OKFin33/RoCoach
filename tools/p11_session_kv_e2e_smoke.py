from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / "bin" / "python"
HOST = "127.0.0.1"
SECRET_MARKERS = (
    "p4b-secret-test-key",
    "ROCO_OPENAI_API_KEY",
    "X-Roco-Provider-Key",
    "https://provider.example/v1",
)


@dataclass(frozen=True)
class SmokeResult:
    session_id: str
    db_path: Path
    archive_path: Path
    assertions: list[str]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run P11 single-active-session KV E2E smoke.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--keep-temp", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="roco-p11-e2e-") as tmpdir:
        tmp_path = Path(tmpdir)
        result = run_smoke(tmp_path=tmp_path, port=args.port)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "session_id": result.session_id,
                    "db_path": str(result.db_path),
                    "archive_path": str(result.archive_path),
                    "assertions": result.assertions,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        if args.keep_temp:
            kept = ROOT / "artifacts" / "p11_session_kv_e2e_smoke"
            kept.mkdir(parents=True, exist_ok=True)
            (kept / "latest_result.json").write_text(
                json.dumps(
                    {
                        "db_path": str(result.db_path),
                        "archive_path": str(result.archive_path),
                        "assertions": result.assertions,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        return 0


def run_smoke(*, tmp_path: Path, port: int) -> SmokeResult:
    db_path = tmp_path / "session.sqlite3"
    archive_path = tmp_path / "session_archive.jsonl"
    env = {
        **os.environ,
        "ROCO_SESSION_DB_PATH": str(db_path),
        "ROCO_MANAGED_PERSONA_SCOPE": "internal_only_runtime",
        "ROCO_SESSION_NATIVE_HISTORY_MAX_BYTES": "1000000",
    }
    base_url = f"http://{HOST}:{port}"
    assertions: list[str] = []

    process = start_backend(port=port, env=env)
    try:
        client = httpx.Client(base_url=base_url, timeout=10.0, trust_env=False)
        health = client.get("/health")
        require(health.status_code == 200, "health endpoint is reachable")
        assertions.append("health endpoint reachable")

        first = client.post("/chat", json={"message": "/set-team 草 地 龙 翼 火 水"})
        require(first.status_code == 200, first.text)
        first_payload = first.json()
        session_id = first_payload["session_id"]
        require(session_id, "first response returns session_id")
        assertions.append("first chat returned authoritative session_id")

        second = client.post(
            "/chat",
            json={"session_id": session_id, "message": "分析这队联防"},
        )
        require(second.status_code == 200, second.text)
        require(second.json()["response"]["analysis_type"] == "team_analysis", second.text)
        assertions.append("active state supports follow-up team analysis before restart")
    finally:
        stop_backend(process)

    process = start_backend(port=port, env=env)
    try:
        client = httpx.Client(base_url=base_url, timeout=10.0, trust_env=False)
        restarted = client.post("/chat", json={"message": "分析这队联防"})
        require(restarted.status_code == 200, restarted.text)
        restarted_payload = restarted.json()
        require(restarted_payload["session_id"] == session_id, restarted.text)
        require(restarted_payload["response"]["analysis_type"] == "team_analysis", restarted.text)
        assertions.append("backend restart restored active SQLite session")

        stale = client.post(
            "/chat",
            json={"session_id": "stale-desktop-session", "message": "分析这队联防"},
        )
        require(stale.status_code == 200, stale.text)
        stale_payload = stale.json()
        require(stale_payload["session_id"] == session_id, stale.text)
        require(stale_payload["session_event"]["type"] == "reconciled", stale.text)
        require(
            stale_payload["session_event"]["diagnostic"]["visible_messages"] == "mark_stale",
            stale.text,
        )
        assertions.append("stale desktop session reconciled without forking active state")

        cleared = client.post("/session/clear", json={"reason": "e2e_clear"})
        require(cleared.status_code == 200, cleared.text)
        require(cleared.json()["session_event"]["type"] == "cleared", cleared.text)
        require(
            cleared.json()["session_event"]["diagnostic"]["visible_messages"] == "clear",
            cleared.text,
        )
        assertions.append("clear endpoint emitted controlled clear event")

        after_clear = client.post(
            "/chat",
            json={"session_id": session_id, "message": "分析这队联防"},
        )
        require(after_clear.status_code == 200, after_clear.text)
        require(after_clear.json()["response"]["analysis_type"] != "team_analysis", after_clear.text)
        assertions.append("clear reset active team state")
    finally:
        stop_backend(process)

    require(db_path.exists(), "SQLite session DB was created")
    require(archive_path.exists(), "JSONL archive was created")
    assert_no_secret_markers(db_path.read_bytes().decode("utf-8", errors="ignore"), "sqlite")
    assert_no_secret_markers(archive_path.read_text(encoding="utf-8"), "archive")
    require_archive_has_summary_only(archive_path)
    assertions.append("SQLite and archive contain no provider secret markers")
    assertions.append("archive is summary/diagnostic evidence")
    return SmokeResult(session_id=session_id, db_path=db_path, archive_path=archive_path, assertions=assertions)


def start_backend(*, port: int, env: dict[str, str]) -> subprocess.Popen[str]:
    process = subprocess.Popen(
        [
            str(PYTHON),
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            HOST,
            "--port",
            str(port),
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.monotonic() + 15.0
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            raise RuntimeError(f"backend exited early code={process.returncode}\n{output}")
        try:
            response = httpx.get(f"http://{HOST}:{port}/health", timeout=1.0, trust_env=False)
            if response.status_code == 200:
                return process
        except Exception as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"
        time.sleep(0.2)
    stop_backend(process)
    output = process.stdout.read() if process.stdout is not None else ""
    raise TimeoutError(f"backend did not become ready: {last_error}\n{output}")


def stop_backend(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5.0)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_secret_markers(text: str, label: str) -> None:
    for marker in SECRET_MARKERS:
        require(marker not in text, f"{label} contains secret marker: {marker}")


def require_archive_has_summary_only(path: Path) -> None:
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(lines, "archive should contain at least one record")
    for record in lines:
        require(record.get("summary") is not None, "archive record missing summary")
        require("messages" not in record, "archive must not contain full messages")
        require("native_model_messages" not in record, "archive must not contain native model messages")


if __name__ == "__main__":
    raise SystemExit(main())
