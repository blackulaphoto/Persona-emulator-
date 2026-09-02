"""
v2.2 final shadow stability pass harness.

Same 20-call structure (5 runs x {brandon, complex, mixed, low_adversity}),
same validators, same regression checks. What's new: both pattern_scorecard
and hypothesis_scorecard are now FIXED-coverage (every canonical family
present every run, by schema construction), so "family presence frequency"
for the pre-threshold scorecard is trivially 5/5 always - the harness
verifies that directly as proof the structural fix worked, and measures
score variance/Jaccard/flicker for both patterns AND hypotheses (v2.1 only
had the pattern-side metrics). Nothing here touches the database.

Usage:
    python run_harness.py [--runs 5] [--fixtures brandon,complex,mixed,low_adversity]
"""
import argparse
import concurrent.futures
import json
import statistics
import sys
import time
from dataclasses import asdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # backend/
sys.path.insert(0, str(Path(__file__).resolve().parent))       # this dir, for fixtures.py

from app.services.whole_life_formulation.derivation import HYPOTHESIS_FAMILY_FIELDS, PATTERN_FAMILY_FIELDS
from app.services.whole_life_formulation.request_assembler import assemble_request
from app.services.whole_life_formulation.formulation_service import (
    generate_whole_life_formulation, FormulationCallError,
)
from app.services.whole_life_formulation.validators import validate_formulation
from fixtures import ALL_FIXTURES, BRANDON_SELF_EVENT_IDS
from regression_checks import check_no_diagnosis_language, run_regression_checks

RESULTS_DIR = Path(__file__).resolve().parent / "results"
BIG_FIVE_TOLERANCE = 0.15
ATTACHMENT_DIM_TOLERANCE = 0.15
ATTACHMENT_STYLE_MIN_MODE_FRACTION = 0.8  # 4 of 5
PATTERN_FAMILY_JACCARD_MIN = 0.8
EVIDENCE_OVERLAP_JACCARD_MIN = 0.7
HYPOTHESIS_FLICKER_MAX = 0.2

SELF_EVENT_IDS_BY_FIXTURE = {
    "brandon": BRANDON_SELF_EVENT_IDS,
}


def _one_run(fixture_name: str, life, run_index: int, max_retries: int = 1):
    request = assemble_request(life)
    t0 = time.time()
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            result = generate_whole_life_formulation(request, reasoning_effort="medium", max_output_tokens=16000)
            elapsed = time.time() - t0
            validation = validate_formulation(result.final, life)
            self_ids = SELF_EVENT_IDS_BY_FIXTURE.get(fixture_name, set())
            regression = run_regression_checks(result.final, life, self_ids)
            diagnosis_leaks = check_no_diagnosis_language(result.final)
            return {
                "fixture": fixture_name,
                "run_index": run_index,
                "elapsed_seconds": round(elapsed, 1),
                "status": "ok",
                "formulation": result.final.model_dump(),
                "pattern_scorecard_raw": result.raw_model_output.pattern_scorecard.model_dump(),
                "hypothesis_scorecard_raw": result.raw_model_output.hypothesis_scorecard.model_dump(),
                "validation_findings": [asdict(f) for f in validation.findings],
                "regression_findings": [asdict(f) for f in regression.findings],
                "diagnosis_leak_findings": [asdict(f) for f in diagnosis_leaks],
            }
        except FormulationCallError as e:
            last_error = e
            continue
    return {
        "fixture": fixture_name,
        "run_index": run_index,
        "elapsed_seconds": round(time.time() - t0, 1),
        "status": "failed",
        "error": last_error.message if last_error else "unknown",
        "raw_output": (last_error.raw_output[:3000] if last_error and last_error.raw_output else None),
    }


def run_all(fixture_names, n_runs: int, max_workers: int = 6):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {}
        for fixture_name in fixture_names:
            life = ALL_FIXTURES[fixture_name]
            for run_index in range(n_runs):
                fut = pool.submit(_one_run, fixture_name, life, run_index)
                futures[fut] = (fixture_name, run_index)

        for fut in concurrent.futures.as_completed(futures):
            fixture_name, run_index = futures[fut]
            result = fut.result()
            out_path = RESULTS_DIR / f"{fixture_name}_run{run_index}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"[{result['status']}] {fixture_name} run {run_index} in {result['elapsed_seconds']}s -> {out_path}", flush=True)
            jobs.append(result)
    return jobs


# ---------------------------------------------------------------------------
# Repeatability metrics
# ---------------------------------------------------------------------------

def _big_five_max_diff(runs, profile_key):
    diffs = {}
    for trait in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"):
        values = [r["formulation"][profile_key][trait]["value"] for r in runs if r["status"] == "ok"]
        if len(values) < 2:
            diffs[trait] = None
            continue
        diffs[trait] = max(abs(a - b) for a, b in combinations(values, 2))
    return diffs


def _attachment_style_agreement(runs, profile_key):
    styles = [r["formulation"][profile_key]["style"] for r in runs if r["status"] == "ok"]
    if not styles:
        return {"styles": [], "mode": None, "mode_fraction": 0.0}
    mode = max(set(styles), key=styles.count)
    return {"styles": styles, "mode": mode, "mode_fraction": styles.count(mode) / len(styles)}


def _attachment_dim_max_diff(runs, profile_key):
    diffs = {}
    for dim in ("attachment_anxiety", "attachment_avoidance", "relational_security"):
        values = [r["formulation"][profile_key][dim]["value"] for r in runs if r["status"] == "ok"]
        if len(values) < 2:
            diffs[dim] = None
            continue
        diffs[dim] = max(abs(a - b) for a, b in combinations(values, 2))
    return diffs


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _scorecard_presence_frequency(runs, raw_key: str, family_fields):
    """
    Proof the structural fix worked: every family should be present in the
    RAW scorecard in 5/5 runs, always - there is no longer a way for the
    model to omit a family from the scorecard the way v2.1's variable-length
    candidate list allowed. This is the direct measurement of "candidate-
    generation completeness."
    """
    ok_runs = [r for r in runs if r["status"] == "ok"]
    n = len(ok_runs)
    presence = {fam: 0 for fam in family_fields}
    for r in ok_runs:
        for fam in family_fields:
            if fam in r[raw_key]:
                presence[fam] += 1
    return {"n_runs": n, "presence": presence, "always_present": all(v == n for v in presence.values())}


def _family_score_variance(runs, raw_key: str, family_fields, score_field: str):
    ok_runs = [r for r in runs if r["status"] == "ok"]
    per_family = {}
    for fam in family_fields:
        scores = [r[raw_key][fam][score_field] for r in ok_runs if fam in r[raw_key]]
        entry = {"n_runs_scored": len(scores), "mean": round(sum(scores) / len(scores), 3) if scores else None}
        if len(scores) >= 2:
            entry["stdev"] = round(statistics.stdev(scores), 3)
        per_family[fam] = entry
    stdevs = [v["stdev"] for v in per_family.values() if "stdev" in v]
    avg_stdev = round(sum(stdevs) / len(stdevs), 3) if stdevs else None
    return {"per_family": per_family, "avg_stdev": avg_stdev}


def _post_threshold_jaccard(runs, output_list_key: str, status_field: str, shown_statuses):
    family_sets = []
    for r in runs:
        if r["status"] != "ok":
            continue
        families = {item["canonical_family"] for item in r["formulation"][output_list_key] if item[status_field] in shown_statuses}
        family_sets.append(families)
    if len(family_sets) < 2:
        return {"pairwise": [], "min": None, "avg": None}
    pairwise = [_jaccard(a, b) for a, b in combinations(family_sets, 2)]
    return {"pairwise": [round(x, 2) for x in pairwise], "min": round(min(pairwise), 2), "avg": round(sum(pairwise) / len(pairwise), 2)}


def _post_threshold_presence_frequency(runs, output_list_key: str):
    ok_runs = [r for r in runs if r["status"] == "ok"]
    n = len(ok_runs)
    presence = {}
    for r in ok_runs:
        for item in r["formulation"][output_list_key]:
            fam = item["canonical_family"]
            presence[fam] = presence.get(fam, 0) + 1
    return {"n_runs": n, "presence": presence}


def _hypothesis_flicker(runs):
    ok_runs = [r for r in runs if r["status"] == "ok"]
    n = len(ok_runs)
    if n == 0:
        return {"presence_counts": {}, "flickering": {}, "flicker_rate": None}
    presence = {}
    for r in ok_runs:
        seen = {h["canonical_family"] for h in r["formulation"]["hypotheses"]}
        for fam in seen:
            presence[fam] = presence.get(fam, 0) + 1
    flickering = {fam: cnt for fam, cnt in presence.items() if not (cnt >= max(n - 1, 1) or cnt <= 1)}
    rate = len(flickering) / len(presence) if presence else 0.0
    return {"presence_counts": presence, "flickering": flickering, "flicker_rate": round(rate, 2)}


def _evidence_overlap(runs, output_list_key: str):
    ok_runs = [r for r in runs if r["status"] == "ok"]
    n = len(ok_runs)
    if n < 2:
        return {"per_family": {}, "avg": None}
    family_evidence = {}
    for r in ok_runs:
        for item in r["formulation"][output_list_key]:
            fam = item["canonical_family"]
            ids = {c["experience_id"] for c in item["supporting_evidence"] if c.get("experience_id")}
            family_evidence.setdefault(fam, []).append(ids)
    per_family = {}
    for fam, sets_ in family_evidence.items():
        if len(sets_) < max(n - 1, 2):
            continue
        pairwise = [_jaccard(a, b) for a, b in combinations(sets_, 2)]
        if pairwise:
            per_family[fam] = round(sum(pairwise) / len(pairwise), 2)
    avg = round(sum(per_family.values()) / len(per_family), 2) if per_family else None
    return {"per_family": per_family, "avg": avg}


def _zero_tolerance(runs):
    unsupported = 0
    actor_confusion = 0
    diagnosis_leaks = 0
    for r in runs:
        if r["status"] != "ok":
            continue
        for f in r["validation_findings"]:
            if f["rule_violated"] in ("citation_existence", "background_span_existence"):
                unsupported += 1
        for f in r["regression_findings"]:
            if f["check"].startswith("caregiver_self_confusion"):
                actor_confusion += 1
        diagnosis_leaks += len(r.get("diagnosis_leak_findings", []))
    return {
        "unsupported_fact_rejections": unsupported,
        "actor_confusion_findings": actor_confusion,
        "diagnosis_language_leaks": diagnosis_leaks,
    }


def compute_repeatability(runs_for_fixture):
    return {
        "n_ok": sum(1 for r in runs_for_fixture if r["status"] == "ok"),
        "n_failed": sum(1 for r in runs_for_fixture if r["status"] != "ok"),
        "big_five_baseline_max_diff": _big_five_max_diff(runs_for_fixture, "baseline_personality"),
        "big_five_current_max_diff": _big_five_max_diff(runs_for_fixture, "current_personality"),
        "attachment_style_current_derived": _attachment_style_agreement(runs_for_fixture, "current_attachment"),
        "attachment_dims_current_max_diff": _attachment_dim_max_diff(runs_for_fixture, "current_attachment"),
        "pattern_scorecard_presence_frequency": _scorecard_presence_frequency(
            runs_for_fixture, "pattern_scorecard_raw", PATTERN_FAMILY_FIELDS),
        "pattern_family_score_variance": _family_score_variance(
            runs_for_fixture, "pattern_scorecard_raw", PATTERN_FAMILY_FIELDS, "relevance_score"),
        "pattern_family_jaccard_post_threshold": _post_threshold_jaccard(
            runs_for_fixture, "developmental_patterns", "status", {"emerging", "established", "historically_weakened"}),
        "pattern_family_presence_post_threshold": _post_threshold_presence_frequency(runs_for_fixture, "developmental_patterns"),
        "hypothesis_scorecard_presence_frequency": _scorecard_presence_frequency(
            runs_for_fixture, "hypothesis_scorecard_raw", HYPOTHESIS_FAMILY_FIELDS),
        "hypothesis_family_score_variance": _family_score_variance(
            runs_for_fixture, "hypothesis_scorecard_raw", HYPOTHESIS_FAMILY_FIELDS, "evidence_strength"),
        "hypothesis_family_jaccard_post_threshold": _post_threshold_jaccard(
            runs_for_fixture, "hypotheses", "status", {"candidate", "supported", "contradicted"}),
        "hypothesis_flicker": _hypothesis_flicker(runs_for_fixture),
        "pattern_evidence_overlap": _evidence_overlap(runs_for_fixture, "developmental_patterns"),
        "hypothesis_evidence_overlap": _evidence_overlap(runs_for_fixture, "hypotheses"),
        "zero_tolerance": _zero_tolerance(runs_for_fixture),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--fixtures", type=str, default="brandon,complex,mixed,low_adversity")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    fixture_names = args.fixtures.split(",")
    all_results = run_all(fixture_names, args.runs, max_workers=args.workers)

    summary = {}
    for fixture_name in fixture_names:
        runs_for_fixture = [r for r in all_results if r["fixture"] == fixture_name]
        runs_for_fixture.sort(key=lambda r: r["run_index"])
        summary[fixture_name] = compute_repeatability(runs_for_fixture)

    summary_path = RESULTS_DIR / "repeatability_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("\n=== SUMMARY WRITTEN TO", summary_path, "===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
