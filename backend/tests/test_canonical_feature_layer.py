"""Cross-engine invariants for the deterministic canonical evidence layer."""
from unittest.mock import AsyncMock, patch

import pytest

from app.services.attachment_engine import derive_baseline_attachment
from app.services.developmental_exposure_engine import extract_developmental_exposures_async
from app.services.pattern_engine import interpret_experience_async
from app.services.state_trait_engine import propose_state_trait_implications_async
from app.utils.foundational_baseline import derive_foundational_baseline_async


@pytest.mark.asyncio
async def test_canonical_paths_do_not_call_openai():
    with patch(
        "app.services.developmental_exposure_engine.openai_service.analyze",
        new_callable=AsyncMock,
    ) as exposure_ai, patch(
        "app.services.pattern_engine.openai_service.analyze",
        new_callable=AsyncMock,
    ) as pattern_ai, patch(
        "app.services.state_trait_engine.openai_service.analyze",
        new_callable=AsyncMock,
    ) as state_ai, patch(
        "app.utils.foundational_baseline.openai_service.analyze",
        new_callable=AsyncMock,
    ) as baseline_ai:
        extraction = await extract_developmental_exposures_async(
            "Her father was alcoholic and absent."
        )
        interpretation = await interpret_experience_async(
            "Case", 8, extraction["exposures"]
        )
        await propose_state_trait_implications_async("Case", 8, interpretation)
        await derive_foundational_baseline_async("A chaotic and neglectful household.")

    exposure_ai.assert_not_awaited()
    pattern_ai.assert_not_awaited()
    state_ai.assert_not_awaited()
    baseline_ai.assert_not_awaited()


@pytest.mark.asyncio
async def test_contrasting_lives_keep_distinct_canonical_formulations():
    cases = {
        "stable": "Easygoing, close friends, a secure relationship, and a mentor.",
        "unpredictable": "An alcoholic caregiver made the household unpredictable.",
        "betrayal": "A best friend excluded and bullied her.",
        "physical_threat": "He was beaten and physically abused by a caregiver.",
        "corrective": "She started therapy and repaired conflicts with a reliable partner.",
    }
    outputs = {}
    for name, text in cases.items():
        extraction = await extract_developmental_exposures_async(text)
        interpretation = await interpret_experience_async(
            name, 12, extraction["exposures"],
            protective_factors_this_batch=extraction["protective_factors"],
        )
        outputs[name] = (
            tuple(item["exposure_type"] for item in extraction["exposures"]),
            tuple(item["factor_type"] for item in extraction["protective_factors"]),
            interpretation["adaptation_strategy"],
        )

    assert len(set(outputs.values())) == len(cases)
    assert outputs["unpredictable"][2] == "hypervigilance"
    assert outputs["physical_threat"][2] == "hypervigilance"
    assert outputs["corrective"][2] is None
    assert outputs["stable"][0] == ()


def test_baseline_attachment_uses_canonical_features_and_low_information_is_neutral():
    adverse = derive_baseline_attachment({
        "exposures": [{"developmental_domains": ["attachment_security"]}],
        "protective_factors": [],
    })
    supported = derive_baseline_attachment({
        "exposures": [],
        "protective_factors": [{"domains_buffered": ["attachment_security"]}],
    })
    low_information = derive_baseline_attachment({"exposures": [], "protective_factors": []})

    assert adverse["dimensions"]["relational_security"] < low_information["dimensions"]["relational_security"]
    assert supported["dimensions"]["relational_security"] > low_information["dimensions"]["relational_security"]
    assert low_information == {
        "style": "secure",
        "dimensions": {
            "attachment_anxiety": 0.2,
            "attachment_avoidance": 0.2,
            "relational_security": 0.8,
        },
    }
