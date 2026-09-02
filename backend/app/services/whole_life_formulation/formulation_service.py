"""
WholeLifeFormulationService - v2.1 SEMANTIC STABILITY PASS.

Same one evidence-bound whole-life formulation call as Phase 0 (same model,
same Responses API path). What changed: the model is now asked for
ModelWholeLifeFormulation (relevance-scored pattern candidates + attachment
dimensions only, no categorical status/style choices), and this service
runs derivation.py immediately after parsing to produce the final
WholeLifeFormulation everything else consumes. See derivation.py for the
actual threshold logic - this file only wires model call -> parse -> derive.

Not wired into any route. No persistence.
"""
import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx
import openai

from app.core.config import settings
from app.services.whole_life_formulation.derivation import (
    derive_attachment_profile,
    derive_hypothesis_projection,
    derive_pattern_projection,
)
from app.services.whole_life_formulation.request_assembler import WholeLifeFormulationRequest
from app.services.whole_life_formulation.schema import ModelWholeLifeFormulation, WholeLifeFormulation
from app.services.whole_life_formulation.strict_schema import strict_json_schema

logger = logging.getLogger(__name__)

FORMULATION_MODEL = "gpt-5.6-luna"
FORMULATION_SCHEMA_VERSION = "v2.2-final-stability-pass"
DEFAULT_REASONING_EFFORT = "medium"
DEFAULT_MAX_OUTPUT_TOKENS = 16000

SYSTEM_INSTRUCTIONS = """You are a careful developmental psychologist producing a single, complete, \
evidence-bound psychological formulation of one person's whole life, given their background, \
caregiver history, temperament self-description, and every recorded life experience in \
chronological order.

You are NOT diagnosing. You are NOT assigning a disorder. You are reasoning about developmental \
patterns, beliefs, protective factors, and hypotheses - all at the level of psychological \
constructs, never formal DSM/ICD diagnosis names.

HARD RULES - VIOLATING ANY OF THESE MAKES YOUR OUTPUT UNUSABLE:

1. EVERY substantive claim (every Big Five score, every attachment dimension, every state dimension, \
every pattern candidate, belief, protective factor, causal chain step, and hypothesis) must cite at \
least one real experience_id from the EXPERIENCES list, a real intervention_id from the INTERVENTIONS \
list, or an EXACT substring from the BACKGROUND / CAREGIVER HISTORY / TEMPERAMENT text as a \
background_span. Never invent an id. Never paraphrase a background_span - copy the exact words, \
including punctuation, in full - do not truncate a quotation partway through.

2. For every citation, tag subject_role honestly: "self" if the cited text describes something the \
SUBJECT themself did or experienced, "caregiver" if it describes a parent/caregiver's own behavior \
or state, "other" for anyone else, "unspecified" only if genuinely ambiguous. This is the single \
most important rule in this task: the subject's OWN substance use, the subject's OWN incarceration, \
the subject's OWN drug involvement must always be tagged subject_role="self", never "caregiver" - \
even when the surrounding context involves family. Confusing who an event happened TO is the exact \
failure mode this system exists to prevent. Read each sentence's actual grammatical subject.

3. If the text explicitly denies, negates, or rules out something ("was never abused", "no violence \
in the home"), do not extract it as a finding. Hedged language ("kind of chaotic sometimes") still \
counts if the underlying event is affirmed - only genuine denial removes it.

4. Never assert or imply a formal clinical diagnosis (e.g. do not say "Reactive Attachment Disorder", \
"PTSD", "Major Depressive Disorder", or similar). canonical_family values are developmental-pattern- \
level constructs only - use "other" if nothing in the allowed list fits rather than reaching for a \
diagnosis-shaped label in human_label either.

5. change_points must be SPARSE. Only include an entry for an experience_id if it produced a real, \
specific personality, attachment, or state change you can justify with reasoning and evidence. Do \
NOT include an entry for every experience "just in case" - omit entries entirely for experiences \
with nothing meaningful to report. Do not manufacture small movements to avoid an empty list.

6. Every score (Big Five, attachment, state) needs real evidence and an honest confidence value. If \
the life gives you little to go on for a trait, say so with low confidence and general/background \
evidence rather than a bare number - there is no field in this schema that doesn't require a \
citation and a confidence value.

7. hypotheses, contradictions, and unresolved_questions are how you handle uncertainty - use them. \
A hypothesis you are not confident in belongs at status="candidate" with a lower evidence_strength \
and named competing_explanations, not omitted and not overstated. unresolved_questions never need a \
citation - that is the explicit "we don't know" bucket.

8. Reason about the WHOLE life together, not experience-by-experience in isolation. A pattern in the \
30s can be reinforced by, or reinterpret, something that happened in childhood - use \
supporting_evidence and causal_chains to show that connective reasoning explicitly.

9. EVERY numeric score in this schema - every Big Five trait value, every attachment dimension value, \
every state dimension value, every confidence, every evidence_strength, every relevance_score - is on \
a 0.0-to-1.0 scale. Use decimals like 0.55 or 0.7, NEVER whole numbers like 55 or 85. A value above \
1.0 is always wrong.

10. PATTERN SCORECARD: you must score EVERY one of the ten canonical developmental-pattern families \
listed in the schema - loss_and_bereavement, identity_reconstruction, relational_repair, \
avoidant_withdrawal, risk_seeking_dysregulation, caregiving_role_reversal, \
achievement_or_competence_compensation, hypervigilant_monitoring, prosocial_reinvention, and \
substance_coping. This is not optional and not a "pick the relevant ones" task - the schema requires \
an entry for all ten, every time. For each one, score its RELEVANCE to this specific person on the \
0.0-1.0 scale, honestly and continuously. Do not think in terms of "is this pattern present or \
absent" - think "how strongly does the evidence in this life support this developmental construct, \
right now." Most lives will have several families that are genuinely NOT relevant - for those, give \
an honest low score (well under 0.35) with EMPTY supporting_evidence. Do not manufacture or stretch \
evidence just because the schema requires an entry for that family - a low score with no evidence is \
a completely normal, expected, and correct answer for an irrelevant family. You are NOT deciding \
whether a pattern is "emerging" or "established" - that label is derived later from your score.

11. HYPOTHESIS SCORECARD: the same principle applies to hypotheses. You must score EVERY one of the \
six canonical hypothesis families - adjustment_reaction, complicated_grief_pattern, \
attachment_insecurity_pattern, substance_use_vulnerability, identity_disruption_pattern, and \
resilient_trajectory - every time, not a chosen subset. For each, give evidence_strength (0.0-1.0), \
confidence, supporting_evidence, contradicting_evidence, and competing_explanations. A family that \
doesn't fit this life at all gets a low evidence_strength and empty supporting_evidence - never \
manufactured evidence, never omission. These remain developmental-pattern-level constructs only - \
never reach for a diagnosis name in competing_explanations either.

12. ATTACHMENT: you output attachment_anxiety, attachment_avoidance, and relational_security as \
evidence-bound dimensions, for baseline and current separately, exactly as you would score any other \
dimension. You do NOT choose a categorical attachment style anywhere - there is no style field for \
you to fill in. Score the three dimensions as honestly and independently as you can from the actual \
evidence; the categorical style is derived from your dimension scores afterward, not asserted by you.

Return ONLY the structured JSON object matching the provided schema. No prose outside the schema."""


@dataclass
class FormulationCallError(Exception):
    message: str
    raw_output: Optional[str] = None


@dataclass
class FormulationResult:
    final: WholeLifeFormulation
    raw_model_output: ModelWholeLifeFormulation
    model_id: str


def _client() -> openai.OpenAI:
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    if not api_key:
        raise FormulationCallError("OpenAI API key is not configured.")
    http_client = httpx.Client(
        timeout=httpx.Timeout(connect=5.0, read=600.0, write=600.0, pool=600.0),
    )
    return openai.OpenAI(api_key=api_key, http_client=http_client)


def generate_whole_life_formulation(
    request: WholeLifeFormulationRequest,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
) -> FormulationResult:
    """
    One evidence-bound whole-life formulation call, followed by deterministic
    derivation (pattern status from relevance_score, attachment style from
    dimensions). Raises FormulationCallError on any failure - callers own
    retry policy (design doc: one automatic retry then hard-fail; the
    harness implements that, not this function).
    """
    client = _client()
    schema = strict_json_schema(ModelWholeLifeFormulation)

    try:
        response = client.responses.create(
            model=FORMULATION_MODEL,
            instructions=SYSTEM_INSTRUCTIONS,
            input=request.prompt_input,
            reasoning={"effort": reasoning_effort},
            max_output_tokens=max_output_tokens,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "model_whole_life_formulation",
                    "schema": schema,
                    "strict": True,
                }
            },
        )
    except Exception as exc:  # noqa: BLE001 - surfacing any API failure uniformly for the harness
        raise FormulationCallError(f"OpenAI call failed: {exc}") from exc

    output_text = response.output_text
    if not output_text:
        raise FormulationCallError("Empty output_text from model", raw_output=None)

    try:
        parsed_json = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise FormulationCallError(f"Output was not valid JSON: {exc}", raw_output=output_text) from exc

    try:
        model_formulation = ModelWholeLifeFormulation.model_validate(parsed_json)
    except Exception as exc:  # noqa: BLE001
        raise FormulationCallError(f"Output did not match schema: {exc}", raw_output=output_text) from exc

    # --- deterministic derivation (v2.2: both scorecards now fixed-coverage) ---
    life = request.life
    developmental_patterns = derive_pattern_projection(model_formulation.pattern_scorecard, life)
    hypotheses = derive_hypothesis_projection(model_formulation.hypothesis_scorecard)
    baseline_attachment = derive_attachment_profile(model_formulation.baseline_attachment)
    current_attachment = derive_attachment_profile(model_formulation.current_attachment)

    final = WholeLifeFormulation(
        schema_version=FORMULATION_SCHEMA_VERSION,
        baseline_personality=model_formulation.baseline_personality,
        current_personality=model_formulation.current_personality,
        personality_deltas=model_formulation.personality_deltas,
        baseline_attachment=baseline_attachment,
        current_attachment=current_attachment,
        attachment_trajectory=model_formulation.attachment_trajectory,
        current_state=model_formulation.current_state,
        developmental_patterns=developmental_patterns,
        beliefs=model_formulation.beliefs,
        protective_factors=model_formulation.protective_factors,
        causal_chains=model_formulation.causal_chains,
        hypotheses=hypotheses,
        contradictions=model_formulation.contradictions,
        unresolved_questions=model_formulation.unresolved_questions,
        change_points=model_formulation.change_points,
        overall_confidence=model_formulation.overall_confidence,
    )

    usage = response.usage
    logger.info(
        "whole_life_formulation call complete model=%s input_tokens=%s output_tokens=%s reasoning_tokens=%s "
        "patterns_shown=%s/10 hypotheses_shown=%s/6",
        response.model,
        getattr(usage, "input_tokens", None),
        getattr(usage, "output_tokens", None),
        getattr(getattr(usage, "output_tokens_details", None), "reasoning_tokens", None),
        len(developmental_patterns),
        len(hypotheses),
    )
    return FormulationResult(final=final, raw_model_output=model_formulation, model_id=response.model)
