from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from tools.p14_bilibili_creator_discovery import (
    CreatorSeed,
    creator_seeds_from_args,
    discover_creator_candidates,
    fetch_video_hit,
    run_creator_space,
)


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


class P14BilibiliCreatorDiscoveryTests(unittest.TestCase):
    def test_creator_space_parses_bvids(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="BV1GOOD\nnot-a-bv\nBV1OTHER\nBV1GOOD\n",
            stderr="",
        )
        with patch("tools.p14_bilibili_creator_discovery.subprocess.run", return_value=completed):
            bvids, diagnostics = run_creator_space(CreatorSeed("123"), max_videos=10, timeout=5)

        self.assertEqual(bvids, ["BV1GOOD", "BV1OTHER"])
        self.assertEqual(diagnostics, "")

    def test_fetch_video_hit_uses_source_discovery_parser(self) -> None:
        line = 'BV1GOOD\t洛克王国世界PVP冷门阵容讲解\t作者\t1778510821\t10000\t20\t120\t["pvp"]\n'
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=line, stderr="")
        with patch("tools.p14_bilibili_creator_discovery.subprocess.run", return_value=completed):
            hit, diagnostics = fetch_video_hit("BV1GOOD", query_label="creator_space:作者", timeout=5)

        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.bvid, "BV1GOOD")
        self.assertEqual(hit.title, "洛克王国世界PVP冷门阵容讲解")
        self.assertEqual(diagnostics, "")

    def test_seed_source_id_resolves_creator(self) -> None:
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
            completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="12345\t作者\n", stderr="")
            with patch("tools.p14_bilibili_creator_discovery.subprocess.run", return_value=completed):
                seeds = creator_seeds_from_args(
                    source_queue_path=queue,
                    uploader_ids=[],
                    seed_source_ids=["seed_source"],
                    timeout=5,
                )

        self.assertEqual(seeds, [CreatorSeed(uploader_id="12345", uploader="作者", seed_source_id="seed_source")])

    def test_discovers_candidates_and_skips_off_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue = root / "source_queue.yaml"
            battle_dex = root / "missing.sqlite"
            _write_yaml(queue, {"schema_version": "p14.source_queue.v0", "sources": []})

            def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                target = command[-1]
                if target == "https://space.bilibili.com/123/video":
                    return subprocess.CompletedProcess(args=command, returncode=0, stdout="BV1GOOD\nBV1PVE\n", stderr="")
                if target == "https://www.bilibili.com/video/BV1GOOD/":
                    line = 'BV1GOOD\t洛克王国世界PVP冷门阵容讲解\t作者\t1778510821\t10000\t20\t120\t["洛克王国"]\n'
                    return subprocess.CompletedProcess(args=command, returncode=0, stdout=line, stderr="")
                if target == "https://www.bilibili.com/video/BV1PVE/":
                    line = 'BV1PVE\t洛克王国世界剧情通关攻略\t作者\t1778510821\t10000\t20\t120\t["洛克王国"]\n'
                    return subprocess.CompletedProcess(args=command, returncode=0, stdout=line, stderr="")
                raise AssertionError(target)

            with patch("tools.p14_bilibili_creator_discovery.subprocess.run", side_effect=fake_run):
                candidates, report = discover_creator_candidates(
                    seeds=[CreatorSeed("123", uploader="作者")],
                    max_videos_per_creator=10,
                    max_candidates=10,
                    min_score=7,
                    source_queue_path=queue,
                    battle_dex_path=battle_dex,
                    timeout=5,
                )

        self.assertEqual([item["source_id"] for item in candidates], ["kgsrc_bili_bv1good"])
        self.assertEqual(report["candidate_count_after_cap"], 1)
        self.assertEqual(report["skipped"][0]["reason"], "off_boundary_pve_or_non_pvp_title")


if __name__ == "__main__":
    unittest.main()
