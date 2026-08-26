"""Build the audited activity inventory used before physicality screening.

The release is a deterministic view over ``canonical_v2``, ``weights_v2``,
and ``source_evidence_v2``.  It does not add physicality, calibration, action,
or simulator labels.  Market-work dollars and everyday-life population hours
remain separate axes throughout.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, getcontext, localcontext
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import build_canonical as canonical
import build_source_evidence as source_evidence
import build_weights as weights


GROUNDING_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ROOT = GROUNDING_ROOT / "data" / "derived" / "canonical_v2"
WEIGHTS_ROOT = GROUNDING_ROOT / "data" / "derived" / "weights_v2"
EVIDENCE_ROOT = GROUNDING_ROOT / "data" / "derived" / "source_evidence_v2"
DEFAULT_OUTPUT = GROUNDING_ROOT / "data" / "derived" / "activity_inventory_v1"
SCHEMA_PATH = GROUNDING_ROOT / "schemas" / "activity_inventory_release.schema.json"
REPORT_PATH = GROUNDING_ROOT / "reports" / "activity_inventory_v1.md"

RELEASE = "activity_inventory_v1"
METHOD = "deterministic_activity_inventory_v1"
MARKET_AXIS = "market_work_economic_value_usd"
MARKET_UNIT = "USD_2025"
EVERYDAY_AXIS = "everyday_life_annual_population_hours"
EVERYDAY_UNIT = "person_hours_per_year_2021_2025_average"
ATUS_VARIANT = "pooled_2021_2025_population_time"
EXPECTED_ATUS_REPLICATE_SYSTEMS = 800
Z_95 = Decimal("1.959963984540054")
SERIALIZATION_TOLERANCE_USD = Decimal("0.001")

# Aggregation must not depend on whichever module happened to set Decimal's
# process-global context first.  This bound is comfortably above the combined
# significant digits of every serialized source value and every finite sum or
# product used below.  Irrational square roots are separately rounded in a
# fixed 50-digit local context.
getcontext().prec = max(getcontext().prec, 256)

TABLE_FILES = (
    "occupations.csv",
    "occupational_tasks.csv.gz",
    "everyday_activities.csv",
    "market_work_groups.csv",
    "everyday_life_groups.csv",
)
RELEASE_FILES = set(TABLE_FILES) | {"summary.json", "manifest.json"}

SOURCE_NATIVE_FIELDS = {
    "occupations.csv": {
        "source_release",
        "onet_soc_code",
        "occupation_title",
        "occupation_description",
    },
    "occupational_tasks.csv.gz": {
        "source_release",
        "onet_soc_code",
        "task_id",
        "task_text",
        "task_type",
        "incumbents_responding",
        "task_date",
        "task_domain_source",
        "importance_value",
        "relevance_value",
        "frequency_n",
    },
    "everyday_activities.csv": {
        "activity_code",
        "tier1_code",
        "tier2_code",
        "tier3_code",
        "first_tier_label",
        "activity_label",
        "latest_examples_json",
    },
    "market_work_groups.csv": set(),
    "everyday_life_groups.csv": set(),
}

VARIANTS = tuple(weights.VARIANTS)
CENTRAL_VARIANT = weights.CENTRAL_VARIANT

# These are the official 2018 SOC major-group names.  The grouping itself is
# the first two digits already carried by the O*NET/OEWS bridge; no grouping is
# inferred from occupation titles or task text.
SOC_MAJOR_GROUP_TITLES = {
    "11-0000": "Management Occupations",
    "13-0000": "Business and Financial Operations Occupations",
    "15-0000": "Computer and Mathematical Occupations",
    "17-0000": "Architecture and Engineering Occupations",
    "19-0000": "Life, Physical, and Social Science Occupations",
    "21-0000": "Community and Social Service Occupations",
    "23-0000": "Legal Occupations",
    "25-0000": "Educational Instruction and Library Occupations",
    "27-0000": "Arts, Design, Entertainment, Sports, and Media Occupations",
    "29-0000": "Healthcare Practitioners and Technical Occupations",
    "31-0000": "Healthcare Support Occupations",
    "33-0000": "Protective Service Occupations",
    "35-0000": "Food Preparation and Serving Related Occupations",
    "37-0000": "Building and Grounds Cleaning and Maintenance Occupations",
    "39-0000": "Personal Care and Service Occupations",
    "41-0000": "Sales and Related Occupations",
    "43-0000": "Office and Administrative Support Occupations",
    "45-0000": "Farming, Fishing, and Forestry Occupations",
    "47-0000": "Construction and Extraction Occupations",
    "49-0000": "Installation, Maintenance, and Repair Occupations",
    "51-0000": "Production Occupations",
    "53-0000": "Transportation and Material Moving Occupations",
    "55-0000": "Military Specific Occupations",
}


class InventoryError(RuntimeError):
    """Raised when an inventory provenance or conservation rule fails."""


@dataclass(frozen=True)
class InventoryBundle:
    occupations: list[dict[str, str]]
    occupational_tasks: list[dict[str, str]]
    everyday_activities: list[dict[str, str]]
    market_work_groups: list[dict[str, str]]
    everyday_life_groups: list[dict[str, str]]
    summary: dict[str, Any]


def read_csv(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def iter_csv(path: Path) -> Iterator[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InventoryError(f"{path} must contain a JSON object")
    return value


def decimal_value(
    value: Any,
    label: str,
    *,
    nullable: bool = False,
    nonnegative: bool = True,
) -> Decimal | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        if nullable:
            return None
        raise InventoryError(f"{label} is missing")
    if isinstance(value, bool):
        raise InventoryError(f"{label} must be a decimal, not a boolean")
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise InventoryError(f"{label} is not a decimal: {value!r}") from exc
    if not result.is_finite():
        raise InventoryError(f"{label} must be finite")
    if nonnegative and result < 0:
        raise InventoryError(f"{label} must be nonnegative")
    return result


def decimal_string(value: Decimal | int) -> str:
    number = value if isinstance(value, Decimal) else Decimal(value)
    if not number.is_finite():
        raise InventoryError("cannot serialize a non-finite decimal")
    if number == 0:
        return "0"
    rendered = format(number, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return sum(values, Decimal(0))


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def stable_row_sha256(row: Mapping[str, Any]) -> str:
    import hashlib

    return hashlib.sha256(canonical.stable_json(dict(row)).encode("utf-8")).hexdigest()


def index_unique(
    rows: Iterable[Mapping[str, str]], key: str, label: str
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for raw in rows:
        row = dict(raw)
        value = row.get(key, "")
        if not value or value in result:
            raise InventoryError(f"{label} has a blank or duplicate {key}: {value!r}")
        result[value] = row
    return result


def atus_weight_status(row: Mapping[str, str]) -> str:
    """Apply the registered ATUS status precedence used by allocation."""

    mass = decimal_value(row.get("annual_population_hours"), "ATUS mass")
    assert mass is not None
    first_tier = row.get("first_tier_code") or row.get("tier1_code")
    if first_tier == "05":
        return "excluded_paid_work"
    if row.get("analysis_class") == "data_code":
        return "excluded_data_code"
    if row.get("zero_observed_sample") == "true" or mass == 0:
        return "observed_zero"
    return "available"


def _evidence_fields(packet: Mapping[str, str]) -> dict[str, str]:
    return {
        "packet_id": packet["packet_id"],
        "packet_version": packet["packet_version"],
        "packet_sha256": packet["packet_sha256"],
        "native_evidence_count": packet["native_evidence_count"],
        "external_evidence_count": packet["external_evidence_count"],
        "evidence_status": packet["evidence_status"],
        "packet_canonical_manifest_sha256": packet["canonical_manifest_sha256"],
        "evidence_join_status": "matched",
    }


def _variant_fields(source: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for variant in VARIANTS:
        for stem in (
            "source_score",
            "effective_score",
            "task_share",
            "task_economic_value_usd",
        ):
            field = f"{stem}_{variant}"
            result[field] = source[field]
        result[f"task_economic_value_status_{variant}"] = (
            "available"
            if source[f"task_economic_value_usd_{variant}"]
            else "unavailable_upstream"
        )
    return result


def build_market_inventory(
    packet_index: Mapping[str, Mapping[str, str]],
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    dict[str, Any],
]:
    canonical_occupations = index_unique(
        read_csv(CANONICAL_ROOT / "market_work" / "onet_occupations.csv"),
        "onet_soc_code",
        "canonical occupation table",
    )
    canonical_tasks = index_unique(
        read_csv(CANONICAL_ROOT / "market_work" / "onet_tasks.csv"),
        "task_uid",
        "canonical task table",
    )
    occupation_weights = index_unique(
        read_csv(WEIGHTS_ROOT / "market_work" / "onet_occupation_allocations.csv"),
        "onet_soc_code",
        "occupation weight table",
    )
    task_weights = index_unique(
        read_csv(WEIGHTS_ROOT / "market_work" / "onet_task_allocations.csv.gz"),
        "task_uid",
        "task weight table",
    )
    if len(canonical_occupations) != 1_016 or set(canonical_occupations) != set(occupation_weights):
        raise InventoryError("occupation inventory must join all 1,016 O*NET occupations")
    if len(canonical_tasks) != 18_796 or set(canonical_tasks) != set(task_weights):
        raise InventoryError("task inventory must join all 18,796 O*NET tasks")

    hierarchy = index_unique(
        read_csv(CANONICAL_ROOT / "market_work" / "onet_activity_hierarchy.csv"),
        "dwa_element_id",
        "O*NET DWA hierarchy",
    )
    iwa = index_unique(
        read_csv(CANONICAL_ROOT / "market_work" / "onet_gwa_iwa_links.csv"),
        "iwa_element_id",
        "O*NET GWA/IWA hierarchy",
    )
    links_by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    for link in read_csv(CANONICAL_ROOT / "market_work" / "onet_task_dwa_links.csv"):
        if link["task_uid"] not in canonical_tasks:
            raise InventoryError(f"DWA link refers to unknown task {link['task_uid']}")
        links_by_task[link["task_uid"]].append(link)
    for rows in links_by_task.values():
        rows.sort(key=lambda row: (row["dwa_element_id"], row["link_uid"]))

    tools_by_occupation: dict[str, list[dict[str, str]]] = defaultdict(list)
    tool_release_values: set[str] = set()
    carry_forward_reasons: set[str] = set()
    for row in read_csv(
        CANONICAL_ROOT / "market_work" / "onet_tools_used_30_2.csv.gz"
    ):
        if row["onet_soc_code"] not in canonical_occupations:
            raise InventoryError(f"tool context refers to unknown occupation {row['onet_soc_code']}")
        tool_release_values.add(row["source_release"])
        carry_forward_reasons.add(row["carry_forward_reason"])
        tools_by_occupation[row["onet_soc_code"]].append(
            {
                "commodity_code": row["commodity_code"],
                "commodity_title": row["commodity_title"],
                "example": row["example"],
            }
        )
    if tool_release_values != {"O*NET 30.2"} or len(carry_forward_reasons) != 1:
        raise InventoryError("Tools Used must remain the declared final O*NET 30.2 carry-forward")
    for rows in tools_by_occupation.values():
        rows.sort(key=lambda row: (row["commodity_code"], row["example"], row["commodity_title"]))

    tasks_by_occupation: dict[str, list[dict[str, str]]] = defaultdict(list)
    for task in canonical_tasks.values():
        tasks_by_occupation[task["onet_soc_code"]].append(task)
    for rows in tasks_by_occupation.values():
        rows.sort(key=lambda row: row["task_uid"])

    occupations: list[dict[str, str]] = []
    for code, source in sorted(canonical_occupations.items()):
        allocation = occupation_weights[code]
        native_tasks = tasks_by_occupation.get(code, [])
        tools = tools_by_occupation.get(code, [])
        missing: list[str] = []
        if not native_tasks:
            missing.append("no_native_task_rows")
        if not allocation["occupation_economic_value_usd"]:
            missing.append("market_economic_value_unavailable")
        if not tools:
            missing.append("no_occupation_tool_context")
        rated = sum(task["ratings_available"] == "true" for task in native_tasks)
        suppressed = sum(
            task["importance_recommend_suppress"] == "Y"
            or task["relevance_recommend_suppress"] == "Y"
            or task["frequency_recommend_suppress_any"] == "true"
            for task in native_tasks
        )
        linked = sum(int(task["dwa_link_count"] or "0") > 0 for task in native_tasks)
        group_code = allocation["major_occupation_group"]
        occupations.append(
            {
                "occupation_uid": source["occupation_uid"],
                "source_release": source["source_release"],
                "onet_soc_code": code,
                "occupation_title": source["title"],
                "occupation_description": source["description"],
                "market_group_uid": f"soc-major-group:2018:{group_code}",
                "major_occupation_group": group_code,
                "inventory_status": (
                    "available" if native_tasks else "structurally_missing_native_task_inventory"
                ),
                "native_task_count": str(len(native_tasks)),
                "rated_task_count": str(rated),
                "unrated_task_count": str(len(native_tasks) - rated),
                "rating_suppressed_task_count": str(suppressed),
                "dwa_linked_task_count": str(linked),
                "dwa_unlinked_task_count": str(len(native_tasks) - linked),
                "occupation_allocation_uid": allocation["occupation_allocation_uid"],
                "soc_2018_code": allocation["soc_2018_code"],
                "oews_occupation_code": allocation["oews_occupation_code"],
                "occupation_mapping_status": allocation["mapping_status"],
                "occupation_economic_value_usd": allocation["occupation_economic_value_usd"],
                "upstream_economic_value_status": allocation["economic_value_status"],
                "market_weight_status": (
                    "available"
                    if allocation["occupation_economic_value_usd"]
                    else "unavailable_upstream"
                ),
                "economic_axis": MARKET_AXIS,
                "economic_unit": MARKET_UNIT,
                "reference_period": "2025",
                "tools_context_release": "O*NET 30.2 final Tools Used table",
                "tools_carry_forward_reason": next(iter(carry_forward_reasons)),
                "tools_context_status": (
                    "occupation_context_available" if tools else "occupation_context_absent"
                ),
                "occupation_tool_example_count": str(len(tools)),
                "occupation_tool_records_json": canonical.stable_json(tools),
                "tools_context_scope": "occupation_level_carry_forward_context_only",
                "task_tool_requirement_inference": "prohibited",
                "structural_missingness_codes_json": canonical.stable_json(sorted(missing)),
                "canonical_occupation_row_sha256": stable_row_sha256(source),
                "occupation_weight_row_sha256": stable_row_sha256(allocation),
            }
        )

    task_rows: list[dict[str, str]] = []
    for task_uid, task in sorted(canonical_tasks.items()):
        allocation = task_weights[task_uid]
        if (
            allocation["onet_soc_code"] != task["onet_soc_code"]
            or allocation["task_id"] != task["task_id"]
            or allocation["task_text"] != task["task_text"]
        ):
            raise InventoryError(f"canonical and weighted task rows disagree for {task_uid}")
        occupation = canonical_occupations[task["onet_soc_code"]]
        occupation_output = next(
            row for row in occupations if row["onet_soc_code"] == task["onet_soc_code"]
        )
        packet = packet_index.get(task_uid)
        if packet is None or packet.get("activity_stream") != "market_work":
            raise InventoryError(f"task lacks its market-work evidence packet: {task_uid}")
        links = links_by_task.get(task_uid, [])
        source_ids = sorted(json.loads(task["dwa_element_ids_json"]))
        link_ids = sorted(link["dwa_element_id"] for link in links)
        if int(task["dwa_link_count"] or "0") != len(links) or source_ids != link_ids:
            raise InventoryError(f"task/DWA linkage fields disagree for {task_uid}")
        paths: list[dict[str, str]] = []
        for link in links:
            dwa = hierarchy.get(link["dwa_element_id"])
            if dwa is None:
                raise InventoryError(f"task DWA link has no hierarchy row: {link['link_uid']}")
            iwa_row = iwa.get(dwa["iwa_element_id"])
            if iwa_row is None or iwa_row["gwa_element_id"] != dwa["gwa_element_id"]:
                raise InventoryError(f"DWA has an inconsistent IWA/GWA path: {dwa['dwa_element_id']}")
            paths.append(
                {
                    "dwa_element_id": dwa["dwa_element_id"],
                    "dwa_element_name": dwa["dwa_element_name"],
                    "gwa_element_id": dwa["gwa_element_id"],
                    "iwa_element_id": dwa["iwa_element_id"],
                    "iwa_element_name": iwa_row["iwa_element_name"],
                    "link_date": link["date"],
                    "link_domain_source": link["domain_source"],
                    "link_uid": link["link_uid"],
                }
            )
        tools = tools_by_occupation.get(task["onet_soc_code"], [])
        missing: list[str] = []
        if task["ratings_available"] != "true":
            missing.append("source_task_ratings_unavailable")
        if not links:
            missing.append("no_native_dwa_link")
        if not tools:
            missing.append("no_occupation_tool_context")
        if not allocation["task_economic_value_usd"]:
            missing.append("market_economic_value_unavailable")
        row = {
            "task_uid": task_uid,
            "source_release": task["source_release"],
            "onet_soc_code": task["onet_soc_code"],
            "occupation_uid": occupation["occupation_uid"],
            "occupation_title": occupation["title"],
            "market_group_uid": occupation_output["market_group_uid"],
            "major_occupation_group": allocation["major_occupation_group"],
            "task_id": task["task_id"],
            "task_text": task["task_text"],
            "task_type": task["task_type"],
            "incumbents_responding": task["incumbents_responding"],
            "task_date": task["task_date"],
            "task_domain_source": task["task_domain_source"],
            "inventory_status": "available",
            "ratings_available": task["ratings_available"],
            "rating_status": (
                "source_ratings_available"
                if task["ratings_available"] == "true"
                else "source_ratings_unavailable_with_declared_imputation"
            ),
            "rating_imputation_status": allocation["rating_imputation_status"],
            "rating_suppressed_any": allocation["rating_suppressed_any"],
            "importance_value": task["importance_value"],
            "relevance_value": task["relevance_value"],
            "frequency_distribution_json": task["frequency_distribution_json"],
            "frequency_n": task["frequency_n"],
            "frequency_percent_sum": task["frequency_percent_sum"],
            "hierarchy_status": "linked" if links else "no_native_dwa_link",
            "hierarchy_scope": "source_native_context_not_action_decomposition",
            "dwa_link_count": str(len(links)),
            "dwa_element_ids_json": canonical.stable_json(link_ids),
            "dwa_hierarchy_paths_json": canonical.stable_json(paths),
            "tools_context_scope": "occupation_level_carry_forward_context_only",
            "occupation_tools_context_status": (
                "occupation_context_available" if tools else "occupation_context_absent"
            ),
            "occupation_tool_example_count": str(len(tools)),
            "task_tool_requirement_inference": "prohibited",
            "occupation_allocation_uid": occupation_output["occupation_allocation_uid"],
            "task_allocation_uid": allocation["task_allocation_uid"],
            "oews_occupation_code": allocation["oews_occupation_code"],
            "occupation_mapping_status": allocation["occupation_mapping_status"],
            "occupation_economic_value_usd": allocation["occupation_economic_value_usd"],
            "market_weight_status": (
                "available" if allocation["task_economic_value_usd"] else "unavailable_upstream"
            ),
            "economic_axis": MARKET_AXIS,
            "economic_unit": MARKET_UNIT,
            "reference_period": "2025",
            **_variant_fields(allocation),
            "central_weight_variant": allocation["central_weight_variant"],
            "task_economic_value_usd": allocation["task_economic_value_usd"],
            **_evidence_fields(packet),
            "structural_missingness_codes_json": canonical.stable_json(sorted(missing)),
            "canonical_task_row_sha256": stable_row_sha256(task),
            "task_weight_row_sha256": stable_row_sha256(allocation),
        }
        task_rows.append(row)

    occupations_by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    tasks_by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in occupations:
        occupations_by_group[row["major_occupation_group"]].append(row)
    for row in task_rows:
        tasks_by_group[row["major_occupation_group"]].append(row)
    if set(occupations_by_group) != set(SOC_MAJOR_GROUP_TITLES):
        raise InventoryError("SOC major-group inventory differs from the declared 23-group frame")

    market_groups: list[dict[str, str]] = []
    max_residual_by_variant: dict[str, Decimal] = {variant: Decimal(0) for variant in VARIANTS}
    for group_code in sorted(occupations_by_group):
        group_occupations = occupations_by_group[group_code]
        group_tasks = tasks_by_group.get(group_code, [])
        known_occupation_mass = sum_decimal(
            decimal_value(row["occupation_economic_value_usd"], "occupation value")
            for row in group_occupations
            if row["occupation_economic_value_usd"]
        )
        no_task_mass = sum_decimal(
            decimal_value(row["occupation_economic_value_usd"], "occupation value")
            for row in group_occupations
            if row["inventory_status"] != "available" and row["occupation_economic_value_usd"]
        )
        no_task_count = sum(row["inventory_status"] != "available" for row in group_occupations)
        unavailable_occupations = sum(row["market_weight_status"] != "available" for row in group_occupations)
        missing: list[str] = []
        if no_task_count:
            missing.append("contains_occupations_without_native_task_inventory")
        if unavailable_occupations:
            missing.append("contains_unavailable_market_economic_values")
        if any(row["tools_context_status"] == "occupation_context_absent" for row in group_occupations):
            missing.append("contains_occupations_without_tool_context")
        if any(row["hierarchy_status"] != "linked" for row in group_tasks):
            missing.append("contains_tasks_without_native_dwa_links")
        base = {
            "market_group_uid": f"soc-major-group:2018:{group_code}",
            "major_occupation_group": group_code,
            "major_occupation_group_title": SOC_MAJOR_GROUP_TITLES[group_code],
            "group_definition": "2018_SOC_major_group_code_prefix",
            "occupation_count": str(len(group_occupations)),
            "occupation_with_task_inventory_count": str(len(group_occupations) - no_task_count),
            "occupation_without_task_inventory_count": str(no_task_count),
            "task_count": str(len(group_tasks)),
            "rated_task_count": str(sum(row["ratings_available"] == "true" for row in group_tasks)),
            "unrated_task_count": str(sum(row["ratings_available"] != "true" for row in group_tasks)),
            "rating_suppressed_task_count": str(sum(row["rating_suppressed_any"] == "true" for row in group_tasks)),
            "dwa_linked_task_count": str(sum(row["hierarchy_status"] == "linked" for row in group_tasks)),
            "dwa_unlinked_task_count": str(sum(row["hierarchy_status"] != "linked" for row in group_tasks)),
            "occupation_with_tool_context_count": str(sum(row["tools_context_status"] == "occupation_context_available" for row in group_occupations)),
            "occupation_without_tool_context_count": str(sum(row["tools_context_status"] == "occupation_context_absent" for row in group_occupations)),
            "evidence_packet_joined_task_count": str(sum(row["evidence_join_status"] == "matched" for row in group_tasks)),
            "occupation_economic_value_available_count": str(len(group_occupations) - unavailable_occupations),
            "occupation_economic_value_unavailable_count": str(unavailable_occupations),
            "occupation_economic_value_usd_known": decimal_string(known_occupation_mass),
            "unassigned_economic_value_usd_no_task_inventory": decimal_string(no_task_mass),
            "inventory_status": (
                "complete_native_task_inventory"
                if no_task_count == 0
                else "contains_structural_task_inventory_gaps"
            ),
            "economic_status": (
                "complete_available_values"
                if unavailable_occupations == 0
                else "contains_unavailable_upstream_values"
            ),
            "economic_axis": MARKET_AXIS,
            "economic_unit": MARKET_UNIT,
            "reference_period": "2025",
        }
        for variant in VARIANTS:
            field = f"task_economic_value_usd_{variant}"
            numeric_tasks = [row for row in group_tasks if row[field]]
            task_mass = sum_decimal(
                decimal_value(row[field], f"{variant} task value") for row in numeric_tasks
            )
            known_with_tasks = sum_decimal(
                decimal_value(row["occupation_economic_value_usd"], "occupation value")
                for row in group_occupations
                if row["inventory_status"] == "available" and row["occupation_economic_value_usd"]
            )
            residual = known_with_tasks - task_mass
            per_occupation_task_mass: dict[str, Decimal] = defaultdict(Decimal)
            for row in numeric_tasks:
                value = decimal_value(row[field], f"{variant} task value")
                assert value is not None
                per_occupation_task_mass[row["onet_soc_code"]] += value
            for occupation in group_occupations:
                if occupation["inventory_status"] != "available" or not occupation["occupation_economic_value_usd"]:
                    continue
                occupation_value = decimal_value(
                    occupation["occupation_economic_value_usd"], "occupation value"
                )
                assert occupation_value is not None
                difference = occupation_value - per_occupation_task_mass[occupation["onet_soc_code"]]
                max_residual_by_variant[variant] = max(
                    max_residual_by_variant[variant], abs(difference)
                )
                if abs(difference) > SERIALIZATION_TOLERANCE_USD:
                    raise InventoryError(
                        f"{occupation['onet_soc_code']}/{variant} exceeds the declared serialized-dollar tolerance"
                    )
            if known_occupation_mass != task_mass + no_task_mass + residual:
                raise InventoryError(f"market group conservation failed for {group_code}/{variant}")
            base[field] = decimal_string(task_mass)
            base[f"task_economic_value_available_count_{variant}"] = str(len(numeric_tasks))
            base[f"task_economic_value_unavailable_count_{variant}"] = str(len(group_tasks) - len(numeric_tasks))
            base[f"allocation_serialization_residual_usd_{variant}"] = decimal_string(residual)
            base[f"conservation_status_{variant}"] = "conserved_with_explicit_serialization_residual"
        base["central_weight_variant"] = CENTRAL_VARIANT
        base["task_economic_value_usd"] = base[f"task_economic_value_usd_{CENTRAL_VARIANT}"]
        base["structural_missingness_codes_json"] = canonical.stable_json(sorted(missing))
        market_groups.append(base)

    market_summary = {
        "occupation_rows": len(occupations),
        "occupations_with_native_tasks": sum(row["inventory_status"] == "available" for row in occupations),
        "occupations_without_native_tasks": sum(row["inventory_status"] != "available" for row in occupations),
        "occupations_with_tool_context": sum(row["tools_context_status"] == "occupation_context_available" for row in occupations),
        "occupations_without_tool_context": sum(row["tools_context_status"] == "occupation_context_absent" for row in occupations),
        "occupational_task_rows": len(task_rows),
        "tasks_with_evidence_packet": sum(row["evidence_join_status"] == "matched" for row in task_rows),
        "tasks_with_dwa_hierarchy": sum(row["hierarchy_status"] == "linked" for row in task_rows),
        "tasks_without_dwa_hierarchy": sum(row["hierarchy_status"] != "linked" for row in task_rows),
        "market_group_rows": len(market_groups),
        "task_weight_variants": {
            variant: {
                "task_economic_value_usd": decimal_string(
                    sum_decimal(
                        decimal_value(row[f"task_economic_value_usd_{variant}"], "group task mass")
                        for row in market_groups
                    )
                ),
                "allocation_serialization_residual_usd": decimal_string(
                    sum_decimal(
                        decimal_value(row[f"allocation_serialization_residual_usd_{variant}"], "group residual", nonnegative=False)
                        for row in market_groups
                    )
                ),
                "maximum_absolute_occupation_serialization_residual_usd": decimal_string(max_residual_by_variant[variant]),
            }
            for variant in VARIANTS
        },
        "serialized_dollar_conservation_tolerance_usd": decimal_string(SERIALIZATION_TOLERANCE_USD),
        "tools_used_scope": "O*NET 30.2 occupation-level carry-forward context only; never a task requirement",
    }
    return occupations, task_rows, market_groups, market_summary


def build_everyday_activities(
    packet_index: Mapping[str, Mapping[str, str]],
) -> list[dict[str, str]]:
    lexicon_by_code: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(CANONICAL_ROOT / "everyday_life" / "atus_activity_lexicon.csv"):
        lexicon_by_code[row["activity_code"]].append(row)
    weights_by_code = index_unique(
        read_csv(WEIGHTS_ROOT / "everyday_life" / "atus_activity_weights.csv"),
        "activity_code",
        "ATUS activity weight table",
    )
    if len(lexicon_by_code) != 465 or len(weights_by_code) != 465:
        raise InventoryError("everyday inventory must retain all 465 ATUS activity codes")

    result: list[dict[str, str]] = []
    for code, weight in sorted(weights_by_code.items()):
        versions = sorted(lexicon_by_code.get(code, []), key=lambda row: int(row["year"]))
        if not versions:
            raise InventoryError(f"ATUS weight has no lexicon version: {code}")
        latest = versions[-1]
        tier_signature = {
            (row["tier1_code"], row["tier2_code"], row["tier3_code"], row["first_tier_label"], row["analysis_class"])
            for row in versions
        }
        if len(tier_signature) != 1:
            raise InventoryError(f"ATUS hierarchy changed across the declared window: {code}")
        if (
            latest["activity_label"] != weight["activity_label"]
            or latest["first_tier_label"] != weight["first_tier_label"]
            or latest["analysis_class"] != weight["analysis_class"]
        ):
            raise InventoryError(f"latest ATUS lexicon and weight labels disagree: {code}")
        source_uid = f"atus-activity:2021-2025:{code}"
        packet = packet_index.get(source_uid)
        if packet is None or packet.get("activity_stream") != "everyday_life":
            raise InventoryError(f"ATUS activity lacks its evidence packet: {source_uid}")
        years = [row["year"] for row in versions]
        missing: list[str] = []
        if years != ["2021", "2022", "2023", "2024", "2025"]:
            missing.append("lexicon_absent_in_one_or_more_window_years")
        mass = decimal_value(weight["annual_population_hours"], "ATUS mass")
        lower = decimal_value(
            weight["annual_population_hours_ci95_lower"],
            "ATUS CI lower",
            nullable=True,
            nonnegative=False,
        )
        result.append(
            {
                "source_unit_uid": source_uid,
                "activity_weight_uid": weight["activity_weight_uid"],
                "source_release": weight["source_release"],
                "activity_code": code,
                "tier1_code": latest["tier1_code"],
                "tier2_code": latest["tier2_code"],
                "tier3_code": latest["tier3_code"],
                "first_tier_group_uid": f"atus-first-tier:2021-2025:{latest['tier1_code']}",
                "second_tier_group_uid": f"atus-second-tier:2021-2025:{latest['tier1_code']}{latest['tier2_code']}",
                "third_tier_group_uid": f"atus-third-tier:2021-2025:{code}",
                "first_tier_label": latest["first_tier_label"],
                "activity_label": latest["activity_label"],
                "analysis_class": latest["analysis_class"],
                "inventory_status": "available",
                "lexicon_status": (
                    "present_all_window_years" if not missing else "absent_in_one_or_more_window_years"
                ),
                "lexicon_version_count": str(len(versions)),
                "lexicon_years_json": canonical.stable_json(years),
                "lexicon_activity_uids_json": canonical.stable_json([row["activity_uid"] for row in versions]),
                "label_version_count": str(len({row["activity_label"] for row in versions})),
                "examples_version_count": str(len({row["examples_json"] for row in versions})),
                "latest_examples_json": latest["examples_json"],
                "weight_status": atus_weight_status(weight),
                "weight_policy": weight["weight_policy"],
                "weight_axis": EVERYDAY_AXIS,
                "weight_variant": ATUS_VARIANT,
                "weight_unit": EVERYDAY_UNIT,
                "reference_period": "2021-2025 pooled annual average",
                "annual_population_hours": decimal_string(mass),
                "annual_population_hours_se": weight["annual_population_hours_se"],
                "annual_population_hours_ci95_lower_unclipped": weight["annual_population_hours_ci95_lower"],
                "annual_population_hours_ci95_lower_nonnegative": (
                    "" if lower is None else decimal_string(max(lower, Decimal(0)))
                ),
                "annual_population_hours_ci95_upper": weight["annual_population_hours_ci95_upper"],
                "participation_rate": weight["participation_rate"],
                "mean_minutes_per_person_day": weight["mean_minutes_per_person_day"],
                "zero_observed_sample": weight["zero_observed_sample"],
                **_evidence_fields(packet),
                "structural_missingness_codes_json": canonical.stable_json(sorted(missing)),
                "latest_lexicon_row_sha256": stable_row_sha256(latest),
                "activity_weight_row_sha256": stable_row_sha256(weight),
            }
        )
    return result


def _uncertainty(
    point: Decimal,
    systems: Sequence[str],
    factor_by_system: Mapping[str, Decimal],
    deviation_by_system: Mapping[str, Decimal],
) -> tuple[str, str, str, str, str]:
    variance = sum_decimal(
        factor_by_system[system]
        * deviation_by_system.get(system, Decimal(0))
        * deviation_by_system.get(system, Decimal(0))
        for system in systems
    )
    with localcontext() as context:
        context.prec = 50
        standard_error = variance.sqrt()
        lower = point - Z_95 * standard_error
        upper = point + Z_95 * standard_error
    return (
        decimal_string(standard_error),
        decimal_string(lower),
        decimal_string(max(lower, Decimal(0))),
        decimal_string(upper),
        decimal_string(variance),
    )


def aggregate_atus_groups(
    activities: Sequence[Mapping[str, str]],
    replicate_rows: Iterable[Mapping[str, str]],
    *,
    expected_systems: int = EXPECTED_ATUS_REPLICATE_SYSTEMS,
) -> list[dict[str, str]]:
    """Aggregate code deviations inside each replicate system before squaring."""

    activity_by_code = index_unique(activities, "activity_code", "everyday activities")
    groups_by_code = {
        code: row["tier1_code"] for code, row in activity_by_code.items()
    }
    factor_by_system: dict[str, Decimal] = {}
    systems_by_code: dict[str, set[str]] = defaultdict(set)
    seen: set[tuple[str, str]] = set()
    all_deviation: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
    in_scope_deviation: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
    for raw in replicate_rows:
        row = dict(raw)
        code = row.get("activity_code", "")
        if code not in activity_by_code:
            raise InventoryError(f"replicate row refers to unknown ATUS code: {code}")
        system = row.get("replicate_system_id", "")
        key = (code, system)
        if not system or key in seen:
            raise InventoryError(f"blank or duplicate ATUS code/system replicate row: {key}")
        seen.add(key)
        factor = decimal_value(row.get("replicate_variance_factor"), "replicate variance factor")
        assert factor is not None
        previous = factor_by_system.setdefault(system, factor)
        if previous != factor:
            raise InventoryError(f"replicate factor differs within system {system}")
        central = decimal_value(row.get("central_annual_population_hours"), "replicate central")
        expected_central = decimal_value(activity_by_code[code]["annual_population_hours"], "activity central")
        if central != expected_central:
            raise InventoryError(f"replicate central differs from activity weight for {code}")
        deviation = decimal_value(
            row.get("replicate_deviation_hours"),
            "replicate deviation",
            nonnegative=False,
        )
        assert deviation is not None
        group = groups_by_code[code]
        systems_by_code[code].add(system)
        all_deviation[(group, system)] += deviation
        if activity_by_code[code]["weight_status"] in {"available", "observed_zero"}:
            in_scope_deviation[(group, system)] += deviation

    systems = sorted(factor_by_system)
    system_set = set(systems)
    if len(systems) != expected_systems:
        raise InventoryError(
            f"expected {expected_systems} ATUS replicate systems, found {len(systems)}"
        )
    for code in sorted(activity_by_code):
        if systems_by_code[code] != system_set:
            raise InventoryError(f"ATUS replicate systems are incomplete for {code}")

    grouped: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in activities:
        grouped[row["tier1_code"]].append(row)
    result: list[dict[str, str]] = []
    for group, rows in sorted(grouped.items()):
        labels = {row["first_tier_label"] for row in rows}
        classes = {row["analysis_class"] for row in rows}
        if len(labels) != 1 or len(classes) != 1:
            raise InventoryError(f"ATUS first-tier metadata is not unique for {group}")
        status_counts = Counter(row["weight_status"] for row in rows)
        all_point = sum_decimal(
            decimal_value(row["annual_population_hours"], "activity mass") for row in rows
        )
        in_scope_point = sum_decimal(
            decimal_value(row["annual_population_hours"], "activity mass")
            for row in rows
            if row["weight_status"] in {"available", "observed_zero"}
        )
        paid_point = sum_decimal(
            decimal_value(row["annual_population_hours"], "activity mass")
            for row in rows
            if row["weight_status"] == "excluded_paid_work"
        )
        data_point = sum_decimal(
            decimal_value(row["annual_population_hours"], "activity mass")
            for row in rows
            if row["weight_status"] == "excluded_data_code"
        )
        if all_point != in_scope_point + paid_point + data_point:
            raise InventoryError(f"ATUS status partition does not conserve group {group}")
        all_stats = _uncertainty(
            all_point,
            systems,
            factor_by_system,
            {system: all_deviation[(group, system)] for system in systems},
        )
        in_scope_stats = _uncertainty(
            in_scope_point,
            systems,
            factor_by_system,
            {system: in_scope_deviation[(group, system)] for system in systems},
        )
        statuses = set(status_counts)
        if statuses == {"excluded_paid_work"}:
            group_status = "excluded_paid_work"
        elif statuses == {"excluded_data_code"}:
            group_status = "excluded_data_code"
        elif statuses == {"observed_zero"}:
            group_status = "observed_zero"
        elif statuses <= {"available", "observed_zero"}:
            group_status = (
                "available_with_observed_zero" if "observed_zero" in statuses else "available"
            )
        else:
            group_status = "mixed_status"
        missing_codes = sorted(
            {
                code
                for row in rows
                for code in json.loads(row["structural_missingness_codes_json"])
            }
        )
        result.append(
            {
                "everyday_group_uid": f"atus-first-tier:2021-2025:{group}",
                "first_tier_code": group,
                "first_tier_label": next(iter(labels)),
                "analysis_class": next(iter(classes)),
                "group_definition": "ATUS_first_tier_activity_code",
                "activity_count": str(len(rows)),
                "available_activity_count": str(status_counts["available"]),
                "observed_zero_activity_count": str(status_counts["observed_zero"]),
                "excluded_paid_work_activity_count": str(status_counts["excluded_paid_work"]),
                "excluded_data_code_activity_count": str(status_counts["excluded_data_code"]),
                "evidence_packet_joined_activity_count": str(sum(row["evidence_join_status"] == "matched" for row in rows)),
                "group_weight_status": group_status,
                "status_counts_json": canonical.stable_json(dict(sorted(status_counts.items()))),
                "weight_axis": EVERYDAY_AXIS,
                "weight_variant": ATUS_VARIANT,
                "weight_unit": EVERYDAY_UNIT,
                "reference_period": "2021-2025 pooled annual average",
                "annual_population_hours_all_codes": decimal_string(all_point),
                "annual_population_hours_in_scope": decimal_string(in_scope_point),
                "annual_population_hours_excluded_paid_work": decimal_string(paid_point),
                "annual_population_hours_excluded_data_code": decimal_string(data_point),
                "all_codes_standard_error": all_stats[0],
                "all_codes_ci95_lower_unclipped": all_stats[1],
                "all_codes_ci95_lower_nonnegative": all_stats[2],
                "all_codes_ci95_upper": all_stats[3],
                "all_codes_variance": all_stats[4],
                "in_scope_standard_error": in_scope_stats[0],
                "in_scope_ci95_lower_unclipped": in_scope_stats[1],
                "in_scope_ci95_lower_nonnegative": in_scope_stats[2],
                "in_scope_ci95_upper": in_scope_stats[3],
                "in_scope_variance": in_scope_stats[4],
                "replicate_systems_expected": str(expected_systems),
                "replicate_systems_used": str(len(systems)),
                "replicate_input_status": "complete",
                "uncertainty_aggregation_method": "sum_code_deviations_within_each_replicate_system_before_squaring",
                "structural_missingness_codes_json": canonical.stable_json(missing_codes),
            }
        )
    return result


def build_summary(
    occupations: Sequence[Mapping[str, str]],
    tasks: Sequence[Mapping[str, str]],
    activities: Sequence[Mapping[str, str]],
    market_groups: Sequence[Mapping[str, str]],
    everyday_groups: Sequence[Mapping[str, str]],
    market_summary: Mapping[str, Any],
) -> dict[str, Any]:
    activity_status = Counter(row["weight_status"] for row in activities)
    task_missing = Counter(
        code
        for row in tasks
        for code in json.loads(row["structural_missingness_codes_json"])
    )
    occupation_missing = Counter(
        code
        for row in occupations
        for code in json.loads(row["structural_missingness_codes_json"])
    )
    activity_missing = Counter(
        code
        for row in activities
        for code in json.loads(row["structural_missingness_codes_json"])
    )
    total_all = sum_decimal(
        decimal_value(row["annual_population_hours_all_codes"], "ATUS group mass")
        for row in everyday_groups
    )
    total_in_scope = sum_decimal(
        decimal_value(row["annual_population_hours_in_scope"], "ATUS group mass")
        for row in everyday_groups
    )
    total_paid = sum_decimal(
        decimal_value(row["annual_population_hours_excluded_paid_work"], "ATUS group mass")
        for row in everyday_groups
    )
    total_data = sum_decimal(
        decimal_value(row["annual_population_hours_excluded_data_code"], "ATUS group mass")
        for row in everyday_groups
    )
    if total_all != total_in_scope + total_paid + total_data:
        raise InventoryError("everyday-life group partition does not conserve total hours")
    return {
        "schema_version": 1,
        "inventory_release": RELEASE,
        "method_provenance_id": METHOD,
        "release_scope": "deterministic_source_activity_inventory_before_physicality_screening",
        "source_unit_rows": len(tasks) + len(activities),
        "human_judgments": 0,
        "model_generated_labels": 0,
        "physicality_or_calibration_labels": 0,
        "axes_kept_separate": True,
        "market_work": dict(market_summary),
        "everyday_life": {
            "activity_rows": len(activities),
            "first_tier_group_rows": len(everyday_groups),
            "weight_status_counts": dict(sorted(activity_status.items())),
            "annual_population_hours_all_codes": decimal_string(total_all),
            "annual_population_hours_in_scope": decimal_string(total_in_scope),
            "annual_population_hours_excluded_paid_work": decimal_string(total_paid),
            "annual_population_hours_excluded_data_code": decimal_string(total_data),
            "replicate_systems_per_activity": EXPECTED_ATUS_REPLICATE_SYSTEMS,
            "group_uncertainty_method": "aggregate activity-code deviations within each independent-year replicate system before squaring",
            "status_precedence": [
                "first_tier_code_05=>excluded_paid_work",
                "analysis_class_data_code=>excluded_data_code",
                "zero_observed_sample_or_zero_mass=>observed_zero",
                "otherwise=>available",
            ],
        },
        "evidence": {
            "task_packet_joins": len(tasks),
            "everyday_activity_packet_joins": len(activities),
            "packet_join_status": "complete",
        },
        "hierarchy": {
            "market_task_dwa_links": sum(int(row["dwa_link_count"]) for row in tasks),
            "market_tasks_linked": sum(row["hierarchy_status"] == "linked" for row in tasks),
            "market_tasks_unlinked": sum(row["hierarchy_status"] != "linked" for row in tasks),
            "everyday_hierarchy": "ATUS_three_tier_codes_with_first_tier_groups",
        },
        "structural_missingness": {
            "occupations": dict(sorted(occupation_missing.items())),
            "occupational_tasks": dict(sorted(task_missing.items())),
            "everyday_activities": dict(sorted(activity_missing.items())),
            "missing_activity_is_zero_importance": False,
        },
        "tools_used_policy": {
            "source_release": "O*NET 30.2 final Tools Used table",
            "scope": "occupation_level_carry_forward_context_only",
            "task_requirement_inference": "prohibited",
        },
    }


def assemble_inventory() -> InventoryBundle:
    canonical.verify(CANONICAL_ROOT)
    weights.verify(WEIGHTS_ROOT)
    source_evidence.verify(EVIDENCE_ROOT)
    packet_rows = read_csv(EVIDENCE_ROOT / source_evidence.INDEX_FILENAME)
    packet_index = index_unique(packet_rows, "source_unit_uid", "source evidence packet index")
    if len(packet_index) != 19_261:
        raise InventoryError("source evidence index must contain 19,261 source units")
    occupations, tasks, market_groups, market_summary = build_market_inventory(packet_index)
    activities = build_everyday_activities(packet_index)
    everyday_groups = aggregate_atus_groups(
        activities,
        iter_csv(
            WEIGHTS_ROOT
            / "everyday_life"
            / "atus_activity_replicate_estimates.csv.gz"
        ),
    )
    summary = build_summary(
        occupations,
        tasks,
        activities,
        market_groups,
        everyday_groups,
        market_summary,
    )
    return InventoryBundle(
        occupations=occupations,
        occupational_tasks=tasks,
        everyday_activities=activities,
        market_work_groups=market_groups,
        everyday_life_groups=everyday_groups,
        summary=summary,
    )


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    temporary.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _json_artifact(path: Path) -> dict[str, Any]:
    return {
        "format": "json",
        "rows": 1,
        "bytes": path.stat().st_size,
        "sha256": canonical.sha256_file(path),
    }


def build(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    if not SCHEMA_PATH.is_file():
        raise InventoryError(f"activity inventory schema is missing: {SCHEMA_PATH}")
    output.mkdir(parents=True, exist_ok=True)
    unexpected = {
        path.name for path in output.iterdir() if path.name not in RELEASE_FILES
    }
    if unexpected:
        raise InventoryError(
            f"activity inventory output contains unexpected files: {sorted(unexpected)}"
        )
    bundle = assemble_inventory()
    catalog = canonical.OutputCatalog(output)
    tables = {
        "occupations.csv": bundle.occupations,
        "occupational_tasks.csv.gz": bundle.occupational_tasks,
        "everyday_activities.csv": bundle.everyday_activities,
        "market_work_groups.csv": bundle.market_work_groups,
        "everyday_life_groups.csv": bundle.everyday_life_groups,
    }
    primary_keys = {
        "occupations.csv": ["occupation_uid"],
        "occupational_tasks.csv.gz": ["task_uid"],
        "everyday_activities.csv": ["source_unit_uid"],
        "market_work_groups.csv": ["market_group_uid"],
        "everyday_life_groups.csv": ["everyday_group_uid"],
    }
    for filename in TABLE_FILES:
        rows = tables[filename]
        if not rows:
            raise InventoryError(f"cannot write empty inventory table {filename}")
        fields = list(rows[0])
        catalog.write_csv(
            filename,
            fields,
            rows,
            primary_key=primary_keys[filename],
            origins={
                field: (
                    canonical.ORIGIN_SOURCE
                    if field in SOURCE_NATIVE_FIELDS[filename]
                    else canonical.ORIGIN_DERIVED
                )
                for field in fields
            },
        )
    _write_json(output / "summary.json", bundle.summary)

    artifacts: dict[str, Any] = {}
    for filename, record in sorted(catalog.tables.items()):
        artifacts[filename] = {
            "format": "csv_gzip" if filename.endswith(".gz") else "csv",
            "rows": record.rows,
            "fields": record.fields,
            "primary_key": record.primary_key,
            "field_origins": catalog.field_origins[filename],
            "bytes": record.bytes,
            "sha256": record.sha256,
        }
    artifacts["summary.json"] = _json_artifact(output / "summary.json")
    manifest = {
        "schema_version": 1,
        "inventory_release": RELEASE,
        "method_provenance_id": METHOD,
        "complete": True,
        "production_eligible_as_source_inventory": True,
        "human_judgments_included": False,
        "model_generated_labels_included": False,
        "physicality_or_calibration_labels_included": False,
        "canonical_manifest_sha256": canonical.sha256_file(CANONICAL_ROOT / "manifest.json"),
        "weights_manifest_sha256": canonical.sha256_file(WEIGHTS_ROOT / "manifest.json"),
        "source_evidence_manifest_sha256": canonical.sha256_file(EVIDENCE_ROOT / "manifest.json"),
        "schema_path": "schemas/activity_inventory_release.schema.json",
        "schema_sha256": canonical.sha256_file(SCHEMA_PATH),
        "axes": [
            {"axis": MARKET_AXIS, "unit": MARKET_UNIT, "stream": "market_work"},
            {"axis": EVERYDAY_AXIS, "unit": EVERYDAY_UNIT, "stream": "everyday_life"},
        ],
        "task_weight_variants": list(VARIANTS),
        "central_task_weight_variant": CENTRAL_VARIANT,
        "tools_used_policy": "O*NET 30.2 occupation-level carry-forward context only; task-requirement inference is prohibited",
        "atus_status_precedence": [
            "excluded_paid_work",
            "excluded_data_code",
            "observed_zero",
            "available",
        ],
        "atus_group_uncertainty_method": "sum_code_deviations_within_each_replicate_system_before_squaring",
        "artifacts": dict(sorted(artifacts.items())),
    }
    _write_json(output / "manifest.json", manifest)
    return manifest


def _compare_rows(
    actual: Sequence[Mapping[str, str]],
    expected: Sequence[Mapping[str, str]],
    label: str,
) -> None:
    if len(actual) != len(expected):
        raise InventoryError(f"{label} has {len(actual)} rows; expected {len(expected)}")
    for index, (left, right) in enumerate(zip(actual, expected), start=1):
        if dict(left) != dict(right):
            raise InventoryError(f"{label} differs from deterministic reconstruction at row {index}")


def verify(output: Path = DEFAULT_OUTPUT, *, deep: bool = True) -> dict[str, Any]:
    canonical.verify(CANONICAL_ROOT)
    weights.verify(WEIGHTS_ROOT)
    source_evidence.verify(EVIDENCE_ROOT)
    manifest = read_json(output / "manifest.json")
    if manifest.get("inventory_release") != RELEASE or manifest.get("complete") is not True:
        raise InventoryError("activity inventory manifest is not a complete v1 release")
    expected_manifest_contract = {
        "schema_version": 1,
        "method_provenance_id": METHOD,
        "production_eligible_as_source_inventory": True,
        "human_judgments_included": False,
        "model_generated_labels_included": False,
        "physicality_or_calibration_labels_included": False,
        "schema_path": "schemas/activity_inventory_release.schema.json",
        "task_weight_variants": list(VARIANTS),
        "central_task_weight_variant": CENTRAL_VARIANT,
        "atus_status_precedence": [
            "excluded_paid_work",
            "excluded_data_code",
            "observed_zero",
            "available",
        ],
        "atus_group_uncertainty_method": "sum_code_deviations_within_each_replicate_system_before_squaring",
    }
    for field, expected_value in expected_manifest_contract.items():
        if manifest.get(field) != expected_value:
            raise InventoryError(f"activity inventory manifest violates {field}")
    expected_axes = {
        (MARKET_AXIS, MARKET_UNIT, "market_work"),
        (EVERYDAY_AXIS, EVERYDAY_UNIT, "everyday_life"),
    }
    actual_axes = {
        (row.get("axis"), row.get("unit"), row.get("stream"))
        for row in manifest.get("axes", [])
        if isinstance(row, Mapping)
    }
    if actual_axes != expected_axes or len(manifest.get("axes", [])) != 2:
        raise InventoryError("activity inventory manifest mixes or omits weighting axes")
    upstream = {
        "canonical_manifest_sha256": canonical.sha256_file(CANONICAL_ROOT / "manifest.json"),
        "weights_manifest_sha256": canonical.sha256_file(WEIGHTS_ROOT / "manifest.json"),
        "source_evidence_manifest_sha256": canonical.sha256_file(EVIDENCE_ROOT / "manifest.json"),
        "schema_sha256": canonical.sha256_file(SCHEMA_PATH),
    }
    for field, value in upstream.items():
        if manifest.get(field) != value:
            raise InventoryError(f"activity inventory has a stale {field}")
    if set(manifest.get("artifacts", {})) != set(TABLE_FILES) | {"summary.json"}:
        raise InventoryError("activity inventory manifest has the wrong artifact inventory")
    actual_files = {path.name for path in output.iterdir() if path.is_file()}
    if actual_files != RELEASE_FILES:
        raise InventoryError(
            f"activity inventory directory has unexpected or missing files: {sorted(actual_files ^ RELEASE_FILES)}"
        )
    total_bytes = 0
    for filename, record in manifest["artifacts"].items():
        path = output / filename
        if (
            not path.is_file()
            or path.stat().st_size != record["bytes"]
            or canonical.sha256_file(path) != record["sha256"]
        ):
            raise InventoryError(f"activity inventory artifact identity failed: {filename}")
        total_bytes += path.stat().st_size
        if filename in TABLE_FILES:
            rows = read_csv(path)
            expected_format = "csv_gzip" if filename.endswith(".gz") else "csv"
            if record.get("format") != expected_format:
                raise InventoryError(f"activity inventory format contract failed: {filename}")
            if len(rows) != record["rows"]:
                raise InventoryError(f"activity inventory row count failed: {filename}")
            if list(rows[0]) != record["fields"]:
                raise InventoryError(f"activity inventory field contract failed: {filename}")
            if set(record.get("field_origins", {})) != set(record["fields"]):
                raise InventoryError(f"activity inventory field-origin contract failed: {filename}")
            if not set(record["primary_key"]) <= set(record["fields"]):
                raise InventoryError(f"activity inventory primary-key contract failed: {filename}")
            seen: set[tuple[str, ...]] = set()
            for row in rows:
                key = tuple(row[field] for field in record["primary_key"])
                if any(not value for value in key) or key in seen:
                    raise InventoryError(f"activity inventory primary key failed: {filename}:{key}")
                seen.add(key)

    if deep:
        expected = assemble_inventory()
        actual_tables = {
            "occupations": read_csv(output / "occupations.csv"),
            "occupational_tasks": read_csv(output / "occupational_tasks.csv.gz"),
            "everyday_activities": read_csv(output / "everyday_activities.csv"),
            "market_work_groups": read_csv(output / "market_work_groups.csv"),
            "everyday_life_groups": read_csv(output / "everyday_life_groups.csv"),
        }
        for name, actual in actual_tables.items():
            _compare_rows(actual, getattr(expected, name), name)
            if any(
                "physicality" in field.lower() or "calibration" in field.lower()
                for field in actual[0]
            ):
                raise InventoryError(f"{name} contains a prohibited downstream label field")
        if read_json(output / "summary.json") != expected.summary:
            raise InventoryError("summary differs from deterministic reconstruction")
    return {
        "ok": True,
        "inventory_release": RELEASE,
        "table_count": len(TABLE_FILES),
        "source_unit_rows": 19_261,
        "occupation_rows": manifest["artifacts"]["occupations.csv"]["rows"],
        "occupational_task_rows": manifest["artifacts"]["occupational_tasks.csv.gz"]["rows"],
        "everyday_activity_rows": manifest["artifacts"]["everyday_activities.csv"]["rows"],
        "market_group_rows": manifest["artifacts"]["market_work_groups.csv"]["rows"],
        "everyday_group_rows": manifest["artifacts"]["everyday_life_groups.csv"]["rows"],
        "manifest_sha256": canonical.sha256_file(output / "manifest.json"),
        "artifact_bytes": total_bytes,
        "deep_reconstruction_verified": deep,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "verify"])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--shallow", action="store_true", help="skip deterministic row reconstruction during verify")
    args = parser.parse_args(argv)
    try:
        result = (
            build(args.output)
            if args.command == "build"
            else verify(args.output, deep=not args.shallow)
        )
    except (
        InventoryError,
        canonical.CanonicalError,
        weights.WeightError,
        source_evidence.EvidenceError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
