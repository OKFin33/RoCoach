from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from tools.p14_bilibili_related_discovery import (
    RelatedSeed,
    discover_related_candidates,
    parse_related_bvids,
    related_seeds_from_args,
)


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


class P14BilibiliRelatedDiscoveryTests(unittest.TestCase):
    def test_parse_related_bvids(self) -> None:
        response = '{"code":0,"data":[{"bvid":"BV1GOOD"},{"bvid":"BV1GOOD"},{"bvid":"BV1OTHER"}]}'

        self.assertEqual(parse_related_bvids(response), ["BV1GOOD", "BV1OTHER"])

    def test_seed_source_id_resolves_bvid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue = root / "source_queue.yaml"
            _write_yaml(
                queue,
                {
                    "sources": [
                        {
                            "source_id": "seed_source",
                            "url": "https://www.bilibili.com/video/BV1SEED/",
                            "title": "洛克王国世界PVP实战",
                        }
                    ]
                },
            )

            seeds = related_seeds_from_args(source_queue_path=queue, bvids=[], seed_source_ids=["seed_source"])

        self.assertEqual(seeds, [RelatedSeed(bvid="BV1SEED", seed_source_id="seed_source", title="洛克王国世界PVP实战")])

    def test_discovers_related_candidates_and_skips_existing_or_off_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue = root / "source_queue.yaml"
            battle_dex = root / "missing.sqlite"
            _write_yaml(
                queue,
                {
                    "schema_version": "p14.source_queue.v0",
                    "sources": [
                        {
                            "source_id": "existing",
                            "url": "https://www.bilibili.com/video/BV1EXIST/",
                        }
                    ],
                },
            )

            def fake_fetch_related(seed: RelatedSeed, *, max_related: int, timeout: int) -> tuple[list[str], str]:
                return ["BV1EXIST", "BV1GOOD", "BV1PVE"], ""

            def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                target = command[-1]
                if target == "https://www.bilibili.com/video/BV1GOOD/":
                    line = 'BV1GOOD\t洛克王国世界PVP冷门阵容讲解\t作者\t1778510821\t10000\t20\t120\t["洛克王国"]\n'
                    return subprocess.CompletedProcess(args=command, returncode=0, stdout=line, stderr="")
                if target == "https://www.bilibili.com/video/BV1PVE/":
                    line = 'BV1PVE\t洛克王国世界剧情通关攻略\t作者\t1778510821\t10000\t20\t120\t["洛克王国"]\n'
                    return subprocess.CompletedProcess(args=command, returncode=0, stdout=line, stderr="")
                raise AssertionError(target)

            with patch("tools.p14_bilibili_related_discovery.fetch_related_bvids", side_effect=fake_fetch_related):
                with patch("tools.p14_bilibili_creator_discovery.subprocess.run", side_effect=fake_run):
                    candidates, report = discover_related_candidates(
                        seeds=[RelatedSeed("BV1SEED", seed_source_id="seed_source")],
                        max_related_per_seed=10,
                        max_candidates=10,
                        min_score=7,
                        source_queue_path=queue,
                        battle_dex_path=battle_dex,
                        timeout=5,
                    )

        self.assertEqual([item["source_id"] for item in candidates], ["kgsrc_bili_bv1good"])
        reasons = [item["reason"] for item in report["skipped"]]
        self.assertIn("duplicate_existing_queue", reasons)
        self.assertIn("off_boundary_pve_or_non_pvp_title", reasons)


if __name__ == "__main__":
    unittest.main()
