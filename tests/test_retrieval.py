from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from advisor.retrieval import DocContextRetriever
from tools.import_battle_dex_sqlite import write_sqlite


ROOT = Path(__file__).resolve().parent.parent
IMPORTER_RUN_DIR = ROOT / "data" / "importer_runs" / "2026-04-14Tpolicy_b_importer_dry_run"
SCHEMA_PATH = ROOT / "docs" / "specs" / "battle_dex_sqlite_schema_v1.sql"


class RetrievalPhaseAEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls._tmpdir.name) / "retrieval_eval.sqlite"
        write_sqlite(
            argparse_namespace(
                importer_run_dir=IMPORTER_RUN_DIR,
                db_path=cls.db_path,
                schema_path=SCHEMA_PATH,
                write_run_id="retrieval_eval_run",
                replace_run=False,
            )
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()

    def setUp(self) -> None:
        self.retriever = DocContextRetriever()

    def test_topic_coverage_for_representative_queries(self) -> None:
        cases = (
            ("分析这队联防结构", "team", "engine_grounding"),
            ("这个判断有什么证据，confidence 够吗", "team", "confidence_guard"),
            ("双属性抗性和弱点怎么按当前 baseline 算", "team", "dual_type_baseline"),
            ("豆丁鱼在这队里适合主C还是辅助", "species", "team_conditional_roles"),
            ("当前 CLI 支持范围和边界是什么", "species", "scope_boundary"),
        )

        for query, analysis_type, expected_topic in cases:
            with self.subTest(query=query, analysis_type=analysis_type):
                topics = self._topics(query=query, analysis_type=analysis_type)
                self.assertIn(expected_topic, topics)

    def test_limit_is_strictly_respected(self) -> None:
        query = "分析这队联防，双属性抗性，有什么证据，支持范围是什么"

        for limit in (0, 1, 2, 3):
            with self.subTest(limit=limit):
                snippets = self.retriever.retrieve(query=query, analysis_type="team", limit=limit)
                self.assertLessEqual(len(snippets), limit)

        self.assertEqual(self.retriever.retrieve(query=query, analysis_type="team", limit=-1), [])

    def test_duplicate_topics_are_not_returned(self) -> None:
        snippets = self.retriever.retrieve(
            query="分析分析联防联防结构结构证据证据",
            analysis_type="team",
            limit=10,
        )
        topics = [snippet.topic for snippet in snippets]

        self.assertEqual(len(topics), len(set(topics)))

    def test_analysis_type_filter_prevents_irrelevant_snippet_leakage(self) -> None:
        team_topics = self._topics(query="这队的主C辅助角色定位怎么判断", analysis_type="team")
        species_topics = self._topics(query="这只精灵双属性抗性弱点怎么算", analysis_type="species")

        self.assertNotIn("team_conditional_roles", team_topics)
        self.assertNotIn("dual_type_baseline", species_topics)

    def test_unrelated_query_only_returns_baseline_guardrails(self) -> None:
        topics = set(self._topics(query="banana weather unrelated noise", analysis_type="team"))

        self.assertLessEqual(topics, {"engine_grounding", "confidence_guard"})
        self.assertNotIn("dual_type_baseline", topics)
        self.assertNotIn("team_conditional_roles", topics)
        self.assertNotIn("scope_boundary", topics)

    def test_mechanism_tokens_in_ability_text_trigger_reviewed_and_missing_mechanism_states(self) -> None:
        matches = self.retriever.inspect_mechanisms(
            query="帕帕斯卡适合干什么",
            evidence_texts=["1号位技能获得迅捷和传动1。"],
        )

        resolved = {match.token for match in matches if match.has_reviewed_page}
        missing = {match.token for match in matches if not match.has_reviewed_page}

        self.assertIn("迅捷", resolved)
        self.assertIn("传动", resolved)
        self.assertNotIn("传动", missing)

        snippets = self.retriever.retrieve(
            query="帕帕斯卡适合干什么",
            analysis_type="species",
            evidence_texts=["1号位技能获得迅捷和传动1。"],
            limit=6,
        )
        self.assertTrue(
            any(
                snippet.source_path == "wiki/pages/mechanics/speed_priority_and_swift.md"
                for snippet in snippets
            )
        )
        self.assertTrue(
            any(
                snippet.source_path == "wiki/pages/mechanics/transmission_and_skill_slots.md"
                for snippet in snippets
            )
        )

    def test_mechanism_tokens_in_move_text_trigger_reviewed_page_lookup(self) -> None:
        matches = self.retriever.inspect_mechanisms(
            query="晶石蜗适合干什么",
            evidence_texts=["减伤50%,迅捷,应对攻击。"],
        )
        resolved_topics = {match.topic for match in matches if match.has_reviewed_page}

        self.assertIn("mechanism_speed_priority_swift", resolved_topics)
        self.assertIn("mechanism_response", resolved_topics)

        snippets = self.retriever.retrieve(
            query="晶石蜗适合干什么",
            analysis_type="species",
            evidence_texts=["减伤50%,迅捷,应对攻击。"],
            limit=6,
        )
        snippet_sources = {snippet.source_path for snippet in snippets}
        self.assertIn("wiki/pages/mechanics/speed_priority_and_swift.md", snippet_sources)
        self.assertIn("wiki/pages/mechanics/response_counterplay.md", snippet_sources)

    def test_new_status_and_entry_tokens_trigger_reviewed_page_lookup(self) -> None:
        matches = self.retriever.inspect_mechanisms(
            query="为什么对方换人后我这边还是被冻结",
            evidence_texts=["敌方获得2层中毒印记,主动离场后更换精灵入场。"],
        )
        resolved_topics = {match.topic for match in matches if match.has_reviewed_page}

        self.assertIn("mechanism_status_effects", resolved_topics)
        self.assertIn("mechanism_entry_exit_replacement", resolved_topics)
        self.assertIn("mechanism_marks", resolved_topics)

        snippets = self.retriever.retrieve(
            query="为什么对方换人后我这边还是被冻结",
            analysis_type="species",
            evidence_texts=["敌方获得2层中毒印记,主动离场后更换精灵入场。"],
            limit=8,
        )
        snippet_sources = {snippet.source_path for snippet in snippets}
        self.assertIn("wiki/pages/mechanics/status_effects_and_persistence.md", snippet_sources)
        self.assertIn("wiki/pages/mechanics/entry_exit_and_replacement_timing.md", snippet_sources)
        self.assertIn("wiki/pages/mechanics/marks_and_persistence.md", snippet_sources)

    def test_cli_team_path_shows_doc_context_evidence(self) -> None:
        output = self._run_cli("分析 草 地 龙 翼 火 水 这队联防")

        self.assertIn("retrieve_doc_context", output)
        self.assertIn("doc:", output)
        self.assertIn("docs/agent_framework_decision.md", output)

    def test_cli_species_path_shows_doc_context_evidence(self) -> None:
        output = self._run_cli("豆丁鱼适合当主C还是辅助")

        self.assertIn("retrieve_doc_context", output)
        self.assertIn("doc:", output)
        self.assertTrue(
            "docs/battle_analysis_architecture.md" in output
            or "wiki/pages/mechanics/charge_and_release.md" in output
            or "wiki/pages/mechanics/speed_priority_and_swift.md" in output
        )

    def _topics(self, *, query: str, analysis_type: str, limit: int = 4) -> list[str]:
        return [
            snippet.topic
            for snippet in self.retriever.retrieve(
                query=query,
                analysis_type=analysis_type,
                limit=limit,
            )
        ]

    def _run_cli(self, message: str) -> str:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "advisor.conversation_cli",
                "--db-path",
                str(self.db_path),
                "--skip-bootstrap",
                "--backend",
                "deterministic",
                "--message",
                message,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout


def argparse_namespace(**kwargs: object):
    class _Namespace:
        def __init__(self, **values: object) -> None:
            self.__dict__.update(values)

    return _Namespace(**kwargs)


if __name__ == "__main__":
    unittest.main()
