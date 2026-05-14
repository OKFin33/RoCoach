from __future__ import annotations

import unittest

from advisor.experiment_layers import ExperimentLayerConfig, P10hExperimentDocContextRetriever


class P10hExperimentLayerTests(unittest.TestCase):
    def test_full_condition_retrieves_layer_diverse_context(self) -> None:
        retriever = P10hExperimentDocContextRetriever(
            ExperimentLayerConfig(
                include_b_layer_candidates=True,
                include_d1_attention=True,
                include_d2_general_priors=True,
                include_d3_demonstrations=True,
            )
        )

        snippets = retriever.retrieve(
            query="有贝古斯的队伍是不是都靠贝古斯当核心？",
            analysis_type="team",
            limit=4,
        )
        topics = [snippet.topic for snippet in snippets]

        self.assertTrue(any(topic.startswith("Bplus_archetype_candidate:") for topic in topics))
        self.assertTrue(any(topic.startswith("D1_attention:") for topic in topics))
        self.assertTrue(any(topic.startswith("D3_long_demo:") for topic in topics))
        self.assertLessEqual(len(snippets), 4)

    def test_d1_d2_condition_retrieves_general_priors(self) -> None:
        retriever = P10hExperimentDocContextRetriever(
            ExperimentLayerConfig(
                include_d1_attention=True,
                include_d2_general_priors=True,
            )
        )

        snippets = retriever.retrieve(
            query="翼王斩杀线能不能直接套百分比？",
            analysis_type="team",
            limit=4,
        )
        topics = [snippet.topic for snippet in snippets]

        self.assertTrue(any(topic.startswith("D1_attention:") for topic in topics))
        self.assertTrue(any(topic.startswith("D2_general_prior:") for topic in topics))

    def test_negative_query_does_not_inject_experiment_layers(self) -> None:
        retriever = P10hExperimentDocContextRetriever(
            ExperimentLayerConfig(
                include_b_layer_candidates=True,
                include_d1_attention=True,
                include_d2_general_priors=True,
                include_d3_demonstrations=True,
            )
        )

        snippets = retriever.retrieve(
            query="这个项目怎么配置 API key？",
            analysis_type="team",
            limit=4,
        )

        self.assertFalse(
            any(
                snippet.topic.startswith(
                    (
                        "Bplus_archetype_candidate:",
                        "D1_attention:",
                        "D2_general_prior:",
                        "D3_long_demo:",
                    )
                )
                for snippet in snippets
            )
        )


if __name__ == "__main__":
    unittest.main()
