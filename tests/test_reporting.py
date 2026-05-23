import json
import subprocess
import sys
import unittest
from pathlib import Path

from engine.contracts import TeamSlot
from knowledge.service import Phase15ReportService


ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_TEAM = ROOT / "examples" / "phase1_sample_team.json"


class ReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = Phase15ReportService()

    def test_deterministic_report_service_returns_schema_payload(self) -> None:
        slots = (
            TeamSlot(slot_index=1, species_key=None, primary_type="草"),
            TeamSlot(slot_index=2, species_key=None, primary_type="地"),
            TeamSlot(slot_index=3, species_key=None, primary_type="龙"),
            TeamSlot(slot_index=4, species_key=None, primary_type="翼"),
            TeamSlot(slot_index=5, species_key=None, primary_type="火"),
            TeamSlot(slot_index=6, species_key=None, primary_type="水"),
        )

        result = self.service.analyze(slots)

        self.assertEqual(result.backend, "deterministic")
        self.assertTrue(result.narrative_report.summary)
        self.assertTrue(result.narrative_report.major_risks)
        self.assertTrue(result.narrative_report.patch_guidance.primary_patch_types)
        self.assertTrue(result.retrieved_snippets)

    def test_report_confidence_notes_include_structure_scope(self) -> None:
        slots = (
            TeamSlot(slot_index=1, species_key=None, primary_type="机械", secondary_type="地"),
            TeamSlot(slot_index=2, species_key=None, primary_type="武", secondary_type="水"),
        )

        result = self.service.analyze(slots)
        scopes = {item.claim_scope for item in result.narrative_report.confidence_notes}
        self.assertIn("structure_analysis", scopes)

    def test_phase15_cli_outputs_text_report(self) -> None:
        output = subprocess.run(
            [
                sys.executable,
                "-m",
                "knowledge.phase15_cli",
                "--slot",
                "A,草",
                "--slot",
                "B,地",
                "--slot",
                "C,龙",
                "--slot",
                "D,翼",
                "--slot",
                "E,火",
                "--slot",
                "F,水",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("== Phase 1.5 Team Report ==", output.stdout)
        self.assertIn("== Major Risks ==", output.stdout)
        self.assertIn("primary_patch_types:", output.stdout)

    def test_phase15_cli_outputs_json_report(self) -> None:
        output = subprocess.run(
            [
                sys.executable,
                "-m",
                "knowledge.phase15_cli",
                "--input-file",
                str(EXAMPLE_TEAM),
                "--format",
                "json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(output.stdout)
        self.assertEqual(payload["backend"], "deterministic")
        self.assertIn("narrative_report", payload)
        self.assertIn("summary", payload["narrative_report"])
        self.assertIn("retrieved_snippets", payload)


if __name__ == "__main__":
    unittest.main()
