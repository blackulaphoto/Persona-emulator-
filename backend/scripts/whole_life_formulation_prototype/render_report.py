"""Render saved harness result JSON into human-readable markdown for the Phase 0 report."""
import json
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _cite(c):
    if c.get("experience_id"):
        return f'exp:{c["experience_id"]} (subject={c["subject_role"]})'
    if c.get("intervention_id"):
        return f'intervention:{c["intervention_id"]} (subject={c["subject_role"]})'
    if c.get("background_span"):
        return f'bg:"{c["background_span"][:70]}" (subject={c["subject_role"]})'
    return "NO CITATION"


def render_formulation(f: dict, title: str) -> str:
    out = [f"### {title}", ""]

    out.append("**BIG FIVE**")
    out.append("")
    out.append("| Trait | Baseline | Current | Confidence (base/cur) |")
    out.append("|---|---|---|---|")
    for trait in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"):
        b = f["baseline_personality"][trait]
        c = f["current_personality"][trait]
        out.append(f"| {trait} | {b['value']:.2f} | {c['value']:.2f} | {b['confidence']:.2f} / {c['confidence']:.2f} |")
    out.append("")
    for d in f["personality_deltas"]:
        ev = "; ".join(_cite(c) for c in d["evidence"])
        out.append(f"- **{d['trait']}** {d['direction']} ({d['magnitude']}): {d['from_value']:.2f}→{d['to_value']:.2f} — {d['reasoning']} [{ev}]")
    out.append("")

    out.append("**ATTACHMENT** (style is code-derived from the anxiety/avoidance/relational_security dimensions - see derivation.py)")
    out.append("")
    ba, ca = f["baseline_attachment"], f["current_attachment"]
    out.append(f"- Baseline style (derived): **{ba['style']}** (conf {ba['style_confidence']:.2f}) — {'; '.join(_cite(c) for c in ba['style_evidence'])}")
    out.append(f"- Current style (derived): **{ca['style']}** (conf {ca['style_confidence']:.2f}) — {'; '.join(_cite(c) for c in ca['style_evidence'])}")
    for dim in ("attachment_anxiety", "attachment_avoidance", "relational_security"):
        out.append(f"  - {dim}: {ba[dim]['value']:.2f} → {ca[dim]['value']:.2f}")
    for t in f["attachment_trajectory"]:
        out.append(f"- Trajectory: *{t['period_label']}* — {t['direction']}: {t['reasoning']} [{'; '.join(_cite(c) for c in t['evidence'])}]")
    out.append("")

    out.append("**CURRENT STATE**")
    out.append("")
    for dim in ("trust", "threat_sensitivity", "mood", "regulation", "avoidance", "relational_security"):
        s = f["current_state"][dim]
        out.append(f"- {dim}: {s['value']:.2f} (conf {s['confidence']:.2f}) — {'; '.join(_cite(c) for c in s['evidence'])}")
    out.append("")

    out.append("**DEVELOPMENTAL PATTERNS** (status/first-emerged are code-derived from relevance_score - see derivation.py)")
    out.append("")
    for p in f["developmental_patterns"]:
        out.append(f"- **[{p['canonical_family']}]** {p['human_label']} — status={p['status']} (derived), "
                    f"relevance_score={p['relevance_score']:.2f}, confidence={p['confidence']:.2f}")
        out.append(f"  - first emerged (derived, earliest dated citation): {_cite(p['first_emerged']) if p['first_emerged'] else '(undated)'}")
        out.append(f"  - supporting evidence: {'; '.join(_cite(c) for c in p['supporting_evidence']) or '(none)'}")
        out.append(f"  - contradicting evidence: {'; '.join(_cite(c) for c in p['contradicting_evidence']) or '(none)'}")
        out.append(f"  - reasoning: {p['reasoning']}")
    out.append("")

    out.append("**BELIEFS**")
    out.append("")
    for b in f["beliefs"]:
        out.append(f"- {b['human_label']}: \"{b['belief_statement']}\" (conf {b['confidence']:.2f})")
        out.append(f"  - formed from: {'; '.join(_cite(c) for c in b['formed_from'])}")
        if b["restated_by"]:
            out.append(f"  - restated by: {'; '.join(_cite(c) for c in b['restated_by'])}")
    out.append("")

    out.append("**PROTECTIVE FACTORS**")
    out.append("")
    for pf in f["protective_factors"]:
        out.append(f"- **[{pf['canonical_family']}]** {pf['human_label']} (conf {pf['confidence']:.2f})")
        out.append(f"  - domains buffered: {', '.join(pf['domains_buffered'])}")
        out.append(f"  - active from: {_cite(pf['active_from'])}; to: {_cite(pf['active_to']) if pf['active_to'] else '(ongoing)'}")
    out.append("")

    out.append("**CAUSAL CHAINS**")
    out.append("")
    for c in f["causal_chains"]:
        out.append(f"- {c['description']} (conf {c['confidence']:.2f})")
        for step in c["steps"]:
            out.append(f"  - {_cite(step['event_citation'])} → {step['mechanism']}")
    out.append("")

    out.append("**HYPOTHESES** (status/human_label/reasoning are code-derived from evidence_strength - see derivation.py)")
    out.append("")
    for h in f["hypotheses"]:
        out.append(f"- **[{h['canonical_family']}]** {h['human_label']} — status={h['status']} (derived), strength={h['evidence_strength']:.2f}")
        out.append(f"  - supporting: {'; '.join(_cite(c) for c in h['supporting_evidence']) or '(none)'}")
        out.append(f"  - contradicting: {'; '.join(_cite(c) for c in h['contradicting_evidence']) or '(none)'}")
        out.append(f"  - competing explanations: {'; '.join(h['competing_explanations']) or '(none)'}")
        out.append(f"  - reasoning: {h['reasoning']}")
    out.append("")

    out.append("**CONTRADICTIONS**")
    out.append("")
    for c in f["contradictions"]:
        out.append(f"- {c['description']} (involves: {', '.join(c['involved_claim_ids'])})")
    out.append("")

    out.append("**UNRESOLVED QUESTIONS**")
    out.append("")
    for q in f["unresolved_questions"]:
        out.append(f"- {q}")
    out.append("")

    out.append("**SPARSE CHANGE POINTS**")
    out.append("")
    for cp in sorted(f["change_points"], key=lambda x: x["age"]):
        parts = []
        for pc in cp["personality_changes"]:
            parts.append(f"{pc['trait']} {pc['direction']} ({pc['magnitude']})")
        for ac in cp["attachment_changes"]:
            parts.append(f"attachment.{ac['dimension']} {ac['direction']} ({ac['magnitude']})")
        for sc in cp["state_changes"]:
            parts.append(f"state.{sc['dimension']} {sc['direction']} ({sc['magnitude']})")
        out.append(f"- age {cp['age']} [{cp['experience_id']}]: {'; '.join(parts)} — {cp['reasoning']}")
    out.append("")
    out.append(f"**Overall confidence:** {f['overall_confidence']:.2f}")
    out.append("")
    return "\n".join(out)


def load(fixture, run):
    with open(RESULTS_DIR / f"{fixture}_run{run}.json", encoding="utf-8") as fh:
        return json.load(fh)


if __name__ == "__main__":
    import sys
    fixture = sys.argv[1] if len(sys.argv) > 1 else "brandon"
    run = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    d = load(fixture, run)
    print(render_formulation(d["formulation"], f"{fixture} run {run} ({d['elapsed_seconds']}s)"))
