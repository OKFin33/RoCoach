from __future__ import annotations

import argparse
import json
import tempfile
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from advisor.battle_dex import BattleDexRepository
from advisor.contracts import AdvisorResponse
from advisor.config import RocoNativeModelConfig
from api.main import create_app
from api.runtime_headers import (
    HEADER_MODEL,
    HEADER_PROVIDER_BASE_URL,
    HEADER_PROVIDER_KEY,
    HEADER_RUNTIME_MODE,
)
from api.services.advisor_service import AdvisorService
from tools.import_battle_dex_sqlite import write_sqlite


IMPORTER_RUN_DIR = ROOT / "data" / "importer_runs" / "2026-04-14Tpolicy_b_importer_dry_run"
SCHEMA_PATH = ROOT / "specs" / "battle_dex_sqlite_schema_v1.sql"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run P12 Agent continuity E2E smoke.")
    parser.add_argument("--keep-temp", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="roco-p12-e2e-") as tmpdir:
        tmp_path = Path(tmpdir)
        battle_dex_path = tmp_path / "battle_dex.sqlite"
        _write_battle_dex(battle_dex_path)
        result = run_smoke(tmp_path=tmp_path, battle_dex_path=battle_dex_path)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        if args.keep_temp:
            out_dir = ROOT / "artifacts" / "p12_agent_continuity_e2e_smoke"
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "latest_result.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        return 0


def run_smoke(*, tmp_path: Path, battle_dex_path: Path) -> dict[str, Any]:
    db_path = tmp_path / "session.sqlite3"
    assertions: list[str] = []

    service = _service(db_path, battle_dex_path=battle_dex_path)
    client = TestClient(create_app(advisor_service=service))
    with patch("advisor.runtime._build_native_agent", return_value=_FakeP12Agent()):
        first = _post_chat(client, "你好")
        session_id = first["session_id"]
        assertions.append("native greeting returns authoritative active session")

        black_cat = _post_chat(client, "为什么黑猫经常用来首发", session_id=session_id)
        require(black_cat["response"]["runtime_path"] == "native_llm_terminal", black_cat)
        require("tool_results" not in black_cat["response"]["answer"], black_cat)
        assertions.append("ambiguous black-cat lead question enters native Agent path without exposing internals")

        named = _post_chat(client, "黑猫巫师", session_id=session_id)
        require(named["response"]["runtime_path"] == "native_llm_terminal", named)
        require("黑猫巫师" in named["response"]["answer"], named)
        assertions.append("explicit species anchor is grounded")

        relation = _post_chat(client, "配合恶魔狼主C", session_id=session_id)
        require(relation["response"]["runtime_path"] == "native_llm_terminal", relation)
        require("黑猫巫师" in relation["response"]["answer"], relation)
        require("恶魔狼" in relation["response"]["answer"], relation)
        require("tool_results" not in relation["response"]["answer"], relation)
        require("runtime_path" not in relation["response"]["answer"], relation)
        assertions.append("relation follow-up preserves active focus without exposing internals")

    stored = service.session_store.resolve(session_id).store.get()
    require(stored.conversation_topic_pool.active_focus.focus_type == "relation", stored.model_dump())
    require(len(stored.conversation_topic_pool.active_focus.subject_species_ids) == 2, stored.model_dump())
    require(all(not summary.user_message for summary in stored.recent_turn_summaries), stored.model_dump())
    assertions.append("topic pool relation focus and redacted summaries persisted")
    service.repository.close() if service.repository is not None else None

    restarted = _service(db_path, battle_dex_path=battle_dex_path)
    restarted_client = TestClient(create_app(advisor_service=restarted))
    with patch("advisor.runtime._build_native_agent", return_value=_FakeP12Agent()):
        followup = _post_chat(restarted_client, "什么意思", session_id=session_id)
    require(followup["session_id"] == session_id, followup)
    require(followup["response"]["runtime_path"] == "native_llm_terminal", followup)
    require("黑猫巫师" in followup["response"]["answer"], followup)
    require("恶魔狼" in followup["response"]["answer"], followup)
    assertions.append("backend restart preserves relation follow-up continuity")

    invalid_context = _team_context_payload(restarted.repository, "豆丁鱼")
    invalid_context["slots"][0]["selected_moves"][0]["move_id"] = "not-a-real-move-id"
    unrelated = restarted_client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "你好",
            "context_attachments": [invalid_context],
        },
    )
    require(unrelated.status_code == 200, unrelated.text)
    unrelated_payload = unrelated.json()
    require(unrelated_payload["response"]["analysis_type"] != "runtime_failure", unrelated_payload)
    require(
        unrelated_payload["session_event"]["diagnostic"]["attachment_validation"]["action"]
        == "ignored_for_unrelated_chat",
        unrelated_payload,
    )
    assertions.append("invalid team attachment is ignored for unrelated chat")

    team_dependent = restarted_client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "分析这队联防",
            "context_attachments": [invalid_context],
        },
    )
    require(team_dependent.status_code == 200, team_dependent.text)
    team_payload = team_dependent.json()
    require(team_payload["response"]["analysis_type"] == "runtime_failure", team_payload)
    require("修正队伍" in team_payload["response"]["answer"], team_payload)
    assertions.append("invalid team attachment blocks only team-dependent turn")
    restarted.repository.close() if restarted.repository is not None else None

    failing_store = _FailingCommitStore()
    failing_service = AdvisorService(
        repository=BattleDexRepository(battle_dex_path),
        default_backend="deterministic",
        session_store=failing_store,
    )
    failing_client = TestClient(create_app(advisor_service=failing_service))
    commit_failure = failing_client.post("/chat", json={"message": "豆丁鱼是什么定位？"})
    require(commit_failure.status_code == 200, commit_failure.text)
    failure_payload = commit_failure.json()
    require(failure_payload["response"]["continuity_persisted"] is False, failure_payload)
    require(failure_payload["session_event"]["reason"] == "continuity_not_persisted", failure_payload)
    require(
        failure_payload["session_event"]["diagnostic"]["continuity"]["code"]
        == "continuity_not_persisted",
        failure_payload,
    )
    require(failing_store.store.set_calls == 1, failing_store.store.set_calls)
    require(not failing_store.store.state.recent_turn_summaries, failing_store.store.state.model_dump())
    assertions.append("commit failure returns controlled event metadata without partial mutation")
    failing_service.repository.close() if failing_service.repository is not None else None

    return {
        "status": "ok",
        "session_id": session_id,
        "session_db_path": str(db_path),
        "assertions": assertions,
    }


def _write_battle_dex(db_path: Path) -> None:
    class _Namespace:
        def __init__(self, **values: object) -> None:
            self.__dict__.update(values)

    write_sqlite(
        _Namespace(
            importer_run_dir=IMPORTER_RUN_DIR,
            db_path=db_path,
            schema_path=SCHEMA_PATH,
            write_run_id="p12_e2e_smoke",
            replace_run=False,
        )
    )


def _service(db_path: Path, *, battle_dex_path: Path) -> AdvisorService:
    return AdvisorService(
        repository=BattleDexRepository(battle_dex_path),
        default_backend="deterministic",
        session_db_path=db_path,
    )


def _post_chat(client: TestClient, message: str, *, session_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"message": message}
    if session_id is not None:
        payload["session_id"] = session_id
    response = client.post("/chat", headers=_native_headers(), json=payload)
    require(response.status_code == 200, response.text)
    return response.json()


def _native_headers() -> dict[str, str]:
    return {
        HEADER_RUNTIME_MODE: "native",
        HEADER_PROVIDER_KEY: "p4b-secret-test-key",
        HEADER_PROVIDER_BASE_URL: "https://provider.example/v1",
        HEADER_MODEL: "p4b-test-model",
    }


def _team_context_payload(repository: BattleDexRepository, species_query: str) -> dict[str, Any]:
    profile = repository.get_species_profile(species_query)
    require(profile is not None, species_query)
    assert profile is not None
    moves = [
        move
        for move in repository.get_species_available_moves(profile.species_id, limit=20)
        if move.move_id
    ]
    require(bool(moves), species_query)
    move = moves[0]
    return {
        "kind": "team_context",
        "schema_version": "team_context.v1",
        "source": "team_builder",
        "team_id": "p12-e2e-team",
        "active": True,
        "slots": [
            {
                "slot_index": 1,
                "species_id": profile.species_id,
                "display_name": profile.display_name,
                "primary_type": profile.primary_type,
                "secondary_type": profile.secondary_type,
                "fixed_ability": (
                    {
                        "ability_name": profile.ability_name,
                        "effect_text": profile.ability_effect_text,
                    }
                    if profile.ability_name
                    else None
                ),
                "selected_moves": [
                    {
                        "move_id": move.move_id,
                        "move_name": move.move_name,
                        "access_channel": move.access_channel,
                        "move_type": move.move_type,
                        "category_raw": move.category_raw,
                    }
                ],
                "nature": {"label": "保守", "plus_stat": "spa", "minus_stat": "atk"},
                "individual_value_bonuses": [{"stat": "spa", "value": 8}],
                "notes": "p12 e2e context",
            }
        ],
    }


class _FakeP12Agent:
    def run_sync(self, message: str, *, deps, model, instructions: str, **_kwargs: Any):
        if "Draft deterministic digest" in message:
            if "黑猫巫师" in message and "恶魔狼" in message:
                answer = "黑猫巫师配合恶魔狼主C时，黑猫巫师是前置节奏/功能入口，恶魔狼是后手收割核心；这只是按当前资料看的 provisional 关系。"
            elif "黑猫巫师" in message:
                answer = "黑猫巫师常被拿来首发，是因为它更像先手/功能或副攻入口，可以先制造节奏再让后排接手。"
            elif "圣羽翼王" in message:
                answer = "圣羽翼王要按有条件威胁处理，先拆速度/先手节奏，再决定换入和反压。"
            else:
                answer = "我会基于已确认资料给出自然语言判断，不暴露工具结果。"
        elif "什么意思" in message:
            answer = "刚才的意思是：黑猫巫师不是要抢恶魔狼的主C位置，而是帮恶魔狼争取登场节奏；恶魔狼仍是收割核心。"
        else:
            answer = "我在，直接说你的队伍目标或想处理的精灵。"
        return _FakeNativeResult(
            AdvisorResponse(
                backend="pydantic_ai_native",
                answer_summary=answer,
                tool_results=[],
                evidence_summary=[],
                confidence_notes=[],
                followup_options=[],
            )
        )


class _FakeNativeResult:
    def __init__(self, output: AdvisorResponse) -> None:
        self.output = output

    def all_messages(self) -> list[Any]:
        return []


class _FailingCommitStateStore:
    def __init__(self) -> None:
        from advisor.contracts import AdvisorSessionState

        self.state = AdvisorSessionState()
        self.set_calls = 0

    def get(self):
        return self.state.model_copy(deep=True)

    def set(self, state):
        self.set_calls += 1
        raise RuntimeError("simulated e2e commit failure")

    def clear(self):
        from advisor.contracts import AdvisorSessionState

        self.state = AdvisorSessionState()
        return self.get()


class _FailingCommitStore:
    def __init__(self) -> None:
        self.store = _FailingCommitStateStore()
        self.session_id = "p12-e2e-failing-session"

    def resolve(self, requested_session_id: str | None):
        from api.services.session_store import SessionEvent, SessionResolution

        return SessionResolution(
            session_id=self.session_id,
            store=self.store,
            event=SessionEvent(
                type="continued",
                reason="p12_e2e_failing_store",
                message="已继续当前本地会话。",
                user_action=None,
                diagnostic={},
            ),
        )

    def clear_active(self, *, reason: str = "user_clear"):
        from api.services.session_store import SessionEvent

        return (
            self.session_id,
            SessionEvent(
                type="cleared",
                reason=reason,
                message="已清空当前会话状态。",
                user_action=None,
                diagnostic={},
            ),
        )


def require(condition: bool, payload: object) -> None:
    if not condition:
        raise AssertionError(payload)


if __name__ == "__main__":
    raise SystemExit(main())
