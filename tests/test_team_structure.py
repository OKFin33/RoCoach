import subprocess
import sys
import unittest
from pathlib import Path
import json

from engine.contracts import TeamSlot
from engine.team_structure import TeamStructureAnalyzer


ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_TEAM = ROOT / "examples" / "phase1_sample_team.json"


class TeamStructureAnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.analyzer = TeamStructureAnalyzer()

    def test_detects_repeated_weaknesses_and_missing_resistances(self) -> None:
        slots = (
            TeamSlot(slot_index=1, species_key=None, primary_type="草"),
            TeamSlot(slot_index=2, species_key=None, primary_type="地"),
            TeamSlot(slot_index=3, species_key=None, primary_type="龙"),
            TeamSlot(slot_index=4, species_key=None, primary_type="翼"),
            TeamSlot(slot_index=5, species_key=None, primary_type="火"),
            TeamSlot(slot_index=6, species_key=None, primary_type="水"),
        )
        report = self.analyzer.analyze(slots)

        self.assertIn("冰", report.repeated_weaknesses)
        self.assertGreaterEqual(report.structural_score, 0.0)
        self.assertLessEqual(report.structural_score, 1.0)
        self.assertTrue(report.evidence)

    def test_patch_suggestions_prefer_covering_missing_resists(self) -> None:
        slots = (
            TeamSlot(slot_index=1, species_key=None, primary_type="草"),
            TeamSlot(slot_index=2, species_key=None, primary_type="草"),
            TeamSlot(slot_index=3, species_key=None, primary_type="地"),
            TeamSlot(slot_index=4, species_key=None, primary_type="地"),
            TeamSlot(slot_index=5, species_key=None, primary_type="龙"),
            TeamSlot(slot_index=6, species_key=None, primary_type="龙"),
        )
        report = self.analyzer.analyze(slots)

        self.assertIn("冰", report.repeated_weaknesses)
        self.assertTrue(report.primary_patch_types)
        self.assertNotIn("冰", report.primary_patch_types[:2])

    def test_patch_suggestions_can_include_dual_type_candidates(self) -> None:
        slots = (
            TeamSlot(slot_index=1, species_key=None, primary_type="草"),
            TeamSlot(slot_index=2, species_key=None, primary_type="虫"),
            TeamSlot(slot_index=3, species_key=None, primary_type="翼"),
            TeamSlot(slot_index=4, species_key=None, primary_type="龙"),
            TeamSlot(slot_index=5, species_key=None, primary_type="草"),
            TeamSlot(slot_index=6, species_key=None, primary_type="虫"),
        )
        report = self.analyzer.analyze(slots)

        self.assertTrue(report.conditional_dual_patch_types)
        self.assertTrue(all("/" in candidate for candidate in report.conditional_dual_patch_types))

    def test_offensive_coverage_uses_represented_team_types(self) -> None:
        slots = (
            TeamSlot(slot_index=1, species_key=None, primary_type="火", secondary_type="翼"),
            TeamSlot(slot_index=2, species_key=None, primary_type="水"),
        )
        report = self.analyzer.analyze(slots)
        covered = {entry.attacker_type for entry in report.offensive_coverage}

        self.assertEqual(covered, {"火", "翼", "水"})

    def test_cli_outputs_report(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "engine.phase1_cli",
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
        self.assertIn("== Team Structure Report ==", result.stdout)
        self.assertIn("== Defensive Coverage ==", result.stdout)
        self.assertIn("primary_patch_types:", result.stdout)
        self.assertIn("conditional_dual_patch_types:", result.stdout)

    def test_cli_supports_json_output(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "engine.phase1_cli",
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
        payload = json.loads(result.stdout)
        self.assertIn("structural_score", payload)
        self.assertIn("defensive_coverage", payload)
        self.assertIn("primary_patch_types", payload)
        self.assertIn("conditional_dual_patch_types", payload)

    def test_cli_supports_file_input_text_mode(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "engine.phase1_cli",
                "--input-file",
                str(EXAMPLE_TEAM),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("== Team Structure Report ==", result.stdout)
        self.assertIn("冰:", result.stdout)


if __name__ == "__main__":
    unittest.main()
