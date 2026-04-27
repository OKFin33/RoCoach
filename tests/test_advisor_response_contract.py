from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from advisor.contracts import AdvisorToolResult, ToolStatus


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "specs" / "advisor_response_contract.yaml"


class AdvisorResponseContractTests(unittest.TestCase):
    def test_tool_status_enum_matches_yaml_contract(self) -> None:
        contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
        status_enum = (
            contract["fields"]["tool_results"]["items"]["fields"]["status"]["enum"]
        )

        self.assertEqual(
            {status.value for status in ToolStatus},
            set(status_enum),
        )
        self.assertNotIn("unavailable", status_enum)

    def test_serialized_tool_statuses_are_contract_compatible(self) -> None:
        for status in ToolStatus:
            payload = AdvisorToolResult(
                tool_name="contract_probe",
                status=status,
                summary="contract status probe",
            ).model_dump(mode="json")

            self.assertIn(payload["status"], {"ok", "degraded", "refused", "failed"})
            self.assertNotEqual(payload["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
