import unittest

from battle_engine.contracts import (
    AnalysisGoals,
    Archetype,
    ArchetypeScore,
    BaseStats,
    DefensiveCoverageEntry,
    OffensiveCoverageEntry,
    PressureProfile,
    RoleScore,
    RoleTag,
    SpeciesProfile,
    SpeciesRoleReport,
    TeamAnalysisRequest,
    TeamArchetypeReport,
    TeamSlot,
    TeamStructureReport,
    to_payload,
)


class ContractsTests(unittest.TestCase):
    def test_base_stats_bst(self) -> None:
        stats = BaseStats(hp=80, atk=90, defense=70, spa=95, spd=75, spe=110)
        self.assertEqual(stats.bst, 520)

    def test_payload_conversion(self) -> None:
        profile = SpeciesProfile(
            species_key="dimo.base",
            dex_no="001",
            base_name="迪莫",
            form_name=None,
            primary_type="光",
            secondary_type=None,
            base_stats=BaseStats(hp=80, atk=90, defense=70, spa=95, spd=75, spe=110),
            abilities=("holy_body",),
            move_ids=("flash_burst", "light_barrier"),
        )
        payload = to_payload(profile)
        self.assertEqual(payload["species_key"], "dimo.base")
        self.assertEqual(payload["primary_type"], "光")
        self.assertEqual(payload["abilities"], ["holy_body"])
        self.assertEqual(payload["base_stats"]["hp"], 80)

    def test_team_request_contract(self) -> None:
        request = TeamAnalysisRequest(
            slots=(
                TeamSlot(slot_index=1, species_key=None, primary_type="水", secondary_type="冰"),
                TeamSlot(slot_index=2, species_key=None, primary_type="火"),
            ),
            goals=AnalysisGoals(preserve_bulk=True, avoid_duplicate_weakness=True),
            target_archetypes=(Archetype.BALANCE,),
        )
        payload = to_payload(request)
        self.assertEqual(payload["slots"][0]["secondary_type"], "冰")
        self.assertEqual(payload["goals"]["preserve_bulk"], True)
        self.assertEqual(payload["target_archetypes"], ["balance"])

    def test_report_contracts(self) -> None:
        role_report = SpeciesRoleReport(
            species_key="mock.species",
            primary_role=RoleTag.BULKY_PIVOT,
            secondary_roles=(RoleScore(role_tag=RoleTag.SUPPORT, score=0.68, evidence=("has pivot move",)),),
            pressure_profile=PressureProfile(
                offense=0.52,
                bulk=0.83,
                speed=0.41,
                utility=0.77,
                sustain=0.64,
            ),
            evidence=("good mixed bulk", "can pivot and spread status"),
        )
        structure_report = TeamStructureReport(
            structural_score=0.74,
            repeated_weaknesses=("地", "毒"),
            missing_resistances=("光",),
            offensive_coverage=(
                OffensiveCoverageEntry(
                    attacker_type="火",
                    super_effective_targets=("草", "冰", "虫", "机械"),
                    resisted_targets=("水", "地", "龙"),
                ),
            ),
            defensive_coverage=(
                DefensiveCoverageEntry(defending_type="地", weak_slots=2, resist_slots=1, neutral_slots=3),
            ),
            primary_patch_types=("草", "翼"),
            conditional_dual_patch_types=("草/龙",),
            evidence=("ground weakness appears twice",),
        )
        archetype_report = TeamArchetypeReport(
            primary_archetype=Archetype.BALANCE,
            archetype_scores=(
                ArchetypeScore(archetype=Archetype.BALANCE, score=0.82),
                ArchetypeScore(archetype=Archetype.BULKY_OFFENSE, score=0.57),
            ),
            tempo_score=0.58,
            sustain_score=0.75,
            pivot_score=0.69,
            setup_score=0.31,
            anti_setup_score=0.44,
            explanation_evidence=("has durable core and moderate pivot access",),
        )

        self.assertEqual(to_payload(role_report)["primary_role"], "bulky_pivot")
        self.assertEqual(to_payload(structure_report)["primary_patch_types"], ["草", "翼"])
        self.assertEqual(to_payload(structure_report)["conditional_dual_patch_types"], ["草/龙"])
        self.assertEqual(to_payload(archetype_report)["primary_archetype"], "balance")


if __name__ == "__main__":
    unittest.main()
