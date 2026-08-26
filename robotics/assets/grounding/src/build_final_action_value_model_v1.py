"""Build the final action, capability, value, and policy-view model.

The established source-level physical-mass ledger is preserved. Each source's
robot-relevant validated physical mass is divided equally among its recovered
atomic action occurrences, then aggregated through the final action groups.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter, defaultdict
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path

import build_action_reuse_candidates_v1 as files
import build_capability_semantic_profiles as semantic
import build_thresholded_capability_requirements_v1 as old_requirements


getcontext().prec = max(getcontext().prec, 96)

GROUNDING_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = GROUNDING_ROOT.parent
DERIVED_ROOT = GROUNDING_ROOT / "data" / "derived"

FINAL_CAPABILITY_ROOT = (
    DERIVED_ROOT / "corrected_action_capability_dedup_final_v1"
)
ACTION_CAPABILITIES = (
    FINAL_CAPABILITY_ROOT / "action_group_canonical_capabilities.jsonl.gz"
)
FINAL_PROFILE_MAP = FINAL_CAPABILITY_ROOT / "profile_to_canonical.jsonl.gz"
FINAL_CANONICAL = FINAL_CAPABILITY_ROOT / "canonical_capabilities.jsonl.gz"
FINAL_CAPABILITY_RELEASE = FINAL_CAPABILITY_ROOT / "release_manifest.json"

NEW_GENERATION_ROOT = (
    DERIVED_ROOT / "corrected_action_capability_generation_v4_batch_v1"
)
NEW_MENTIONS = NEW_GENERATION_ROOT / "capability_mentions.jsonl.gz"
NEW_GENERATION_RELEASE = NEW_GENERATION_ROOT / "release_manifest.json"
NEW_MENTION_MAP = FINAL_CAPABILITY_ROOT / "mention_to_canonical.jsonl.gz"

OLD_REQUIREMENT_ROOT = DERIVED_ROOT / "thresholded_capability_requirements_v1"
OLD_ACTION_REQUIREMENTS = (
    OLD_REQUIREMENT_ROOT / "action_capability_requirements.jsonl.gz"
)
OLD_REQUIREMENT_RELEASE = OLD_REQUIREMENT_ROOT / "release_manifest.json"

ACTION_GROUP_ROOT = DERIVED_ROOT / "deduplicated_action_groups_v3"
OCCURRENCE_GROUP_MAP = ACTION_GROUP_ROOT / "occurrence_group_map.jsonl.gz"
ACTION_GROUP_RELEASE = ACTION_GROUP_ROOT / "release_manifest.json"

WEIGHT_ROOT = DERIVED_ROOT / "action_weights_v1"
SOURCE_ACCOUNTING = WEIGHT_ROOT / "source_weight_accounting.jsonl.gz"
OLD_OCCURRENCE_ALLOCATIONS = (
    WEIGHT_ROOT / "occurrence_weight_allocations.jsonl.gz"
)
WEIGHT_RELEASE = WEIGHT_ROOT / "release_manifest.json"

ELIGIBILITY_ROOT = DERIVED_ROOT / "robot_task_eligibility_v1"
ELIGIBILITY = ELIGIBILITY_ROOT / "eligibility_decisions.jsonl.gz"
ELIGIBILITY_RELEASE = ELIGIBILITY_ROOT / "release_manifest.json"

COVERAGE_ROOT = DERIVED_ROOT / "activity_domain_coverage_v1"
COVERAGE_TARGETS = COVERAGE_ROOT / "coverage_targets.jsonl.gz"
COVERAGE_RELEASE = COVERAGE_ROOT / "release_manifest.json"

OLD_DEDUP_ROOT = DERIVED_ROOT / "simulation_capability_dedup_final_full_v2"
OLD_EDGE_DISPOSITIONS = (
    OLD_DEDUP_ROOT / "confirmed_edge_dispositions.jsonl.gz"
)
OLD_PROFILE_MAP = OLD_DEDUP_ROOT / "profile_to_canonical.jsonl.gz"
OLD_DEDUP_RELEASE = OLD_DEDUP_ROOT / "release_manifest.json"
NEW_EDGE_DISPOSITIONS = (
    FINAL_CAPABILITY_ROOT / "confirmed_edge_dispositions.jsonl.gz"
)

PROTOCOL = (
    GROUNDING_ROOT
    / "experiments"
    / "capability_selection_v2"
    / "protocol.json"
)

DEFAULT_OUTPUT = DERIVED_ROOT / "final_action_value_model_v1"
RELEASE_ID = "final-action-value-model-v1"

MARKET_AXIS = "market_work_economic_value_usd"
EVERYDAY_AXIS = "everyday_life_annual_population_hours"
AXES = (MARKET_AXIS, EVERYDAY_AXIS)
DOMAINS = ("robot_capabilities", "physics_capabilities")
ZERO = Decimal(0)
TOLERANCE = Decimal("1e-18")


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def decimal(value: object) -> Decimal:
    if value is None or str(value).strip() == "":
        return ZERO
    return Decimal(str(value))


def decimal_text(value: Decimal) -> str:
    if value == ZERO:
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def unit_fraction(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise RuntimeError("fraction denominator is not positive")
    value = numerator / denominator
    if abs(value) <= TOLERANCE:
        return ZERO
    if abs(value - Decimal(1)) <= TOLERANCE:
        return Decimal(1)
    if value < ZERO or value > Decimal(1):
        raise RuntimeError(f"fraction is outside [0, 1]: {value}")
    return value


def target_uid(source_uid: str) -> str:
    if source_uid.startswith("atus-activity:"):
        return source_uid
    parts = source_uid.split(":")
    if len(parts) != 4 or parts[0] != "onet":
        raise RuntimeError(f"unexpected weighted source UID: {source_uid}")
    return ":".join(parts[:3])


def exact_group_allocation(
    total: Decimal,
    group_counts: dict[str, int],
) -> dict[str, Decimal]:
    if total < ZERO:
        raise RuntimeError("cannot allocate negative source mass")
    if total == ZERO or not group_counts:
        return {}
    denominator = sum(group_counts.values())
    if denominator <= 0:
        raise RuntimeError("source action count is not positive")
    result: dict[str, Decimal] = {}
    assigned = ZERO
    ordered = sorted(group_counts.items())
    for position, (group_id, count) in enumerate(ordered):
        if count <= 0:
            raise RuntimeError("group occurrence count is not positive")
        value = (
            total - assigned
            if position == len(ordered) - 1
            else total * Decimal(count) / Decimal(denominator)
        )
        result[group_id] = value
        assigned += value
    if assigned != total:
        raise RuntimeError("source action allocation does not conserve mass")
    return result


def lean_capability(
    capability: dict[str, object],
) -> dict[str, object]:
    return {
        "canonical_capability_id": capability[
            "canonical_capability_id"
        ],
        "canonical_name": capability["canonical_name"],
        "requirement_level": capability["requirement_level"],
        "sample_support": capability["sample_support"],
        "samples_present": capability["samples_present"],
        "sample_evidence": capability["sample_evidence"],
    }


def build_new_requirements(
    new_mentions: list[dict[str, object]],
    mapped_mentions: list[dict[str, object]],
    canonical_by_id: dict[str, dict[str, object]],
) -> dict[str, dict[str, list[dict[str, object]]]]:
    if len(new_mentions) != len(mapped_mentions):
        raise RuntimeError("new mention and mapped-mention counts differ")
    mapped_by_index = {
        int(row["mention_index"]): row for row in mapped_mentions
    }
    if len(mapped_by_index) != len(mapped_mentions):
        raise RuntimeError("mapped mention indices are not unique")

    observations: dict[
        tuple[str, str, str], dict[int, list[dict[str, object]]]
    ] = defaultdict(lambda: defaultdict(list))
    for mention_index, mention in enumerate(new_mentions):
        mapped = mapped_by_index.get(mention_index)
        if mapped is None:
            raise RuntimeError(f"new mention is unmapped: {mention_index}")
        for field in ("group_id", "sample_index", "domain"):
            if mention[field] != mapped[field]:
                raise RuntimeError(
                    f"new mention mapping differs at {mention_index}"
                )
        capability_id = str(mapped["canonical_capability_id"])
        if capability_id not in canonical_by_id:
            raise RuntimeError("new mention references unknown capability")
        level = old_requirements.mention_requirement_level(
            dict(mention["importance"])
        )
        key = (
            str(mention["group_id"]),
            str(mention["domain"]),
            capability_id,
        )
        observations[key][int(mention["sample_index"])].append(
            {
                "source_mention_index": mention_index,
                "generated_name": mention["name"],
                "importance": mention["importance"],
                "requirement_level": old_requirements.fraction_record(
                    level
                ),
            }
        )

    result: dict[str, dict[str, list[dict[str, object]]]] = defaultdict(
        lambda: {domain: [] for domain in DOMAINS}
    )
    for (group_id, domain, capability_id), by_sample in observations.items():
        sample_rows = []
        sample_levels = []
        for sample_index in sorted(by_sample):
            mentions = by_sample[sample_index]
            maximum = max(
                Fraction(
                    int(row["requirement_level"]["numerator"]),
                    int(row["requirement_level"]["denominator"]),
                )
                for row in mentions
            )
            sample_levels.append(maximum)
            sample_rows.append(
                {
                    "sample_index": sample_index,
                    "sample_requirement_level": (
                        old_requirements.fraction_record(maximum)
                    ),
                    "mentions": sorted(
                        mentions,
                        key=lambda row: int(
                            row["source_mention_index"]
                        ),
                    ),
                }
            )
        level = sum(sample_levels, Fraction(0, 1)) / len(sample_levels)
        support = Fraction(len(sample_rows), 2)
        canonical = canonical_by_id[capability_id]
        result[group_id][domain].append(
            {
                "canonical_capability_id": capability_id,
                "canonical_name": canonical["canonical_name"],
                "requirement_level": old_requirements.fraction_record(
                    level
                ),
                "sample_support": old_requirements.fraction_record(support),
                "samples_present": len(sample_rows),
                "sample_evidence": sample_rows,
            }
        )
    for domains in result.values():
        for domain in DOMAINS:
            domains[domain].sort(
                key=lambda row: (
                    -float(row["requirement_level"]["decimal"]),
                    str(row["canonical_name"]),
                    str(row["canonical_capability_id"]),
                )
            )
    return result


def canonical_direct_equivalences(
    final_profile_rows: list[dict[str, object]],
    old_profile_rows: list[dict[str, object]],
    old_edges: list[dict[str, object]],
    new_edges: list[dict[str, object]],
    canonical_by_id: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    final_by_profile = {
        str(row["profile_id"]): row for row in final_profile_rows
    }
    old_profile_by_index = {
        int(row["profile_index"]): str(row["profile_id"])
        for row in old_profile_rows
    }
    evidence: dict[
        tuple[str, str, str], list[dict[str, object]]
    ] = defaultdict(list)

    def add(
        edge: dict[str, object],
        left_profile_id: str,
        right_profile_id: str,
        source: str,
    ) -> None:
        left = final_by_profile[left_profile_id]
        right = final_by_profile[right_profile_id]
        left_canonical = str(left["canonical_capability_id"])
        right_canonical = str(right["canonical_capability_id"])
        if left_canonical == right_canonical:
            return
        first, second = sorted((left_canonical, right_canonical))
        key = (str(edge["domain"]), first, second)
        evidence[key].append(
            {
                "edge_id": edge["id"],
                "left_profile_id": left_profile_id,
                "right_profile_id": right_profile_id,
                "cosine_similarity": edge["cosine_similarity"],
                "review_source": source,
            }
        )

    for edge in old_edges:
        add(
            edge,
            old_profile_by_index[int(edge["left_index"])],
            old_profile_by_index[int(edge["right_index"])],
            "existing_catalog_review",
        )
    for edge in new_edges:
        add(
            edge,
            str(edge["left_profile_id"]),
            str(edge["right_profile_id"]),
            "corrected_profile_review",
        )

    rows = []
    for (domain, left, right), edge_evidence in sorted(evidence.items()):
        rows.append(
            {
                "domain": domain,
                "left_canonical_capability_id": left,
                "left_canonical_name": canonical_by_id[left][
                    "canonical_name"
                ],
                "right_canonical_capability_id": right,
                "right_canonical_name": canonical_by_id[right][
                    "canonical_name"
                ],
                "direct_equivalence_only": True,
                "transitive_closure_allowed": False,
                "supporting_profile_edge_count": len(edge_evidence),
                "evidence": sorted(
                    edge_evidence, key=lambda row: str(row["edge_id"])
                ),
            }
        )
    return rows


def build(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    required = (
        ACTION_CAPABILITIES,
        FINAL_PROFILE_MAP,
        FINAL_CANONICAL,
        FINAL_CAPABILITY_RELEASE,
        NEW_MENTIONS,
        NEW_GENERATION_RELEASE,
        NEW_MENTION_MAP,
        OLD_ACTION_REQUIREMENTS,
        OLD_REQUIREMENT_RELEASE,
        OCCURRENCE_GROUP_MAP,
        ACTION_GROUP_RELEASE,
        SOURCE_ACCOUNTING,
        OLD_OCCURRENCE_ALLOCATIONS,
        WEIGHT_RELEASE,
        ELIGIBILITY,
        ELIGIBILITY_RELEASE,
        COVERAGE_TARGETS,
        COVERAGE_RELEASE,
        OLD_EDGE_DISPOSITIONS,
        OLD_PROFILE_MAP,
        OLD_DEDUP_RELEASE,
        NEW_EDGE_DISPOSITIONS,
        PROTOCOL,
    )
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"missing required input: {path}")

    action_capability_rows = files.read_jsonl_gz(ACTION_CAPABILITIES)
    canonical_rows = files.read_jsonl_gz(FINAL_CANONICAL)
    final_profile_rows = files.read_jsonl_gz(FINAL_PROFILE_MAP)
    canonical_by_id = {
        str(row["canonical_capability_id"]): row
        for row in canonical_rows
    }
    old_requirement_rows = files.read_jsonl_gz(
        OLD_ACTION_REQUIREMENTS
    )
    old_requirement_by_group = {
        str(row["group_id"]): row for row in old_requirement_rows
    }
    new_requirements = build_new_requirements(
        files.read_jsonl_gz(NEW_MENTIONS),
        files.read_jsonl_gz(NEW_MENTION_MAP),
        canonical_by_id,
    )

    action_requirements = []
    action_by_group = {}
    origin_counts: Counter[str] = Counter()
    level_distribution: Counter[str] = Counter()
    for expected_index, action in enumerate(action_capability_rows):
        if int(action["action_group_index"]) != expected_index:
            raise RuntimeError("final action index is not contiguous")
        group_id = str(action["action_group_id"])
        origin = str(action["group_origin"])
        origin_counts.update([origin])
        if origin == "existing_action_group":
            old = old_requirement_by_group.get(group_id)
            if old is None:
                raise RuntimeError(
                    f"existing group lacks requirements: {group_id}"
                )
            capabilities = {
                domain: [
                    lean_capability(capability)
                    for capability in old[domain]
                ]
                for domain in DOMAINS
            }
        elif origin == "new_corrected_action_group":
            capabilities = new_requirements.get(group_id)
            if capabilities is None:
                raise RuntimeError(
                    f"new group lacks requirements: {group_id}"
                )
            capabilities = copy.deepcopy(capabilities)
        else:
            raise RuntimeError(f"unexpected action origin: {origin}")

        for domain in DOMAINS:
            expected_capabilities = {
                str(row["canonical_capability_id"])
                for row in action[domain]
            }
            actual_capabilities = {
                str(row["canonical_capability_id"])
                for row in capabilities[domain]
            }
            if expected_capabilities != actual_capabilities:
                raise RuntimeError(
                    f"requirement mapping differs for {group_id}"
                )
            for capability in capabilities[domain]:
                level = capability["requirement_level"]
                level_distribution[
                    f"{level['numerator']}/{level['denominator']}"
                ] += 1
        record = {
            "action_group_index": expected_index,
            "action_group_id": group_id,
            "representative_action": action["representative_action"],
            "representative_action_occurrence_id": action[
                "representative_action_occurrence_id"
            ],
            "action_occurrence_count": action[
                "action_occurrence_count"
            ],
            "group_origin": origin,
            "robot_capabilities": capabilities["robot_capabilities"],
            "physics_capabilities": capabilities[
                "physics_capabilities"
            ],
        }
        action_requirements.append(record)
        action_by_group[group_id] = record

    if len(action_requirements) != 9_363:
        raise RuntimeError("expected 9,363 final action groups")

    eligibility_rows = files.read_jsonl_gz(ELIGIBILITY)
    ineligible_old_groups = {
        str(row["group_id"])
        for row in eligibility_rows
        if row["decision"] == "ineligible_internal_human_biology"
    }
    ineligible_mass_by_source: defaultdict[str, Decimal] = defaultdict(
        Decimal
    )
    for row in files.read_jsonl_gz(OLD_OCCURRENCE_ALLOCATIONS):
        if (
            row.get("group_id") in ineligible_old_groups
            and row.get("occurrence_weight_point") not in (None, "")
        ):
            ineligible_mass_by_source[
                str(row["source_unit_uid"])
            ] += decimal(row["occurrence_weight_point"])

    occurrences_by_source: defaultdict[
        str, list[dict[str, object]]
    ] = defaultdict(list)
    for row in files.read_jsonl_gz(OCCURRENCE_GROUP_MAP):
        group_id = str(row["action_group_id"])
        if group_id not in action_by_group:
            raise RuntimeError("occurrence references unknown final group")
        occurrences_by_source[str(row["source_unit_uid"])].append(row)

    coverage_target_rows = files.read_jsonl_gz(COVERAGE_TARGETS)
    target_metadata = {
        str(row["target_uid"]): row for row in coverage_target_rows
    }
    if len(target_metadata) != len(coverage_target_rows):
        raise RuntimeError("coverage target IDs are not unique")

    source_allocation_rows = []
    source_residual_rows = []
    target_denominators: defaultdict[str, Decimal] = defaultdict(Decimal)
    target_group_mass: defaultdict[
        tuple[str, str], Decimal
    ] = defaultdict(Decimal)
    group_axis_mass: defaultdict[
        tuple[str, str], Decimal
    ] = defaultdict(Decimal)
    denominator_by_axis: defaultdict[str, Decimal] = defaultdict(Decimal)
    mapped_by_axis: defaultdict[str, Decimal] = defaultdict(Decimal)

    source_accounting_rows = files.read_jsonl_gz(SOURCE_ACCOUNTING)
    for source in source_accounting_rows:
        source_uid = str(source["source_unit_uid"])
        axis = str(source["weight_axis"])
        if axis not in AXES:
            raise RuntimeError(f"unexpected value axis: {axis}")
        if source["allocated_group_mass"] in (None, ""):
            robot_mass = ZERO
        else:
            robot_mass = (
                decimal(source["allocated_group_mass"])
                + decimal(source["quarantined_action_mass"])
                - ineligible_mass_by_source[source_uid]
            )
        if robot_mass < -TOLERANCE:
            raise RuntimeError(
                f"source robot mass is negative: {source_uid}"
            )
        if robot_mass < ZERO:
            robot_mass = ZERO
        target = target_uid(source_uid)
        if target not in target_metadata:
            raise RuntimeError(f"source target is missing: {target}")
        target_denominators[target] += robot_mass
        denominator_by_axis[axis] += robot_mass

        occurrences = occurrences_by_source.get(source_uid, [])
        group_counts = Counter(
            str(row["action_group_id"]) for row in occurrences
        )
        allocations = exact_group_allocation(robot_mass, group_counts)
        if allocations:
            mapped_by_axis[axis] += robot_mass
        elif robot_mass > ZERO:
            source_residual_rows.append(
                {
                    "source_unit_uid": source_uid,
                    "target_uid": target,
                    "weight_axis": axis,
                    "unmapped_robot_relevant_validated_physical_mass": (
                        decimal_text(robot_mass)
                    ),
                    "reason": "no_recovered_robot_action",
                }
            )
        occurrence_count = sum(group_counts.values())
        for group_id, allocated_mass in allocations.items():
            count = group_counts[group_id]
            source_allocation_rows.append(
                {
                    "source_unit_uid": source_uid,
                    "target_uid": target,
                    "weight_axis": axis,
                    "source_robot_relevant_validated_physical_mass": (
                        decimal_text(robot_mass)
                    ),
                    "source_atomic_action_occurrences": occurrence_count,
                    "action_group_id": group_id,
                    "group_occurrences_in_source": count,
                    "allocation_share": {
                        "numerator": count,
                        "denominator": occurrence_count,
                    },
                    "allocated_point_mass": decimal_text(allocated_mass),
                }
            )
            target_group_mass[(target, group_id)] += allocated_mass
            group_axis_mass[(group_id, axis)] += allocated_mass

    for target, metadata in target_metadata.items():
        expected = decimal(
            metadata["mass_accounting"][
                "robot_relevant_validated_physical_mass"
            ]
        )
        if target_denominators[target] != expected:
            raise RuntimeError(
                f"target denominator changed: {target}: "
                f"{target_denominators[target]} != {expected}"
            )

    action_target_rows = []
    for (target, group_id), mass in sorted(target_group_mass.items()):
        metadata = target_metadata[target]
        action_target_rows.append(
            {
                "action_group_id": group_id,
                "representative_action": action_by_group[group_id][
                    "representative_action"
                ],
                "target_uid": target,
                "target_label": metadata["label"],
                "target_type": metadata["target_type"],
                "weight_axis": metadata["weight_axis"],
                "allocated_point_mass": decimal_text(mass),
                "share_of_target_robot_relevant_validated_physical_mass": (
                    decimal_text(
                        unit_fraction(
                            mass, target_denominators[target]
                        )
                    )
                ),
            }
        )

    action_target_counts: Counter[str] = Counter(
        row["action_group_id"] for row in action_target_rows
    )
    action_value_rows = []
    for action in action_requirements:
        group_id = str(action["action_group_id"])
        action_value_rows.append(
            {
                "action_group_index": action["action_group_index"],
                "action_group_id": group_id,
                "representative_action": action[
                    "representative_action"
                ],
                "market_work_economic_value_usd": decimal_text(
                    group_axis_mass[(group_id, MARKET_AXIS)]
                ),
                "everyday_life_annual_population_hours": decimal_text(
                    group_axis_mass[(group_id, EVERYDAY_AXIS)]
                ),
                "positive_value_target_count": action_target_counts[
                    group_id
                ],
            }
        )

    view_specs = (
        ("economic_value", "occupation", None, "mass"),
        ("occupation_breadth", "occupation", None, "uniform"),
        ("soc_major_breadth", "occupation", "soc_major:", "uniform"),
        (
            "strategic_domain_breadth",
            "occupation",
            "strategic:",
            "uniform",
        ),
        (
            "stem_research_breadth",
            "occupation",
            "stem_research:",
            "uniform",
        ),
        ("personal_time", "everyday_activity", None, "mass"),
        (
            "personal_activity_breadth",
            "everyday_activity",
            None,
            "uniform",
        ),
        (
            "personal_domain_breadth",
            "everyday_activity",
            "atus_first_tier:",
            "uniform",
        ),
    )
    policy_unit_rows = []
    policy_edge_rows = []
    view_summaries = {}
    for view_id, target_type, membership_prefix, weighting in view_specs:
        unit_members: defaultdict[str, list[str]] = defaultdict(list)
        for target, metadata in target_metadata.items():
            if (
                metadata["target_type"] != target_type
                or target_denominators[target] <= ZERO
            ):
                continue
            if membership_prefix is None:
                unit_members[target].append(target)
            else:
                matches = [
                    str(value)
                    for value in metadata["policy_memberships"]
                    if str(value).startswith(membership_prefix)
                ]
                for membership in matches:
                    unit_members[membership].append(target)
        if not unit_members:
            raise RuntimeError(f"policy view has no units: {view_id}")

        unit_denominators = {
            unit: sum(
                (target_denominators[target] for target in members),
                ZERO,
            )
            for unit, members in unit_members.items()
        }
        if weighting == "mass":
            view_denominator = sum(unit_denominators.values(), ZERO)
            normalization = {
                unit: denominator / view_denominator
                for unit, denominator in unit_denominators.items()
            }
        else:
            normalization = {
                unit: Decimal(1) / Decimal(len(unit_members))
                for unit in unit_members
            }
        if abs(sum(normalization.values(), ZERO) - Decimal(1)) > TOLERANCE:
            raise RuntimeError(f"policy weights do not sum to one: {view_id}")

        view_edge_count = 0
        raw_upper = ZERO
        for unit in sorted(unit_members):
            members = sorted(unit_members[unit])
            denominator = unit_denominators[unit]
            group_mass: defaultdict[str, Decimal] = defaultdict(Decimal)
            for target in members:
                for (edge_target, group_id), mass in target_group_mass.items():
                    if edge_target == target:
                        group_mass[group_id] += mass
            catalogued_mass = sum(group_mass.values(), ZERO)
            raw_upper += (
                normalization[unit]
                * unit_fraction(catalogued_mass, denominator)
            )
            if membership_prefix is None:
                label = str(target_metadata[unit]["label"])
            else:
                label = unit.split(":", 1)[1].replace("_", " ").title()
            value_axis = (
                MARKET_AXIS
                if target_type == "occupation"
                else EVERYDAY_AXIS
            )
            policy_unit_id = f"{view_id}|{unit}"
            policy_unit_rows.append(
                {
                    "policy_unit_id": policy_unit_id,
                    "view_id": view_id,
                    "base_unit_id": unit,
                    "label": label,
                    "target_type": target_type,
                    "member_target_uids": members,
                    "member_target_count": len(members),
                    "value_axis": value_axis,
                    "robot_relevant_validated_physical_mass": decimal_text(
                        denominator
                    ),
                    "catalogued_action_mass": decimal_text(
                        catalogued_mass
                    ),
                    "catalogued_upper_bound_fraction": decimal_text(
                        unit_fraction(catalogued_mass, denominator)
                    ),
                    "normalization_weight": decimal_text(
                        normalization[unit]
                    ),
                    "unit_weighting": weighting,
                }
            )
            for group_id, mass in sorted(group_mass.items()):
                policy_edge_rows.append(
                    {
                        "policy_unit_id": policy_unit_id,
                        "view_id": view_id,
                        "action_group_id": group_id,
                        "allocated_point_mass": decimal_text(mass),
                        "share_of_unit_mass": decimal_text(
                            unit_fraction(mass, denominator)
                        ),
                    }
                )
                view_edge_count += 1
        view_summaries[view_id] = {
            "policy_units": len(unit_members),
            "policy_unit_action_edges": view_edge_count,
            "unit_weighting": weighting,
            "catalogued_full_coverage_upper_bound": decimal_text(
                (
                    Decimal(1)
                    if abs(raw_upper - Decimal(1)) <= TOLERANCE
                    else raw_upper
                )
            ),
        }

    capability_target_mass: defaultdict[
        tuple[str, str], Decimal
    ] = defaultdict(Decimal)
    for row in action_target_rows:
        group_id = str(row["action_group_id"])
        requirements = action_by_group[group_id]
        capabilities = [
            (domain, capability)
            for domain in DOMAINS
            for capability in requirements[domain]
        ]
        level_sum = sum(
            (
                Fraction(
                    int(capability["requirement_level"]["numerator"]),
                    int(capability["requirement_level"]["denominator"]),
                )
                for _, capability in capabilities
            ),
            Fraction(0, 1),
        )
        if level_sum <= 0:
            raise RuntimeError(f"action has no positive requirements: {group_id}")
        mass = decimal(row["allocated_point_mass"])
        for _, capability in capabilities:
            level = Fraction(
                int(capability["requirement_level"]["numerator"]),
                int(capability["requirement_level"]["denominator"]),
            )
            share = (
                Decimal(level.numerator)
                / Decimal(level.denominator)
                / (
                    Decimal(level_sum.numerator)
                    / Decimal(level_sum.denominator)
                )
            )
            capability_target_mass[
                (
                    str(capability["canonical_capability_id"]),
                    str(row["target_uid"]),
                )
            ] += mass * share

    capability_target_rows = []
    capability_axis_mass: defaultdict[
        tuple[str, str], Decimal
    ] = defaultdict(Decimal)
    capability_target_counts: Counter[str] = Counter()
    for (capability_id, target), mass in sorted(
        capability_target_mass.items()
    ):
        metadata = target_metadata[target]
        capability_target_rows.append(
            {
                "canonical_capability_id": capability_id,
                "canonical_name": canonical_by_id[capability_id][
                    "canonical_name"
                ],
                "domain": canonical_by_id[capability_id]["domain"],
                "target_uid": target,
                "target_label": metadata["label"],
                "target_type": metadata["target_type"],
                "weight_axis": metadata["weight_axis"],
                "allocated_point_mass": decimal_text(mass),
            }
        )
        capability_axis_mass[
            (capability_id, str(metadata["weight_axis"]))
        ] += mass
        capability_target_counts.update([capability_id])

    capability_value_rows = []
    for canonical in canonical_rows:
        capability_id = str(canonical["canonical_capability_id"])
        capability_value_rows.append(
            {
                "canonical_capability_id": capability_id,
                "canonical_name": canonical["canonical_name"],
                "domain": canonical["domain"],
                "market_work_economic_value_usd": decimal_text(
                    capability_axis_mass[(capability_id, MARKET_AXIS)]
                ),
                "everyday_life_annual_population_hours": decimal_text(
                    capability_axis_mass[(capability_id, EVERYDAY_AXIS)]
                ),
                "positive_value_target_count": capability_target_counts[
                    capability_id
                ],
                "allocation_rule": (
                    "Within each action, divide its value among capabilities "
                    "in proportion to their recorded requirement levels."
                ),
            }
        )

    for axis in AXES:
        action_total = sum(
            (mass for (group_id, key), mass in group_axis_mass.items() if key == axis),
            ZERO,
        )
        capability_total = sum(
            (
                mass
                for (capability_id, key), mass in capability_axis_mass.items()
                if key == axis
            ),
            ZERO,
        )
        if abs(action_total - mapped_by_axis[axis]) > TOLERANCE:
            raise RuntimeError(f"action value does not conserve {axis}")
        if abs(capability_total - action_total) > Decimal("1e-12"):
            raise RuntimeError(f"capability value does not conserve {axis}")

    direct_equivalence_rows = canonical_direct_equivalences(
        final_profile_rows,
        files.read_jsonl_gz(OLD_PROFILE_MAP),
        files.read_jsonl_gz(OLD_EDGE_DISPOSITIONS),
        files.read_jsonl_gz(NEW_EDGE_DISPOSITIONS),
        canonical_by_id,
    )

    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "action_capability_requirements.jsonl.gz": action_requirements,
        "source_action_allocations.jsonl.gz": sorted(
            source_allocation_rows,
            key=lambda row: (
                str(row["source_unit_uid"]),
                str(row["action_group_id"]),
            ),
        ),
        "unmapped_source_mass.jsonl.gz": sorted(
            source_residual_rows, key=lambda row: str(row["source_unit_uid"])
        ),
        "action_values.jsonl.gz": action_value_rows,
        "action_target_values.jsonl.gz": action_target_rows,
        "capability_values.jsonl.gz": capability_value_rows,
        "capability_target_values.jsonl.gz": capability_target_rows,
        "policy_units.jsonl.gz": sorted(
            policy_unit_rows, key=lambda row: str(row["policy_unit_id"])
        ),
        "policy_unit_action_weights.jsonl.gz": sorted(
            policy_edge_rows,
            key=lambda row: (
                str(row["policy_unit_id"]),
                str(row["action_group_id"]),
            ),
        ),
        "direct_capability_equivalences.jsonl.gz": (
            direct_equivalence_rows
        ),
    }
    artifacts = [
        files.write_jsonl_gz(output / filename, rows)
        for filename, rows in paths.items()
    ]

    summary = {
        "release_id": RELEASE_ID,
        "status": "completed",
        "action_groups": len(action_requirements),
        "action_group_origins": dict(sorted(origin_counts.items())),
        "canonical_capabilities": len(canonical_rows),
        "action_capability_links": sum(
            len(row["robot_capabilities"])
            + len(row["physics_capabilities"])
            for row in action_requirements
        ),
        "requirement_level_distribution": dict(
            sorted(level_distribution.items())
        ),
        "source_records": len(source_accounting_rows),
        "source_action_allocation_edges": len(source_allocation_rows),
        "action_target_value_edges": len(action_target_rows),
        "capability_target_value_edges": len(capability_target_rows),
        "direct_canonical_equivalence_pairs": len(
            direct_equivalence_rows
        ),
        "policy_views": len(view_summaries),
        "policy_units": len(policy_unit_rows),
        "policy_unit_action_edges": len(policy_edge_rows),
        "view_summaries": view_summaries,
        "value_accounting": {
            axis: {
                "robot_relevant_validated_physical_mass": decimal_text(
                    denominator_by_axis[axis]
                ),
                "mapped_action_mass": decimal_text(mapped_by_axis[axis]),
                "unmapped_mass": decimal_text(
                    denominator_by_axis[axis] - mapped_by_axis[axis]
                ),
                "mapped_fraction": decimal_text(
                    mapped_by_axis[axis] / denominator_by_axis[axis]
                ),
                "action_to_capability_conservation_difference": "0",
            }
            for axis in AXES
        },
        "source_to_action_allocation_rule": (
            "For each source, preserve its prior robot-relevant validated "
            "physical point mass after subtracting old internal-human "
            "biology allocations. Divide that mass equally across the "
            "source's recovered atomic action occurrences and aggregate "
            "equivalent occurrences by final action group."
        ),
        "capability_value_allocation_rule": (
            "Within each action, divide action value among capabilities in "
            "proportion to the frozen requirement levels. This descriptive "
            "allocation does not change the all-requirements action coverage "
            "rule."
        ),
    }
    summary_path = output / "summary.json"
    semantic.write_json_atomic(summary_path, summary)
    release = {
        **summary,
        "inputs": [
            *[files.file_identity(path) for path in required],
            files.file_identity(Path(__file__).resolve()),
        ],
        "outputs": [
            *artifacts,
            files.file_identity(summary_path),
        ],
    }
    semantic.write_json_atomic(output / "release_manifest.json", release)
    return summary


def verify(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    release = read_json(output / "release_manifest.json")
    if release.get("release_id") != RELEASE_ID:
        raise RuntimeError("release ID differs")
    for record in release["inputs"] + release["outputs"]:
        path = REPO_ROOT / str(record["path"])
        identity = files.file_identity(path)
        if "rows" in record:
            identity["rows"] = record["rows"]
        if identity != record:
            raise RuntimeError(f"artifact identity differs: {path}")
    summary = read_json(output / "summary.json")
    requirements = files.read_jsonl_gz(
        output / "action_capability_requirements.jsonl.gz"
    )
    actions = files.read_jsonl_gz(output / "action_values.jsonl.gz")
    capabilities = files.read_jsonl_gz(
        output / "capability_values.jsonl.gz"
    )
    units = files.read_jsonl_gz(output / "policy_units.jsonl.gz")
    if (
        len(requirements) != int(summary["action_groups"])
        or len(actions) != int(summary["action_groups"])
        or len(capabilities) != int(summary["canonical_capabilities"])
        or len(units) != int(summary["policy_units"])
    ):
        raise RuntimeError("verified row counts differ")
    if [int(row["action_group_index"]) for row in requirements] != list(
        range(len(requirements))
    ):
        raise RuntimeError("verified action index is not contiguous")
    if set(row["view_id"] for row in units) != set(
        summary["view_summaries"]
    ):
        raise RuntimeError("verified policy views differ")
    for axis, accounting in summary["value_accounting"].items():
        if accounting["action_to_capability_conservation_difference"] != "0":
            raise RuntimeError(f"value conservation differs: {axis}")
    return {
        "status": "verified",
        "release_id": RELEASE_ID,
        "action_groups": len(requirements),
        "canonical_capabilities": len(capabilities),
        "policy_views": len(summary["view_summaries"]),
        "policy_units": len(units),
        "action_target_value_edges": int(
            summary["action_target_value_edges"]
        ),
        "direct_canonical_equivalence_pairs": int(
            summary["direct_canonical_equivalence_pairs"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    result = build(output) if args.command == "build" else verify(output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
