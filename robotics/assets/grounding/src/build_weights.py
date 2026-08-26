"""Build conserved source-activity weights from the canonical tables.

The output is an allocation model, not a claim that O*NET task ratings measure
labor time. OEWS values remain unique economic pots. Conditional shares are
normalized at every bridge: OEWS unit -> 2018 SOC -> O*NET occupation -> task.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import build_canonical as canonical


GROUNDING_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ROOT = GROUNDING_ROOT / "data" / "derived" / "canonical_v2"
DEFAULT_OUTPUT = GROUNDING_ROOT / "data" / "derived" / "weights_v2"
VARIANTS = (
    "uniform",
    "relevance_importance",
    "relevance_frequency_ordinal",
    "combined_ordinal",
    "combined_frequency_events_conservative",
    "combined_frequency_events_central",
    "combined_frequency_events_aggressive",
)
CENTRAL_VARIANT = "combined_ordinal"
FREQUENCY_ANCHORS = {
    # Assumed representative task events per 250-day work year. These are
    # sensitivity mappings, not O*NET measurements. Open-ended categories 1
    # and 7 necessarily require declared endpoints.
    "conservative": (0.1, 1.01, 12.01, 52.01, 250.0, 500.0, 2000.0),
    "central": (0.5, math.sqrt(12.0), math.sqrt(12.0 * 52.0), math.sqrt(52.0 * 250.0), 250.0, 1000.0, 4000.0),
    "aggressive": (1.0, 12.0, 52.0, 249.0, 499.0, 1999.0, 8000.0),
}


class WeightError(RuntimeError):
    """Raised when a weighting assumption or conservation invariant fails."""


def read_csv(relative: str) -> list[dict[str, str]]:
    path = CANONICAL_ROOT / relative
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise WeightError(f"expected numeric value, got {value!r}") from exc


def fmt(value: float | None) -> str:
    return canonical.format_number(value, 16)


def close(left: float, right: float, *, relative: float = 1e-10, absolute: float = 1e-4) -> bool:
    return math.isclose(left, right, rel_tol=relative, abs_tol=absolute)


def macro_values() -> dict[str, float]:
    rows = read_csv("market_work/bea_nipa_table_1_10_2025.csv")
    by_line = {row["line_number"]: float(row["value_billions_usd"]) * 1e9 for row in rows}
    required = {"1", "2", "3"}
    if not required <= set(by_line):
        raise WeightError("BEA NIPA Table 1.10 lacks required lines 1-3")
    gdi = by_line["1"]
    compensation = by_line["2"]
    wages = by_line["3"]
    if not 0 < wages < compensation < gdi:
        raise WeightError("BEA macro anchors have an unexpected ordering")
    return {
        "gross_domestic_income_usd": gdi,
        "compensation_usd": compensation,
        "wages_and_salaries_usd": wages,
        "compensation_to_wages_factor": compensation / wages,
        "gdi_to_compensation_factor": gdi / compensation,
        "gdi_to_wages_factor": gdi / wages,
    }


def build_economic_units(
    catalog: canonical.OutputCatalog,
    macro: dict[str, float],
) -> tuple[list[dict[str, str]], dict[str, float | None]]:
    source_rows = read_csv("market_work/oews_national_may_2025.csv")
    rows: list[dict[str, str]] = []
    values: dict[str, float | None] = {}
    for source in source_rows:
        wage_bill = as_float(source["annual_wage_bill_usd"])
        economic_value = wage_bill * macro["gdi_to_wages_factor"] if wage_bill is not None else None
        code = source["oews_occupation_code"]
        values[code] = economic_value
        rows.append(
            {
                "economic_unit_uid": f"oews-economic:may-2025:{code}",
                "source_release": "May 2025 OEWS + BEA NIPA Table 1.10 annual 2025",
                "oews_occupation_code": code,
                "oews_occupation_title": source["oews_occupation_title"],
                "employment": source["employment"],
                "annual_mean_wage_usd": source["annual_mean_wage_usd"],
                "annual_wage_bill_usd": source["annual_wage_bill_usd"],
                "compensation_to_wages_factor": fmt(macro["compensation_to_wages_factor"]),
                "gdi_to_compensation_factor": fmt(macro["gdi_to_compensation_factor"]),
                "gdi_to_wages_factor": fmt(macro["gdi_to_wages_factor"]),
                "economic_value_usd": fmt(economic_value),
                "economic_value_status": "available" if economic_value is not None else "unavailable_suppressed_annual_wage",
                "allocation_model": "employment_times_annual_mean_wage_times_BEA_GDI_to_wages_ratio",
            }
        )
    if len(rows) != 830 or len(values) != 830:
        raise WeightError("expected exactly 830 OEWS economic units")
    fields = list(rows[0])
    catalog.write_csv(
        "market_work/oews_economic_units.csv",
        fields,
        rows,
        primary_key=["economic_unit_uid"],
        origins={field: canonical.ORIGIN_DERIVED for field in fields},
    )
    return rows, values


def build_occupation_allocations(
    catalog: canonical.OutputCatalog,
    economic_values: dict[str, float | None],
) -> tuple[list[dict[str, str]], dict[str, float | None]]:
    mappings = read_csv("market_work/onet_oews_mapping.csv")
    occupations = {row["onet_soc_code"]: row for row in read_csv("market_work/onet_occupations.csv")}
    mapped_by_target: dict[str, list[dict[str, str]]] = defaultdict(list)
    for mapping in mappings:
        if mapping["oews_occupation_code"]:
            mapped_by_target[mapping["oews_occupation_code"]].append(mapping)
    if set(mapped_by_target) != set(economic_values):
        raise WeightError("O*NET mappings do not cover every OEWS economic unit")

    rows: list[dict[str, str]] = []
    occupation_values: dict[str, float | None] = {}
    for mapping in mappings:
        onet_code = mapping["onet_soc_code"]
        target = mapping["oews_occupation_code"]
        if target:
            target_rows = mapped_by_target[target]
            soc_codes = sorted({row["soc_2018_code"] for row in target_rows})
            onet_within_soc = [row for row in target_rows if row["soc_2018_code"] == mapping["soc_2018_code"]]
            oews_to_soc_share = 1.0 / len(soc_codes)
            soc_to_onet_share = 1.0 / len(onet_within_soc)
            conditional_share = oews_to_soc_share * soc_to_onet_share
            target_value = economic_values[target]
            occupation_value = target_value * conditional_share if target_value is not None else None
            status = "allocated" if occupation_value is not None else "oews_value_unavailable"
        else:
            oews_to_soc_share = None
            soc_to_onet_share = None
            conditional_share = None
            occupation_value = None
            status = mapping["mapping_status"]
        occupation_values[onet_code] = occupation_value
        rows.append(
            {
                "occupation_allocation_uid": f"onet-economic:30.3:{onet_code}",
                "source_release": "O*NET 30.3 + May 2025 OEWS + BEA NIPA 2025",
                "onet_soc_code": onet_code,
                "occupation_title": occupations[onet_code]["title"],
                "major_occupation_group": onet_code[:2] + "-0000",
                "soc_2018_code": mapping["soc_2018_code"],
                "oews_occupation_code": target,
                "mapping_status": mapping["mapping_status"],
                "oews_to_soc_equal_share": fmt(oews_to_soc_share),
                "soc_to_onet_equal_share": fmt(soc_to_onet_share),
                "conditional_share_within_oews_unit": fmt(conditional_share),
                "occupation_economic_value_usd": fmt(occupation_value),
                "economic_value_status": status,
                "allocation_assumption": "equal across constituent SOCs, then equal across O*NET extensions within SOC" if target else "no allocation",
            }
        )
    if len(rows) != 1016 or len(occupation_values) != 1016:
        raise WeightError("occupation allocation did not retain all 1,016 O*NET occupations")
    for target, target_rows in mapped_by_target.items():
        shares = [
            float(row["conditional_share_within_oews_unit"])
            for row in rows
            if row["oews_occupation_code"] == target
        ]
        if not close(sum(shares), 1.0, absolute=1e-12):
            raise WeightError(f"O*NET conditional shares do not sum to one for {target}")
        target_value = economic_values[target]
        if target_value is not None:
            allocated = sum(
                float(row["occupation_economic_value_usd"])
                for row in rows
                if row["oews_occupation_code"] == target and row["occupation_economic_value_usd"]
            )
            if not close(allocated, target_value):
                raise WeightError(f"occupation allocation does not conserve {target}")
    fields = list(rows[0])
    catalog.write_csv(
        "market_work/onet_occupation_allocations.csv",
        fields,
        rows,
        primary_key=["occupation_allocation_uid"],
        origins={field: canonical.ORIGIN_DERIVED for field in fields},
    )
    return rows, occupation_values


def source_task_scores(task: Mapping[str, str]) -> dict[str, float | None]:
    if task["ratings_available"] != "true":
        return {variant: (1.0 if variant == "uniform" else None) for variant in VARIANTS}
    importance = as_float(task["importance_value"])
    relevance = as_float(task["relevance_value"])
    if importance is None or relevance is None or not task["frequency_distribution_json"]:
        raise WeightError(f"rated task {task['task_uid']} lacks a required rating")
    distribution = json.loads(task["frequency_distribution_json"])
    if set(distribution) != {str(index) for index in range(1, 8)}:
        raise WeightError(f"rated task {task['task_uid']} lacks seven frequency categories")
    frequency_expected = sum(int(category) * float(percent) / 100.0 for category, percent in distribution.items())
    importance_normalized = importance / 5.0
    relevance_fraction = relevance / 100.0
    frequency_normalized = frequency_expected / 7.0
    scores = {
        "uniform": 1.0,
        "relevance_importance": relevance_fraction * importance_normalized,
        "relevance_frequency_ordinal": relevance_fraction * frequency_normalized,
        "combined_ordinal": relevance_fraction * importance_normalized * frequency_normalized,
    }
    for anchor_name, anchors in FREQUENCY_ANCHORS.items():
        expected_events = sum(
            float(percent) / 100.0 * anchors[int(category) - 1]
            for category, percent in distribution.items()
        )
        scores[f"combined_frequency_events_{anchor_name}"] = (
            relevance_fraction * importance_normalized * expected_events
        )
    return scores


def build_task_allocations(
    catalog: canonical.OutputCatalog,
    occupation_rows: list[dict[str, str]],
    occupation_values: dict[str, float | None],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    tasks = read_csv("market_work/onet_tasks.csv")
    mapping_by_onet = {row["onet_soc_code"]: row for row in occupation_rows}
    by_occupation: dict[str, list[dict[str, str]]] = defaultdict(list)
    for task in tasks:
        by_occupation[task["onet_soc_code"]].append(task)

    score_by_uid = {task["task_uid"]: source_task_scores(task) for task in tasks}
    effective_scores: dict[str, dict[str, float]] = {}
    imputation_status: dict[str, str] = {}
    for onet_code, occupation_tasks in by_occupation.items():
        rated = [task for task in occupation_tasks if task["ratings_available"] == "true"]
        for variant in VARIANTS:
            observed = [score_by_uid[task["task_uid"]][variant] for task in rated]
            observed_values = [float(value) for value in observed if value is not None]
            if variant == "uniform":
                replacement = 1.0
            elif observed_values:
                replacement = statistics.median(observed_values)
            else:
                replacement = 1.0
            for task in occupation_tasks:
                uid = task["task_uid"]
                effective_scores.setdefault(uid, {})[variant] = (
                    float(score_by_uid[uid][variant])
                    if score_by_uid[uid][variant] is not None
                    else replacement
                )
        if not rated:
            for task in occupation_tasks:
                imputation_status[task["task_uid"]] = "uniform_all_task_ratings_missing"
        else:
            for task in occupation_tasks:
                imputation_status[task["task_uid"]] = (
                    "source_ratings" if task["ratings_available"] == "true" else "occupation_median_score_imputation"
                )

    denominators: dict[str, dict[str, float]] = defaultdict(dict)
    for onet_code, occupation_tasks in by_occupation.items():
        for variant in VARIANTS:
            total = sum(effective_scores[task["task_uid"]][variant] for task in occupation_tasks)
            if total <= 0:
                raise WeightError(f"nonpositive task-score denominator for {onet_code}/{variant}")
            denominators[onet_code][variant] = total

    rows: list[dict[str, str]] = []
    for task in tasks:
        uid = task["task_uid"]
        onet_code = task["onet_soc_code"]
        mapping = mapping_by_onet[onet_code]
        distribution = json.loads(task["frequency_distribution_json"]) if task["frequency_distribution_json"] else {}
        frequency_expected = (
            sum(int(category) * float(percent) / 100.0 for category, percent in distribution.items())
            if distribution
            else None
        )
        expected_events = {
            anchor_name: (
                sum(
                    float(percent) / 100.0 * anchors[int(category) - 1]
                    for category, percent in distribution.items()
                )
                if distribution
                else None
            )
            for anchor_name, anchors in FREQUENCY_ANCHORS.items()
        }
        occupation_value = occupation_values[onet_code]
        row = {
            "task_allocation_uid": f"onet-task-economic:30.3:{onet_code}:{task['task_id']}",
            "task_uid": uid,
            "source_release": "O*NET 30.3 + May 2025 OEWS + BEA NIPA 2025",
            "major_occupation_group": onet_code[:2] + "-0000",
            "onet_soc_code": onet_code,
            "occupation_title": mapping["occupation_title"],
            "task_id": task["task_id"],
            "task_text": task["task_text"],
            "task_type": task["task_type"],
            "oews_occupation_code": mapping["oews_occupation_code"],
            "occupation_mapping_status": mapping["mapping_status"],
            "ratings_available": task["ratings_available"],
            "rating_imputation_status": imputation_status[uid],
            "rating_suppressed_any": canonical.flag(
                task["importance_recommend_suppress"] == "Y"
                or task["relevance_recommend_suppress"] == "Y"
                or task["frequency_recommend_suppress_any"] == "true"
            ),
            "relevance_fraction": fmt(as_float(task["relevance_value"]) / 100.0) if task["relevance_value"] else "",
            "importance_normalized": fmt(as_float(task["importance_value"]) / 5.0) if task["importance_value"] else "",
            "frequency_expected_ordinal_category": fmt(frequency_expected),
            "frequency_ordinal_normalized": fmt(frequency_expected / 7.0) if frequency_expected is not None else "",
            "frequency_expected_events_conservative": fmt(expected_events["conservative"]),
            "frequency_expected_events_central": fmt(expected_events["central"]),
            "frequency_expected_events_aggressive": fmt(expected_events["aggressive"]),
            "occupation_economic_value_usd": fmt(occupation_value),
        }
        for variant in VARIANTS:
            source_score = score_by_uid[uid][variant]
            effective = effective_scores[uid][variant]
            share = effective / denominators[onet_code][variant]
            row[f"source_score_{variant}"] = fmt(source_score)
            row[f"effective_score_{variant}"] = fmt(effective)
            row[f"task_share_{variant}"] = fmt(share)
            row[f"task_economic_value_usd_{variant}"] = fmt(occupation_value * share if occupation_value is not None else None)
        row["central_weight_variant"] = CENTRAL_VARIANT
        row["task_economic_value_usd"] = row[f"task_economic_value_usd_{CENTRAL_VARIANT}"]
        rows.append(row)

    if len(rows) != 18796:
        raise WeightError("task allocation did not retain all 18,796 source tasks")
    for onet_code, occupation_tasks in by_occupation.items():
        for variant in VARIANTS:
            shares = sum(
                float(row[f"task_share_{variant}"])
                for row in rows
                if row["onet_soc_code"] == onet_code
            )
            if not close(shares, 1.0, absolute=1e-12):
                raise WeightError(f"task shares do not sum to one for {onet_code}/{variant}")
            occupation_value = occupation_values[onet_code]
            if occupation_value is not None:
                allocated = sum(
                    float(row[f"task_economic_value_usd_{variant}"])
                    for row in rows
                    if row["onet_soc_code"] == onet_code
                )
                if not close(allocated, occupation_value):
                    raise WeightError(f"task values do not conserve {onet_code}/{variant}")
    fields = list(rows[0])
    catalog.write_csv(
        "market_work/onet_task_allocations.csv.gz",
        fields,
        rows,
        primary_key=["task_allocation_uid"],
        origins={field: canonical.ORIGIN_DERIVED for field in fields},
    )
    occupations_without_tasks = sorted(set(occupation_values) - set(by_occupation))
    return rows, {
        "task_rows": len(rows),
        "occupations_with_tasks": len(by_occupation),
        "occupations_without_tasks": len(occupations_without_tasks),
        "occupation_codes_without_tasks": occupations_without_tasks,
        "rated_tasks": sum(row["ratings_available"] == "true" for row in rows),
        "unrated_tasks": sum(row["ratings_available"] != "true" for row in rows),
        "central_variant": CENTRAL_VARIANT,
        "sensitivity_variants": list(VARIANTS),
        "frequency_anchor_events_per_work_year": {
            name: list(values) for name, values in FREQUENCY_ANCHORS.items()
        },
    }


def build_atus_weights(catalog: canonical.OutputCatalog) -> list[dict[str, str]]:
    estimates = read_csv("everyday_life/atus_activity_estimates.csv")
    pooled = [row for row in estimates if row["estimate_period"] == "2021-2025 pooled annual average"]
    if len(pooled) != 465:
        raise WeightError("expected 465 pooled ATUS activity estimates")
    rows = [
        {
            "activity_weight_uid": f"atus-population-time:2021-2025:{row['activity_code']}",
            "source_release": "ATUS 2021-2025 pooled annual average",
            "activity_code": row["activity_code"],
            "activity_label": row["activity_label"],
            "first_tier_code": row["first_tier_code"],
            "first_tier_label": row["first_tier_label"],
            "analysis_class": row["analysis_class"],
            "annual_population_hours": row["annual_population_hours"],
            "annual_population_hours_se": row["annual_population_hours_se"],
            "annual_population_hours_ci95_lower": row["annual_population_hours_ci95_lower"],
            "annual_population_hours_ci95_upper": row["annual_population_hours_ci95_upper"],
            "participation_rate": row["participation_rate"],
            "mean_minutes_per_person_day": row["mean_minutes_per_person_day"],
            "zero_observed_sample": row["zero_observed_sample"],
            "weight_policy": "validation_only_do_not_double_count_market_work" if row["first_tier_code"] == "05" else "everyday_life_population_time_axis",
        }
        for row in pooled
    ]
    fields = list(rows[0])
    catalog.write_csv(
        "everyday_life/atus_activity_weights.csv",
        fields,
        rows,
        primary_key=["activity_weight_uid"],
        origins={field: canonical.ORIGIN_DERIVED for field in fields},
    )
    return rows


def build_atus_replicate_weights(catalog: canonical.OutputCatalog) -> int:
    """Retain pooled activity replicate systems for covariance-aware sums."""

    source = (
        CANONICAL_ROOT
        / "everyday_life"
        / "atus_activity_replicate_estimates.csv.gz"
    )

    def records() -> Iterable[dict[str, str]]:
        with gzip.open(source, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                code = row["activity_code"]
                yield {
                    "activity_weight_replicate_uid": (
                        f"atus-population-time-replicate:2021-2025:"
                        f"{row['replicate_system_id']}:{code}"
                    ),
                    "source_unit_uid": f"atus-activity:2021-2025:{code}",
                    "activity_code": code,
                    "replicate_system_id": row["replicate_system_id"],
                    "perturbed_year": row["perturbed_year"],
                    "replicate_index": row["replicate_index"],
                    "replicate_variance_factor": row["replicate_variance_factor"],
                    "central_annual_population_hours": row[
                        "central_annual_population_hours"
                    ],
                    "replicate_annual_population_hours": row[
                        "replicate_annual_population_hours"
                    ],
                    "replicate_deviation_hours": row["replicate_deviation_hours"],
                }

    fields = [
        "activity_weight_replicate_uid",
        "source_unit_uid",
        "activity_code",
        "replicate_system_id",
        "perturbed_year",
        "replicate_index",
        "replicate_variance_factor",
        "central_annual_population_hours",
        "replicate_annual_population_hours",
        "replicate_deviation_hours",
    ]
    result = catalog.write_csv(
        "everyday_life/atus_activity_replicate_estimates.csv.gz",
        fields,
        records(),
        primary_key=["activity_weight_replicate_uid"],
        origins={field: canonical.ORIGIN_DERIVED for field in fields},
    )
    return result.rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def build(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    canonical_report = canonical.verify(CANONICAL_ROOT)
    output.mkdir(parents=True, exist_ok=True)
    catalog = canonical.OutputCatalog(output)
    macro = macro_values()
    economic_units, economic_values = build_economic_units(catalog, macro)
    occupation_rows, occupation_values = build_occupation_allocations(catalog, economic_values)
    task_rows, task_audit = build_task_allocations(catalog, occupation_rows, occupation_values)
    atus_rows = build_atus_weights(catalog)
    atus_replicate_rows = build_atus_replicate_weights(catalog)

    available_units = [row for row in economic_units if row["economic_value_usd"]]
    total_oews_value = sum(float(row["economic_value_usd"]) for row in available_units)
    occupations_with_tasks = {row["onet_soc_code"] for row in task_rows}
    unassigned_no_task = sum(
        value
        for code, value in occupation_values.items()
        if value is not None and code not in occupations_with_tasks
    )
    audit = {
        "schema_version": 1,
        "canonical_manifest_sha256": canonical.sha256_file(CANONICAL_ROOT / "manifest.json"),
        "canonical_table_count": canonical_report["table_count"],
        "macro_anchors": macro,
        "oews": {
            "published_units": len(economic_units),
            "units_with_economic_value": len(available_units),
            "units_without_annual_wage": len(economic_units) - len(available_units),
            "sum_available_oews_economic_value_usd": total_oews_value,
            "share_of_gdi_represented_by_available_oews_units": total_oews_value / macro["gross_domestic_income_usd"],
        },
        "occupations": {
            "rows": len(occupation_rows),
            "mapped_rows": sum(bool(row["oews_occupation_code"]) for row in occupation_rows),
            "unmapped_rows": sum(not bool(row["oews_occupation_code"]) for row in occupation_rows),
            "economic_value_unassigned_because_no_task_inventory_usd": unassigned_no_task,
        },
        "tasks": task_audit,
        "atus": {
            "activity_rows": len(atus_rows),
            "pooled_activity_replicate_rows": atus_replicate_rows,
            "paid_work_rows_validation_only": sum(row["first_tier_code"] == "05" for row in atus_rows),
            "population_time_and_market_dollars_kept_separate": True,
        },
        "assumptions": [
            "OEWS wage bills are scaled by BEA gross domestic income divided by BEA wages and salaries.",
            "OEWS aggregates are divided equally among constituent 2018 SOC occupations because no source-native constituent employment split is available.",
            "A 2018 SOC is divided equally among its O*NET extensions because no source-native extension employment split is available.",
            "The central task salience uses relevance times normalized importance times expected ordinal frequency category.",
            "The ordinal frequency category is a ranking factor, not estimated labor time or occurrences per year.",
            "Conservative, central, and aggressive event-rate anchor vectors are emitted only as sensitivity allocations; they assume a 250-day work year and declared endpoints for open categories.",
            "Missing task ratings use the occupation median score; if every rating is missing, task shares are uniform.",
        ],
    }
    write_json(output / "audit_report.json", audit)
    table_manifest = {
        name: {
            "rows": record.rows,
            "fields": record.fields,
            "primary_key": record.primary_key,
            "bytes": record.bytes,
            "sha256": record.sha256,
        }
        for name, record in sorted(catalog.tables.items())
    }
    manifest = {
        "schema_version": 1,
        "weight_release": "weights_v2",
        "canonical_manifest_sha256": canonical.sha256_file(CANONICAL_ROOT / "manifest.json"),
        "central_task_variant": CENTRAL_VARIANT,
        "weighting_axes": [
            "market_work_economic_value_usd",
            "everyday_life_annual_population_hours",
            "household_production_value_usd_unallocated",
        ],
        "tables": table_manifest,
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def verify(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    canonical.verify(CANONICAL_ROOT)
    manifest_path = output / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WeightError(f"cannot read weight manifest: {exc}") from exc
    if manifest["canonical_manifest_sha256"] != canonical.sha256_file(CANONICAL_ROOT / "manifest.json"):
        raise WeightError("weights were built from a different canonical manifest")
    total_bytes = 0
    for filename, expected in manifest["tables"].items():
        path = output / filename
        if not path.is_file():
            raise WeightError(f"weight table is missing: {filename}")
        if path.stat().st_size != expected["bytes"] or canonical.sha256_file(path) != expected["sha256"]:
            raise WeightError(f"weight table identity failed: {filename}")
        total_bytes += path.stat().st_size
    return {"ok": True, "table_count": len(manifest["tables"]), "table_bytes": total_bytes}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "verify"])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = build(args.output) if args.command == "build" else verify(args.output)
    except (WeightError, canonical.CanonicalError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
