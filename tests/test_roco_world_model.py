import unittest

from roco_world_model import RocoWorldTypeChart


class RocoWorldTypeChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chart = RocoWorldTypeChart()

    def test_all_types_loaded(self) -> None:
        self.assertEqual(len(self.chart.types), 18)
        self.assertIn("机械", self.chart.types)
        self.assertIn("光", self.chart.types)

    def test_single_type_multipliers(self) -> None:
        self.assertEqual(self.chart.attack_multiplier("火", "草"), 2.0)
        self.assertEqual(self.chart.attack_multiplier("火", "水"), 0.5)
        self.assertEqual(self.chart.attack_multiplier("电", "地"), 0.5)
        self.assertEqual(self.chart.attack_multiplier("普通", "武"), 1.0)

    def test_dual_type_multipliers(self) -> None:
        self.assertEqual(self.chart.combined_multiplier("火", ("草", "机械")), 3.0)
        self.assertEqual(self.chart.combined_multiplier("水", ("火", "地")), 3.0)
        self.assertEqual(self.chart.combined_multiplier("光", ("恶", "幽")), 3.0)
        self.assertEqual(self.chart.combined_multiplier("电", ("地", "翼")), 1.0)
        self.assertAlmostEqual(self.chart.combined_multiplier("火", ("水", "龙")), 1.0 / 3.0, places=6)

    def test_effectiveness_labels(self) -> None:
        self.assertEqual(self.chart.effectiveness_label("火", ("草",)), "super_effective")
        self.assertEqual(self.chart.effectiveness_label("火", ("水", "龙")), "double_resisted")
        self.assertEqual(self.chart.effectiveness_label("电", ("地", "翼")), "neutral")
        self.assertEqual(self.chart.effectiveness_label("火", ("草", "机械")), "double_super_effective")

    def test_status_immunities(self) -> None:
        self.assertEqual(self.chart.immune_statuses("冰"), ("冻结",))
        self.assertEqual(self.chart.immune_statuses("火"), ("灼烧",))
        self.assertEqual(
            self.chart.immune_statuses(("草", "火")),
            ("寄生", "灼烧"),
        )
        self.assertEqual(self.chart.immune_statuses("普通"), ())

    def test_invalid_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.chart.attack_multiplier("圣", "草")

        with self.assertRaises(ValueError):
            self.chart.combined_multiplier("火", ())


if __name__ == "__main__":
    unittest.main()
