"""Run the frozen k1--k5 action-group selection pipeline in three modes.

The preregistration is
``grounding/experiments/robot_action_group_selection_k1_k5_three_mode_v1/protocol.json``.
All modes share candidates, budgets, policy targets, tie breaks, and solver
settings.  They differ only in which requirement domains define coverage.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix, vstack

import build_action_reuse_candidates_v1 as files
import optimize_stem_research_direct_jump_v1 as exact


getcontext().prec = 100

GROUNDING_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = GROUNDING_ROOT.parent
DERIVED_ROOT = GROUNDING_ROOT / "data" / "derived"
MODEL_ROOT = DERIVED_ROOT / "final_action_value_model_v1"
ELIGIBILITY_ROOT = DERIVED_ROOT / "final_action_eligibility_v1"

ACTION_REQUIREMENTS = MODEL_ROOT / "action_capability_requirements.jsonl.gz"
ACTION_VALUES = MODEL_ROOT / "action_values.jsonl.gz"
POLICY_UNITS = MODEL_ROOT / "policy_units.jsonl.gz"
POLICY_EDGES = MODEL_ROOT / "policy_unit_action_weights.jsonl.gz"
DIRECT_EQUIVALENCES = MODEL_ROOT / "direct_capability_equivalences.jsonl.gz"
MODEL_RELEASE = MODEL_ROOT / "release_manifest.json"
ELIGIBILITY = ELIGIBILITY_ROOT / "final_action_eligibility.jsonl.gz"
ELIGIBILITY_RELEASE = ELIGIBILITY_ROOT / "release_manifest.json"
PROTOCOL = (
    GROUNDING_ROOT
    / "experiments"
    / "robot_action_group_selection_k1_k5_three_mode_v1"
    / "protocol.json"
)
DEFAULT_OUTPUT = (
    DERIVED_ROOT / "robot_action_group_selection_k1_k5_three_mode_v1"
)
RELEASE_ID = "robot-action-group-selection-k1-k5-three-mode-v1"
FIX_TOLERANCE = 1e-9

MODE_DOMAINS = {
    "physics_only": ("physics_capabilities",),
    "physics_plus_robotics": (
        "physics_capabilities",
        "robot_capabilities",
    ),
    "robotics_only": ("robot_capabilities",),
}
MODE_ORDER = tuple(MODE_DOMAINS)
TIER_BUDGETS = {
    "k1_economic_core": 20,
    "k2_1_strategic_domains": 20,
    "k2_2_stem_research": 20,
    "k3_soc_major_diversity": 23,
    "k4_niche_occupations": 9,
    "k5_capability_family_fill": 8,
}
VIEW_IDS = (
    "economic_value",
    "occupation_breadth",
    "soc_major_breadth",
    "strategic_domain_breadth",
    "stem_research_breadth",
    "personal_time",
    "personal_activity_breadth",
    "personal_domain_breadth",
)
Requirement = tuple[str, str, Fraction]

ROBOT_FAMILY_RULES = (
    (
        "bimanual_coordination",
        ("bimanual", "dual arm", "two arm", "multi arm", "bilateral"),
    ),
    (
        "locomotion_navigation",
        (
            "locomot",
            "navigation",
            "gait",
            "walking",
            "mobile base",
            "balance",
            "steering",
        ),
    ),
    (
        "perception_vision",
        (
            "visual",
            "optical",
            "image",
            "camera",
            "vision",
            "perception",
            "object recognition",
            "scene",
        ),
    ),
    (
        "tactile_proprioceptive_sensing",
        (
            "tactile",
            "haptic",
            "proprio",
            "sensor data",
            "sensing",
            "measurement",
            "feedback",
        ),
    ),
    (
        "tool_use_actuation",
        (
            "tool",
            "drill",
            "cut",
            "dispens",
            "actuat",
            "switch",
            "button",
            "trigger",
        ),
    ),
    (
        "manipulation_grasping",
        (
            "grasp",
            "grip",
            "hold",
            "release",
            "retention",
            "pick",
            "payload",
            "placement",
        ),
    ),
    (
        "force_compliance",
        (
            "force",
            "torque",
            "impedance",
            "compliance",
            "pressure",
            "tension",
            "traction",
            "load",
        ),
    ),
    (
        "positioning_motion",
        (
            "position",
            "trajectory",
            "pose",
            "align",
            "orientation",
            "motion",
            "path",
            "insertion",
            "tracking",
            "velocity",
            "rotation",
        ),
    ),
    ("other_robot", ()),
)
PHYSICS_FAMILY_RULES = (
    (
        "biological_tissue",
        (
            "tissue",
            "biological",
            "biomechan",
            "skin",
            "muscle",
            "organ",
            "bone",
            "anatom",
        ),
    ),
    (
        "thermal_phase_change",
        (
            "thermal",
            "heat",
            "temperature",
            "phase",
            "melt",
            "freez",
            "evapor",
            "condens",
            "combust",
        ),
    ),
    (
        "aerodynamics",
        ("aero", "airflow", "wind", "flight", "gas drag"),
    ),
    (
        "fluids",
        (
            "fluid",
            "liquid",
            "flow",
            "visco",
            "capillar",
            "wetting",
            "buoyan",
            "hydrodynamic",
            "suction",
            "hydraulic",
            "gas flow",
        ),
    ),
    (
        "granular_matter",
        ("granular", "grain", "powder", "soil", "sediment", "particul"),
    ),
    (
        "cloth_thin_shell_rope",
        (
            "cloth",
            "textile",
            "fabric",
            "sheet",
            "paper",
            "rope",
            "cable",
            "thread",
            "fiber",
            "thin shell",
        ),
    ),
    (
        "fracture_cutting_wear",
        (
            "fracture",
            "cutting",
            "shear failure",
            "abras",
            "wear",
            "tear",
            "puncture",
            "crack",
            "sever",
        ),
    ),
    (
        "adhesion",
        ("adhesi", "bonding", "cohesi", "glue", "surface tension"),
    ),
    (
        "optics_electromagnetics",
        (
            "optical",
            "light",
            "image formation",
            "reflect",
            "radiation",
            "electromag",
            "electric",
            "magnetic",
            "photoelectric",
            "signal transduction",
        ),
    ),
    (
        "articulated_mechanisms",
        (
            "mechanism",
            "joint",
            "hinge",
            "gear",
            "linkage",
            "lever",
            "torque transmission",
            "kinematic constraint",
            "mechanical advantage",
        ),
    ),
    (
        "compliance_deformation",
        (
            "elastic",
            "deformation",
            "compliant",
            "viscoelastic",
            "flexur",
            "bending",
            "plastic deformation",
            "rigidity",
            "strain",
            "stress",
        ),
    ),
    (
        "rigid_contact_friction",
        (
            "contact",
            "friction",
            "rigid",
            "normal force",
            "collision",
            "impact",
            "rolling",
            "gravity",
            "gravitational",
            "inertia",
            "momentum",
        ),
    ),
    ("other_physics", ()),
)


@dataclass
class Problem:
    protocol: dict[str, object]
    actions: list[dict[str, object]]
    action_ids: list[str]
    action_labels: list[str]
    action_position_by_id: dict[str, int]
    action_values: list[Decimal]
    everyday_values: list[Decimal]
    eligible: set[int]
    units: list[dict[str, object]]
    unit_by_id: dict[str, dict[str, object]]
    unit_ids_by_view: dict[str, list[str]]
    unit_weights: dict[str, dict[int, Decimal]]
    denominators: dict[str, Decimal]
    direct_mass_by_view: dict[str, list[Decimal]]
    occupation_counts: list[int]
    adjacency: dict[tuple[str, str], set[str]]


@dataclass
class ModeIndex:
    mode_id: str
    domains: tuple[str, ...]
    requirements: list[list[int]]
    requirement_records: list[Requirement]
    requirement_names: list[str]
    coverers: list[set[int]]
    supplied_requirements: list[list[int]]
    family_by_requirement: list[str]
    family_order: list[str]
    family_incidence_by_requirement: list[dict[str, Decimal]]
    zero_requirement_actions: set[int]


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    fieldnames = list(rows[0]) if rows else []
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def decimal_text(value: Decimal) -> str:
    result = format(value, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result or "0"


def fraction_record(value: Decimal) -> dict[str, object]:
    return {
        "decimal": decimal_text(value),
        "percent": decimal_text(value * Decimal(100)),
    }


def level_fraction(capability: dict[str, object]) -> Fraction:
    level = capability["requirement_level"]
    return Fraction(int(level["numerator"]), int(level["denominator"]))


def normalize_name(value: object) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).casefold()))


def capability_family(domain: str, name: str) -> str:
    normalized = normalize_name(name)
    rules = (
        ROBOT_FAMILY_RULES
        if domain == "robot_capabilities"
        else PHYSICS_FAMILY_RULES
    )
    for family_id, keywords in rules:
        if not keywords or any(keyword in normalized for keyword in keywords):
            return family_id
    raise AssertionError("family rule must end in a fallback")


def direct_adjacency(
    rows: list[dict[str, object]],
) -> dict[tuple[str, str], set[str]]:
    result: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        if (
            not bool(row["direct_equivalence_only"])
            or bool(row["transitive_closure_allowed"])
        ):
            raise RuntimeError("invalid direct-equivalence record")
        domain = str(row["domain"])
        left = str(row["left_canonical_capability_id"])
        right = str(row["right_canonical_capability_id"])
        result[(domain, left)].add(right)
        result[(domain, right)].add(left)
    return result


def validate_protocol(protocol: dict[str, object]) -> None:
    if protocol.get("experiment_id") != RELEASE_ID:
        raise RuntimeError("protocol experiment ID differs")
    if protocol.get("status") != "frozen_before_optimization":
        raise RuntimeError("protocol is not frozen")
    if int(protocol.get("total_budget", 0)) != 100:
        raise RuntimeError("total budget differs")
    modes = protocol.get("mode_order")
    if not isinstance(modes, list):
        raise RuntimeError("mode order missing")
    observed_modes = tuple(str(row["mode_id"]) for row in modes)
    if observed_modes != MODE_ORDER:
        raise RuntimeError("mode order differs")
    for row in modes:
        mode_id = str(row["mode_id"])
        if tuple(row["required_capability_domains"]) != MODE_DOMAINS[mode_id]:
            raise RuntimeError(f"mode domain definition differs: {mode_id}")
    tiers = protocol.get("tiers")
    if not isinstance(tiers, list):
        raise RuntimeError("tier specifications missing")
    observed_budgets = {
        str(row["tier_id"]): int(row["budget"]) for row in tiers
    }
    if observed_budgets != TIER_BUDGETS:
        raise RuntimeError("tier budgets differ")
    if sum(observed_budgets.values()) != 100:
        raise RuntimeError("tier budgets do not sum to 100")
    solver = protocol.get("solver")
    if not isinstance(solver, dict):
        raise RuntimeError("solver settings missing")
    expected = (0.0, 0.0, "off", 1, 0, FIX_TOLERANCE)
    actual = (
        float(solver["mip_relative_gap"]),
        float(solver["mip_absolute_gap"]),
        str(solver["parallel"]),
        int(solver["threads"]),
        int(solver["random_seed"]),
        float(solver["stage_fix_tolerance"]),
    )
    if actual != expected:
        raise RuntimeError("solver settings differ")


def load_problem() -> Problem:
    protocol = read_json(PROTOCOL)
    validate_protocol(protocol)

    actions = files.read_jsonl_gz(ACTION_REQUIREMENTS)
    values = files.read_jsonl_gz(ACTION_VALUES)
    if len(actions) != 9_363 or len(values) != len(actions):
        raise RuntimeError("final action corpus size differs")
    for position, action in enumerate(actions):
        if int(action["action_group_index"]) != position:
            raise RuntimeError("action indices are not contiguous")
    action_ids = [str(row["action_group_id"]) for row in actions]
    if len(set(action_ids)) != len(action_ids):
        raise RuntimeError("action IDs are not unique")
    action_position_by_id = {
        action_id: position for position, action_id in enumerate(action_ids)
    }
    value_by_id = {str(row["action_group_id"]): row for row in values}
    if set(value_by_id) != set(action_ids):
        raise RuntimeError("action-value IDs differ")
    action_labels = [
        str(value_by_id[action_id]["representative_action"])
        for action_id in action_ids
    ]
    action_values = [
        Decimal(str(value_by_id[action_id]["market_work_economic_value_usd"]))
        for action_id in action_ids
    ]
    everyday_values = [
        Decimal(
            str(
                value_by_id[action_id][
                    "everyday_life_annual_population_hours"
                ]
            )
        )
        for action_id in action_ids
    ]

    eligibility = files.read_jsonl_gz(ELIGIBILITY)
    eligibility_by_id = {
        str(row["action_group_id"]): row for row in eligibility
    }
    if set(eligibility_by_id) != set(action_ids):
        raise RuntimeError("eligibility action set differs")
    eligible = {
        action_position_by_id[action_id]
        for action_id, row in eligibility_by_id.items()
        if bool(row["selection_eligible"])
        and row["selection_status"] == "eligible"
    }
    if len(eligible) != 9_354:
        raise RuntimeError("eligible action count differs")

    units = files.read_jsonl_gz(POLICY_UNITS)
    unit_by_id = {str(row["policy_unit_id"]): row for row in units}
    if len(unit_by_id) != len(units):
        raise RuntimeError("policy unit IDs are not unique")
    observed_views = {str(row["view_id"]) for row in units}
    if observed_views != set(VIEW_IDS):
        raise RuntimeError("policy view set differs")
    unit_ids_by_view: dict[str, list[str]] = {
        view_id: sorted(
            (
                str(row["policy_unit_id"])
                for row in units
                if row["view_id"] == view_id
            )
        )
        for view_id in VIEW_IDS
    }
    denominators = {
        unit_id: Decimal(
            str(unit_by_id[unit_id]["robot_relevant_validated_physical_mass"])
        )
        for unit_id in unit_by_id
    }
    if any(value <= 0 for value in denominators.values()):
        raise RuntimeError("policy unit has nonpositive denominator")

    unit_weights: dict[str, dict[int, Decimal]] = {
        unit_id: {} for unit_id in unit_by_id
    }
    for edge in files.read_jsonl_gz(POLICY_EDGES):
        unit_id = str(edge["policy_unit_id"])
        if unit_id not in unit_by_id:
            raise RuntimeError("policy edge references unknown unit")
        action_id = str(edge["action_group_id"])
        if action_id not in action_position_by_id:
            raise RuntimeError("policy edge references unknown action")
        action_position = action_position_by_id[action_id]
        weight = Decimal(str(edge["allocated_point_mass"]))
        if weight <= 0:
            raise RuntimeError("policy edge has nonpositive mass")
        previous = unit_weights[unit_id].get(action_position, Decimal(0))
        unit_weights[unit_id][action_position] = previous + weight
    exact_mass_views = {
        "economic_value",
        "occupation_breadth",
        "soc_major_breadth",
        "strategic_domain_breadth",
        "stem_research_breadth",
    }
    for unit_id, weights in unit_weights.items():
        edge_mass = sum(weights.values(), Decimal(0))
        denominator = denominators[unit_id]
        view_id = str(unit_by_id[unit_id]["view_id"])
        if edge_mass > denominator + Decimal("1e-6"):
            raise RuntimeError(f"policy edge mass exceeds denominator: {unit_id}")
        if (
            view_id in exact_mass_views
            and abs(edge_mass - denominator) > Decimal("1e-6")
        ):
            raise RuntimeError(f"policy mass does not conserve: {unit_id}")

    direct_mass_by_view: dict[str, list[Decimal]] = {}
    for view_id, unit_ids in unit_ids_by_view.items():
        masses = [Decimal(0) for _ in actions]
        for unit_id in unit_ids:
            for action_position, weight in unit_weights[unit_id].items():
                masses[action_position] += weight
        direct_mass_by_view[view_id] = masses
    for position, value in enumerate(action_values):
        if (
            abs(
                direct_mass_by_view["economic_value"][position] - value
            )
            > Decimal("1e-6")
        ):
            raise RuntimeError("economic policy edges differ from action values")

    occupation_counts = [0 for _ in actions]
    for unit_id in unit_ids_by_view["economic_value"]:
        for action_position in unit_weights[unit_id]:
            occupation_counts[action_position] += 1

    return Problem(
        protocol=protocol,
        actions=actions,
        action_ids=action_ids,
        action_labels=action_labels,
        action_position_by_id=action_position_by_id,
        action_values=action_values,
        everyday_values=everyday_values,
        eligible=eligible,
        units=units,
        unit_by_id=unit_by_id,
        unit_ids_by_view=unit_ids_by_view,
        unit_weights=unit_weights,
        denominators=denominators,
        direct_mass_by_view=direct_mass_by_view,
        occupation_counts=occupation_counts,
        adjacency=direct_adjacency(files.read_jsonl_gz(DIRECT_EQUIVALENCES)),
    )


def build_mode_index(problem: Problem, mode_id: str) -> ModeIndex:
    if mode_id not in MODE_DOMAINS:
        raise RuntimeError(f"unknown mode: {mode_id}")
    domains = MODE_DOMAINS[mode_id]
    requirement_lists: list[list[Requirement]] = []
    name_by_requirement: dict[Requirement, str] = {}
    for action in problem.actions:
        result = []
        for domain in domains:
            capabilities = action[domain]
            if not isinstance(capabilities, list):
                raise RuntimeError(f"invalid capability list: {domain}")
            for capability in capabilities:
                requirement = (
                    domain,
                    str(capability["canonical_capability_id"]),
                    level_fraction(capability),
                )
                result.append(requirement)
                name = str(capability["canonical_name"])
                previous = name_by_requirement.get(requirement)
                if previous is not None and previous != name:
                    raise RuntimeError("canonical requirement name differs")
                name_by_requirement[requirement] = name
        requirement_lists.append(result)

    requirement_records = sorted(
        {value for values in requirement_lists for value in values},
        key=lambda value: (value[0], value[1], value[2]),
    )
    requirement_position = {
        requirement: position
        for position, requirement in enumerate(requirement_records)
    }
    requirements = [
        [requirement_position[value] for value in values]
        for values in requirement_lists
    ]

    occurrences: defaultdict[
        tuple[str, str], list[tuple[int, Fraction]]
    ] = defaultdict(list)
    for action_position in problem.eligible:
        best_levels: dict[tuple[str, str], Fraction] = {}
        for requirement in requirement_lists[action_position]:
            key = requirement[:2]
            previous = best_levels.get(key)
            if previous is None or requirement[2] > previous:
                best_levels[key] = requirement[2]
        for key, level in best_levels.items():
            occurrences[key].append((action_position, level))

    coverers: list[set[int]] = []
    for domain, capability_id, level in requirement_records:
        neighbors = {capability_id}
        neighbors.update(problem.adjacency.get((domain, capability_id), set()))
        supplied_by = {
            action_position
            for neighbor in neighbors
            for action_position, supplied_level in occurrences.get(
                (domain, neighbor), []
            )
            if supplied_level >= level
        }
        coverers.append(supplied_by)
    supplied_requirements = [[] for _ in problem.actions]
    for requirement_position_value, suppliers in enumerate(coverers):
        for supplier in suppliers:
            supplied_requirements[supplier].append(
                requirement_position_value
            )

    family_order = []
    if "physics_capabilities" in domains:
        family_order.extend(row[0] for row in PHYSICS_FAMILY_RULES)
    if "robot_capabilities" in domains:
        family_order.extend(row[0] for row in ROBOT_FAMILY_RULES)
    family_by_requirement = [
        capability_family(requirement[0], name_by_requirement[requirement])
        for requirement in requirement_records
    ]
    family_incidence_by_requirement = [
        defaultdict(Decimal) for _ in requirement_records
    ]
    for action_requirements in requirements:
        if not action_requirements:
            continue
        weight = Decimal(1) / Decimal(len(action_requirements))
        for requirement_position_value in action_requirements:
            family = family_by_requirement[requirement_position_value]
            family_incidence_by_requirement[
                requirement_position_value
            ][family] += weight

    return ModeIndex(
        mode_id=mode_id,
        domains=domains,
        requirements=requirements,
        requirement_records=requirement_records,
        requirement_names=[
            name_by_requirement[value] for value in requirement_records
        ],
        coverers=coverers,
        supplied_requirements=supplied_requirements,
        family_by_requirement=family_by_requirement,
        family_order=family_order,
        family_incidence_by_requirement=[
            dict(value) for value in family_incidence_by_requirement
        ],
        zero_requirement_actions={
            position
            for position, values in enumerate(requirements)
            if not values
        },
    )


def active_requirement_counts(
    selected: set[int], index: ModeIndex
) -> np.ndarray:
    counts = np.zeros(len(index.requirement_records), dtype=np.int16)
    for action_position in selected:
        counts[index.supplied_requirements[action_position]] += 1
    return counts


def coverage_flags(
    active_counts: np.ndarray, index: ModeIndex
) -> np.ndarray:
    return np.asarray(
        [
            all(active_counts[value] > 0 for value in requirements)
            for requirements in index.requirements
        ],
        dtype=np.bool_,
    )


def missing_requirements(
    action_position: int,
    active_counts: np.ndarray,
    index: ModeIndex,
) -> list[int]:
    return [
        requirement
        for requirement in index.requirements[action_position]
        if active_counts[requirement] == 0
    ]


def family_coverage(
    active_counts: np.ndarray, index: ModeIndex
) -> list[dict[str, object]]:
    denominators = {family: Decimal(0) for family in index.family_order}
    covered = {family: Decimal(0) for family in index.family_order}
    for requirement, incidence_by_family in enumerate(
        index.family_incidence_by_requirement
    ):
        for family, weight in incidence_by_family.items():
            denominators[family] += weight
            if active_counts[requirement] > 0:
                covered[family] += weight
    result = []
    for order, family in enumerate(index.family_order):
        denominator = denominators[family]
        mass = covered[family]
        result.append(
            {
                "family_id": family,
                "family_order": order,
                "requirement_incidence_weight": decimal_text(denominator),
                "supplied_incidence_weight": decimal_text(mass),
                "coverage": (
                    fraction_record(mass / denominator)
                    if denominator
                    else None
                ),
            }
        )
    return result


def unit_coverage_record(
    problem: Problem,
    unit_id: str,
    covered: np.ndarray,
) -> dict[str, object]:
    unit = problem.unit_by_id[unit_id]
    covered_mass = sum(
        (
            weight
            for action_position, weight in problem.unit_weights[unit_id].items()
            if covered[action_position]
        ),
        Decimal(0),
    )
    denominator = problem.denominators[unit_id]
    return {
        "policy_unit_id": unit_id,
        "view_id": str(unit["view_id"]),
        "base_unit_id": str(unit["base_unit_id"]),
        "label": str(unit["label"]),
        "target_type": str(unit["target_type"]),
        "denominator_mass": decimal_text(denominator),
        "covered_mass": decimal_text(covered_mass),
        "uncovered_mass": decimal_text(denominator - covered_mass),
        "coverage": fraction_record(covered_mass / denominator),
        "direct_target_action_count": len(problem.unit_weights[unit_id]),
        "covered_target_action_count": sum(
            bool(covered[action_position])
            for action_position in problem.unit_weights[unit_id]
        ),
    }


def view_coverage_summary(
    problem: Problem,
    view_id: str,
    covered: np.ndarray,
) -> dict[str, object]:
    records = [
        unit_coverage_record(problem, unit_id, covered)
        for unit_id in problem.unit_ids_by_view[view_id]
    ]
    fractions = [
        Decimal(str(row["coverage"]["decimal"])) for row in records
    ]
    covered_mass = sum(
        (Decimal(str(row["covered_mass"])) for row in records),
        Decimal(0),
    )
    denominator = sum(
        (Decimal(str(row["denominator_mass"])) for row in records),
        Decimal(0),
    )
    least = min(
        records,
        key=lambda row: (
            Decimal(str(row["coverage"]["decimal"])),
            row["policy_unit_id"],
        ),
    )
    return {
        "view_id": view_id,
        "policy_unit_count": len(records),
        "covered_mass": decimal_text(covered_mass),
        "denominator_mass": decimal_text(denominator),
        "aggregate_coverage": fraction_record(covered_mass / denominator),
        "minimum_unit_coverage": fraction_record(min(fractions)),
        "mean_unit_coverage": fraction_record(
            sum(fractions, Decimal(0)) / Decimal(len(fractions))
        ),
        "least_covered_policy_unit_id": least["policy_unit_id"],
        "least_covered_policy_unit_label": least["label"],
    }


def coverage_snapshot(
    problem: Problem,
    index: ModeIndex,
    selected: set[int],
    snapshot_id: str,
) -> dict[str, object]:
    active = active_requirement_counts(selected, index)
    covered = coverage_flags(active, index)
    paid_targets = np.asarray(
        [value > 0 for value in problem.action_values], dtype=np.bool_
    )
    eligible_mask = np.zeros(len(problem.actions), dtype=np.bool_)
    eligible_mask[list(problem.eligible)] = True
    return {
        "snapshot_id": snapshot_id,
        "selected_action_count": len(selected),
        "covered_action_groups": int(covered.sum()),
        "covered_eligible_action_groups": int((covered & eligible_mask).sum()),
        "covered_paid_work_action_groups": int((covered & paid_targets).sum()),
        "zero_requirement_action_groups": len(index.zero_requirement_actions),
        "views": {
            view_id: view_coverage_summary(problem, view_id, covered)
            for view_id in VIEW_IDS
        },
        "capability_families": family_coverage(active, index),
    }


def target_union(
    problem: Problem, unit_ids: list[str]
) -> tuple[list[int], list[list[Decimal]], list[Decimal]]:
    targets = sorted(
        {
            action_position
            for unit_id in unit_ids
            for action_position in problem.unit_weights[unit_id]
        }
    )
    target_position = {
        action_position: position
        for position, action_position in enumerate(targets)
    }
    unit_target_weights = [
        [Decimal(0) for _ in targets] for _ in unit_ids
    ]
    for unit_position, unit_id in enumerate(unit_ids):
        for action_position, weight in problem.unit_weights[unit_id].items():
            unit_target_weights[unit_position][
                target_position[action_position]
            ] = weight
    aggregate_weights = [
        sum(
            (
                unit_target_weights[unit_position][target_position_value]
                for unit_position in range(len(unit_ids))
            ),
            Decimal(0),
        )
        for target_position_value in range(len(targets))
    ]
    return targets, unit_target_weights, aggregate_weights


def append_floor(
    matrix: csr_matrix,
    lower: np.ndarray,
    upper: np.ndarray,
    coefficients: np.ndarray,
    floor: float,
) -> tuple[csr_matrix, np.ndarray, np.ndarray]:
    nonzero = np.flatnonzero(coefficients)
    row = csr_matrix(
        (
            coefficients[nonzero],
            (
                np.zeros(len(nonzero), dtype=np.int32),
                nonzero,
            ),
        ),
        shape=(1, matrix.shape[1]),
    )
    return (
        vstack([matrix, row], format="csr"),
        np.concatenate([lower, np.asarray([floor], dtype=np.float64)]),
        np.concatenate([upper, np.asarray([np.inf], dtype=np.float64)]),
    )


def exact_batch_selection(
    problem: Problem,
    index: ModeIndex,
    *,
    tier_id: str,
    selected: set[int],
    candidate_actions: set[int],
    unit_ids: list[str],
    budget: int,
    objective: str,
) -> tuple[set[int], dict[str, object]]:
    candidates = sorted(candidate_actions - selected)
    if len(candidates) < budget:
        raise RuntimeError(f"{tier_id} has fewer candidates than its budget")
    candidate_variable = {
        action_position: variable
        for variable, action_position in enumerate(candidates)
    }
    active = active_requirement_counts(selected, index)
    covered_before = coverage_flags(active, index)
    targets, unit_target_weights, aggregate_weights = target_union(
        problem, unit_ids
    )
    precovered_targets = [
        target for target in targets if covered_before[target]
    ]

    reachable: list[tuple[int, list[int]]] = []
    unreachable: list[int] = []
    needed_requirements: set[int] = set()
    for target in targets:
        if covered_before[target]:
            continue
        missing = missing_requirements(target, active, index)
        if not missing:
            raise RuntimeError("uncovered target has no missing requirement")
        if any(
            not (index.coverers[requirement] & candidate_actions - selected)
            for requirement in missing
        ):
            unreachable.append(target)
            continue
        reachable.append((target, missing))
        needed_requirements.update(missing)

    requirements = sorted(needed_requirements)
    requirement_variable = {
        requirement: len(candidates) + position
        for position, requirement in enumerate(requirements)
    }
    y_offset = len(candidates) + len(requirements)
    y_variable = {
        target: y_offset + position
        for position, (target, _) in enumerate(reachable)
    }
    t_index = y_offset + len(reachable)
    variable_count = t_index + 1

    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    lower: list[float] = []
    upper: list[float] = []
    row_index = 0

    for variable in range(len(candidates)):
        rows.append(row_index)
        columns.append(variable)
        values.append(1.0)
    lower.append(float(budget))
    upper.append(float(budget))
    row_index += 1

    for requirement in requirements:
        rows.append(row_index)
        columns.append(requirement_variable[requirement])
        values.append(1.0)
        providers = sorted(
            index.coverers[requirement] & set(candidates)
        )
        if not providers:
            raise RuntimeError("reachable requirement has no batch provider")
        for action_position in providers:
            rows.append(row_index)
            columns.append(candidate_variable[action_position])
            values.append(-1.0)
        lower.append(-np.inf)
        upper.append(0.0)
        row_index += 1

    for target, missing in reachable:
        for requirement in missing:
            rows.extend((row_index, row_index))
            columns.extend(
                (y_variable[target], requirement_variable[requirement])
            )
            values.extend((1.0, -1.0))
            lower.append(-np.inf)
            upper.append(0.0)
            row_index += 1

    # Every eligible action supplies each of its own active-mode
    # requirements at the required level.  Therefore selecting a candidate
    # that is also an uncovered target implies that target is covered.  This
    # redundant implication substantially strengthens the LP relaxation.
    for action_position, x_variable in candidate_variable.items():
        target_y = y_variable.get(action_position)
        if target_y is None:
            if (
                action_position in targets
                and not covered_before[action_position]
            ):
                raise RuntimeError(
                    "eligible candidate cannot cover its own target"
                )
            continue
        rows.extend((row_index, row_index))
        columns.extend((x_variable, target_y))
        values.extend((1.0, -1.0))
        lower.append(-np.inf)
        upper.append(0.0)
        row_index += 1

    target_lookup = {
        action_position: position
        for position, action_position in enumerate(targets)
    }
    precovered_masses = []
    for unit_position, unit_id in enumerate(unit_ids):
        precovered_mass = sum(
            (
                unit_target_weights[unit_position][
                    target_lookup[action_position]
                ]
                for action_position in precovered_targets
            ),
            Decimal(0),
        )
        precovered_masses.append(precovered_mass)
        if objective == "maximin":
            rows.append(row_index)
            columns.append(t_index)
            values.append(1.0)
            denominator = problem.denominators[unit_id]
            for target, _ in reachable:
                weight = unit_target_weights[unit_position][
                    target_lookup[target]
                ]
                if weight:
                    rows.append(row_index)
                    columns.append(y_variable[target])
                    values.append(-float(weight / denominator))
            lower.append(-np.inf)
            upper.append(float(precovered_mass / denominator))
            row_index += 1

    matrix = coo_matrix(
        (
            np.asarray(values, dtype=np.float64),
            (
                np.asarray(rows, dtype=np.int32),
                np.asarray(columns, dtype=np.int32),
            ),
        ),
        shape=(row_index, variable_count),
    ).tocsr()
    base_lower = np.asarray(lower, dtype=np.float64)
    base_upper = np.asarray(upper, dtype=np.float64)

    aggregate_denominator = sum(
        (problem.denominators[unit_id] for unit_id in unit_ids),
        Decimal(0),
    )
    aggregate_coefficients = np.zeros(variable_count, dtype=np.float64)
    for target, _ in reachable:
        aggregate_coefficients[y_variable[target]] = float(
            aggregate_weights[target_lookup[target]] / aggregate_denominator
        )
    stable_cost = np.zeros(variable_count, dtype=np.float64)
    for variable, action_position in enumerate(candidates):
        stable_cost[variable] = float(action_position)

    # Only x is a decision that must be integral.  Conditional on binary x,
    # every positive z or y certifies that all corresponding providers exist.
    # Because the substantive objectives are monotone in y, relaxing the
    # auxiliary coverage variables is an exact formulation of the portfolio
    # problem and removes thousands of unnecessary binary variables.
    integer_variables = len(candidates)

    solver_stages = []
    if objective == "economic":
        primary_cost = -aggregate_coefficients
        values_primary, record = exact.solve_stage(
            stage=f"{index.mode_id}:{tier_id}:primary_economic_mass",
            matrix=matrix,
            lower=base_lower,
            upper=base_upper,
            cost=primary_cost,
            integer_variables=integer_variables,
            warm_values=None,
        )
        solver_stages.append(record)
        primary_value = float(
            np.dot(aggregate_coefficients, values_primary)
        )
        matrix_final, lower_final, upper_final = append_floor(
            matrix,
            base_lower,
            base_upper,
            aggregate_coefficients,
            primary_value - FIX_TOLERANCE,
        )
        values_final, record = exact.solve_stage(
            stage=f"{index.mode_id}:{tier_id}:stable_index",
            matrix=matrix_final,
            lower=lower_final,
            upper=upper_final,
            cost=stable_cost,
            integer_variables=integer_variables,
            warm_values=values_primary,
        )
        solver_stages.append(record)
        substantive_optima = {
            "new_normalized_economic_coverage": primary_value
        }
    elif objective == "maximin":
        primary_cost = np.zeros(variable_count, dtype=np.float64)
        primary_cost[t_index] = -1.0
        values_primary, record = exact.solve_stage(
            stage=f"{index.mode_id}:{tier_id}:primary_maximin",
            matrix=matrix,
            lower=base_lower,
            upper=base_upper,
            cost=primary_cost,
            integer_variables=integer_variables,
            warm_values=None,
        )
        solver_stages.append(record)
        primary_value = float(values_primary[t_index])
        primary_coefficients = np.zeros(variable_count, dtype=np.float64)
        primary_coefficients[t_index] = 1.0
        matrix_secondary, lower_secondary, upper_secondary = append_floor(
            matrix,
            base_lower,
            base_upper,
            primary_coefficients,
            primary_value - FIX_TOLERANCE,
        )
        secondary_cost = -aggregate_coefficients
        values_secondary, record = exact.solve_stage(
            stage=f"{index.mode_id}:{tier_id}:secondary_total_mass",
            matrix=matrix_secondary,
            lower=lower_secondary,
            upper=upper_secondary,
            cost=secondary_cost,
            integer_variables=integer_variables,
            warm_values=values_primary,
        )
        solver_stages.append(record)
        secondary_value = float(
            np.dot(aggregate_coefficients, values_secondary)
        )
        matrix_final, lower_final, upper_final = append_floor(
            matrix_secondary,
            lower_secondary,
            upper_secondary,
            aggregate_coefficients,
            secondary_value - FIX_TOLERANCE,
        )
        values_final, record = exact.solve_stage(
            stage=f"{index.mode_id}:{tier_id}:stable_index",
            matrix=matrix_final,
            lower=lower_final,
            upper=upper_final,
            cost=stable_cost,
            integer_variables=integer_variables,
            warm_values=values_secondary,
        )
        solver_stages.append(record)
        substantive_optima = {
            "minimum_absolute_unit_coverage": primary_value,
            "new_total_normalized_coverage": secondary_value,
        }
    else:
        raise RuntimeError(f"unknown exact objective: {objective}")

    chosen = {
        candidates[variable]
        for variable, value in enumerate(values_final[: len(candidates)])
        if value >= 0.5
    }
    if len(chosen) != budget:
        raise RuntimeError(
            f"{tier_id} solver selected {len(chosen)} actions, expected {budget}"
        )
    evaluated = coverage_snapshot(
        problem, index, selected | chosen, tier_id
    )
    return chosen, {
        "tier_id": tier_id,
        "selection_method": "exact_joint_milp",
        "budget": budget,
        "candidate_action_count": len(candidates),
        "target_action_count": len(targets),
        "precovered_target_action_count": len(precovered_targets),
        "reachable_uncovered_target_action_count": len(reachable),
        "unreachable_uncovered_target_action_count": len(unreachable),
        "unreachable_uncovered_action_group_ids": [
            problem.action_ids[position] for position in unreachable
        ],
        "model": {
            "variables": variable_count,
            "binary_decision_variables": integer_variables,
            "continuous_auxiliary_variables": (
                variable_count - integer_variables
            ),
            "constraints": int(matrix.shape[0]),
            "nonzeros": int(matrix.nnz),
        },
        "substantive_optima": substantive_optima,
        "solver_stages": solver_stages,
        "selected_action_group_ids": [
            problem.action_ids[position] for position in sorted(chosen)
        ],
        "coverage_after_tier": evaluated,
    }


def supplier_intersection(
    missing: list[int],
    index: ModeIndex,
    allowed: set[int],
) -> set[int]:
    if not missing:
        return set()
    ordered = sorted(missing, key=lambda value: len(index.coverers[value]))
    result = index.coverers[ordered[0]] & allowed
    for requirement in ordered[1:]:
        result &= index.coverers[requirement]
        if not result:
            break
    return result


def marginal_action_coverage_gains(
    *,
    weights: dict[int, Decimal],
    candidates: set[int],
    active_counts: np.ndarray,
    covered: np.ndarray,
    index: ModeIndex,
) -> dict[int, Decimal]:
    gains: defaultdict[int, Decimal] = defaultdict(Decimal)
    for target, weight in weights.items():
        if covered[target]:
            continue
        missing = missing_requirements(target, active_counts, index)
        providers = supplier_intersection(missing, index, candidates)
        for provider in providers:
            gains[provider] += weight
    return dict(gains)


def economic_weight_map(problem: Problem) -> dict[int, Decimal]:
    return {
        position: value
        for position, value in enumerate(problem.action_values)
        if value > 0
    }


def sequential_policy_unit_tier(
    problem: Problem,
    index: ModeIndex,
    *,
    tier_id: str,
    selected: set[int],
    view_id: str,
    budget: int,
    niche_only: bool,
) -> tuple[list[int], dict[str, object]]:
    chosen: list[int] = []
    trace = []
    economic_weights = economic_weight_map(problem)
    for step in range(1, budget + 1):
        active = active_requirement_counts(selected, index)
        covered = coverage_flags(active, index)
        unit_candidates: dict[str, set[int]] = {}
        unit_records: dict[str, tuple[Decimal, Decimal]] = {}
        for unit_id in problem.unit_ids_by_view[view_id]:
            candidates = (
                set(problem.unit_weights[unit_id]) & problem.eligible - selected
            )
            if niche_only:
                candidates = {
                    value
                    for value in candidates
                    if problem.occupation_counts[value] == 1
                }
            if not candidates:
                continue
            covered_mass = sum(
                (
                    weight
                    for action_position, weight in problem.unit_weights[
                        unit_id
                    ].items()
                    if covered[action_position]
                ),
                Decimal(0),
            )
            denominator = problem.denominators[unit_id]
            unit_candidates[unit_id] = candidates
            unit_records[unit_id] = (
                covered_mass / denominator,
                denominator - covered_mass,
            )
        if not unit_candidates:
            raise RuntimeError(f"{tier_id} exhausted candidates at step {step}")
        active_unit = min(
            unit_candidates,
            key=lambda unit_id: (
                unit_records[unit_id][0],
                -unit_records[unit_id][1],
                unit_id,
            ),
        )
        candidates = unit_candidates[active_unit]
        unit_gains = marginal_action_coverage_gains(
            weights=problem.unit_weights[active_unit],
            candidates=candidates,
            active_counts=active,
            covered=covered,
            index=index,
        )
        best_unit_gain = max(
            (unit_gains.get(candidate, Decimal(0)) for candidate in candidates),
            default=Decimal(0),
        )
        tied = {
            candidate
            for candidate in candidates
            if unit_gains.get(candidate, Decimal(0)) == best_unit_gain
        }
        global_gains = marginal_action_coverage_gains(
            weights=economic_weights,
            candidates=tied,
            active_counts=active,
            covered=covered,
            index=index,
        )
        selected_action = min(
            tied,
            key=lambda candidate: (
                -global_gains.get(candidate, Decimal(0)),
                -problem.unit_weights[active_unit].get(
                    candidate, Decimal(0)
                ),
                candidate,
            ),
        )
        before_fraction, before_uncovered = unit_records[active_unit]
        selected.add(selected_action)
        chosen.append(selected_action)
        active_after = active_requirement_counts(selected, index)
        covered_after = coverage_flags(active_after, index)
        after_record = unit_coverage_record(
            problem, active_unit, covered_after
        )
        trace.append(
            {
                "step": step,
                "active_policy_unit_id": active_unit,
                "active_policy_unit_label": problem.unit_by_id[active_unit][
                    "label"
                ],
                "active_unit_coverage_before": fraction_record(
                    before_fraction
                ),
                "active_unit_uncovered_mass_before": decimal_text(
                    before_uncovered
                ),
                "selected_action_group_id": problem.action_ids[
                    selected_action
                ],
                "selected_action_group_index": selected_action,
                "representative_action": problem.action_labels[
                    selected_action
                ],
                "marginal_active_unit_mass": decimal_text(best_unit_gain),
                "marginal_global_economic_mass": decimal_text(
                    global_gains.get(selected_action, Decimal(0))
                ),
                "direct_active_unit_mass": decimal_text(
                    problem.unit_weights[active_unit].get(
                        selected_action, Decimal(0)
                    )
                ),
                "active_unit_coverage_after": after_record["coverage"],
            }
        )
    snapshot = coverage_snapshot(problem, index, selected, tier_id)
    return chosen, {
        "tier_id": tier_id,
        "selection_method": (
            "sequential_least_covered_niche_occupation"
            if niche_only
            else "sequential_least_covered_soc_major"
        ),
        "budget": budget,
        "steps": trace,
        "selected_action_group_ids": [
            problem.action_ids[position] for position in chosen
        ],
        "coverage_after_tier": snapshot,
    }


def capability_family_denominators(
    index: ModeIndex,
) -> dict[str, Decimal]:
    denominators = {family: Decimal(0) for family in index.family_order}
    for incidence_by_family in index.family_incidence_by_requirement:
        for family, weight in incidence_by_family.items():
            denominators[family] += weight
    return denominators


def family_candidate_gains(
    index: ModeIndex,
    *,
    active_counts: np.ndarray,
    candidates: set[int],
) -> dict[str, dict[int, Decimal]]:
    result: dict[str, defaultdict[int, Decimal]] = {
        family: defaultdict(Decimal) for family in index.family_order
    }
    for requirement, incidence_by_family in enumerate(
        index.family_incidence_by_requirement
    ):
        if active_counts[requirement] > 0:
            continue
        providers = index.coverers[requirement] & candidates
        for family, weight in incidence_by_family.items():
            for provider in providers:
                result[family][provider] += weight
    return {family: dict(values) for family, values in result.items()}


def sequential_family_tier(
    problem: Problem,
    index: ModeIndex,
    *,
    selected: set[int],
    budget: int,
) -> tuple[list[int], dict[str, object]]:
    tier_id = "k5_capability_family_fill"
    chosen: list[int] = []
    trace = []
    denominators = capability_family_denominators(index)
    family_order_position = {
        family: position for position, family in enumerate(index.family_order)
    }
    economic_weights = economic_weight_map(problem)
    for step in range(1, budget + 1):
        active = active_requirement_counts(selected, index)
        covered = coverage_flags(active, index)
        candidates = problem.eligible - selected
        gains = family_candidate_gains(
            index, active_counts=active, candidates=candidates
        )
        covered_by_family = {family: Decimal(0) for family in index.family_order}
        for requirement, incidence_by_family in enumerate(
            index.family_incidence_by_requirement
        ):
            if active[requirement] == 0:
                continue
            for family, weight in incidence_by_family.items():
                covered_by_family[family] += weight
        active_families = [
            family
            for family in index.family_order
            if denominators[family] > 0
            and any(value > 0 for value in gains[family].values())
        ]
        if not active_families:
            raise RuntimeError(f"{tier_id} exhausted gains at step {step}")
        active_family = min(
            active_families,
            key=lambda family: (
                covered_by_family[family] / denominators[family],
                -(denominators[family] - covered_by_family[family]),
                family_order_position[family],
            ),
        )
        best_gain = max(gains[active_family].values())
        tied = {
            candidate
            for candidate, value in gains[active_family].items()
            if value == best_gain
        }
        global_gains = marginal_action_coverage_gains(
            weights=economic_weights,
            candidates=tied,
            active_counts=active,
            covered=covered,
            index=index,
        )
        selected_action = min(
            tied,
            key=lambda candidate: (
                -global_gains.get(candidate, Decimal(0)),
                candidate,
            ),
        )
        before_mass = covered_by_family[active_family]
        before_fraction = before_mass / denominators[active_family]
        selected.add(selected_action)
        chosen.append(selected_action)
        active_after = active_requirement_counts(selected, index)
        after_rows = {
            row["family_id"]: row
            for row in family_coverage(active_after, index)
        }
        trace.append(
            {
                "step": step,
                "active_family_id": active_family,
                "active_family_coverage_before": fraction_record(
                    before_fraction
                ),
                "active_family_unmet_weight_before": decimal_text(
                    denominators[active_family] - before_mass
                ),
                "selected_action_group_id": problem.action_ids[
                    selected_action
                ],
                "selected_action_group_index": selected_action,
                "representative_action": problem.action_labels[
                    selected_action
                ],
                "newly_supplied_family_incidence_weight": decimal_text(
                    best_gain
                ),
                "marginal_global_economic_mass": decimal_text(
                    global_gains.get(selected_action, Decimal(0))
                ),
                "active_family_coverage_after": after_rows[active_family][
                    "coverage"
                ],
            }
        )
    snapshot = coverage_snapshot(problem, index, selected, tier_id)
    return chosen, {
        "tier_id": tier_id,
        "selection_method": "sequential_least_covered_capability_family",
        "budget": budget,
        "family_order": index.family_order,
        "steps": trace,
        "selected_action_group_ids": [
            problem.action_ids[position] for position in chosen
        ],
        "coverage_after_tier": snapshot,
    }


def leave_one_out_rows(
    problem: Problem,
    index: ModeIndex,
    selected: set[int],
) -> list[dict[str, object]]:
    final_active = active_requirement_counts(selected, index)
    final_covered = coverage_flags(final_active, index)
    result = []
    for removed in sorted(selected):
        active = final_active.copy()
        active[index.supplied_requirements[removed]] -= 1
        if bool(np.any(active < 0)):
            raise RuntimeError("leave-one-out requirement count became negative")
        covered = coverage_flags(active, index)
        lost = final_covered & ~covered
        lost_positions = np.flatnonzero(lost).tolist()
        lost_view_mass = {
            view_id: decimal_text(
                sum(
                    (
                        problem.direct_mass_by_view[view_id][position]
                        for position in lost_positions
                    ),
                    Decimal(0),
                )
            )
            for view_id in VIEW_IDS
        }
        unique_thresholds = sum(
            final_active[requirement] == 1
            for requirement in index.supplied_requirements[removed]
        )
        result.append(
            {
                "action_group_id": problem.action_ids[removed],
                "action_group_index": removed,
                "representative_action": problem.action_labels[removed],
                "lost_covered_action_groups": len(lost_positions),
                "lost_paid_work_action_groups": sum(
                    problem.action_values[position] > 0
                    for position in lost_positions
                ),
                "lost_economic_value_usd": lost_view_mass[
                    "economic_value"
                ],
                "lost_everyday_life_annual_population_hours": decimal_text(
                    sum(
                        (
                            problem.everyday_values[position]
                            for position in lost_positions
                        ),
                        Decimal(0),
                    )
                ),
                "lost_mass_by_view": lost_view_mass,
                "unique_supplied_requirement_thresholds": int(
                    unique_thresholds
                ),
                "removed_action_still_covered": bool(covered[removed]),
            }
        )
    return result


def action_requirement_rows(
    problem: Problem,
    index: ModeIndex,
    action_position: int,
) -> list[dict[str, object]]:
    result = []
    for requirement_position_value in index.requirements[action_position]:
        domain, capability_id, level = index.requirement_records[
            requirement_position_value
        ]
        result.append(
            {
                "domain": domain,
                "canonical_capability_id": capability_id,
                "canonical_name": index.requirement_names[
                    requirement_position_value
                ],
                "requirement_level": {
                    "numerator": level.numerator,
                    "denominator": level.denominator,
                    "decimal": f"{float(level):.9f}",
                },
                "capability_family": index.family_by_requirement[
                    requirement_position_value
                ],
            }
        )
    return result


def selected_action_rows(
    problem: Problem,
    index: ModeIndex,
    tier_choices: dict[str, list[int]],
    tier_results: list[dict[str, object]],
    criticality: list[dict[str, object]],
) -> list[dict[str, object]]:
    criticality_by_action = {
        str(row["action_group_id"]): row for row in criticality
    }
    sequential_provenance: dict[int, dict[str, object]] = {}
    for tier in tier_results:
        for row in tier.get("steps", []):
            action_position = int(row["selected_action_group_index"])
            sequential_provenance[action_position] = {
                key: value
                for key, value in row.items()
                if key
                not in {
                    "selected_action_group_id",
                    "selected_action_group_index",
                    "representative_action",
                }
            }
    result = []
    sequence = 0
    for tier_id in TIER_BUDGETS:
        choices = tier_choices[tier_id]
        joint_batch = tier_id in {
            "k1_economic_core",
            "k2_1_strategic_domains",
            "k2_2_stem_research",
        }
        display_choices = sorted(choices) if joint_batch else choices
        for tier_display_rank, action_position in enumerate(
            display_choices, start=1
        ):
            sequence += 1
            requirements = action_requirement_rows(
                problem, index, action_position
            )
            provenance = sequential_provenance.get(action_position)
            if provenance is None:
                provenance = {
                    "joint_batch": True,
                    "interpretation": (
                        "Unordered joint optimum; display rank is only the "
                        "stable final action-group index order."
                    ),
                }
            result.append(
                {
                    "mode_id": index.mode_id,
                    "portfolio_display_sequence": sequence,
                    "tier_id": tier_id,
                    "tier_display_rank": tier_display_rank,
                    "joint_batch": joint_batch,
                    "action_group_id": problem.action_ids[action_position],
                    "action_group_index": action_position,
                    "representative_action": problem.action_labels[
                        action_position
                    ],
                    "market_work_economic_value_usd": decimal_text(
                        problem.action_values[action_position]
                    ),
                    "everyday_life_annual_population_hours": decimal_text(
                        problem.everyday_values[action_position]
                    ),
                    "economic_value_occupation_count": (
                        problem.occupation_counts[action_position]
                    ),
                    "active_requirement_count": len(requirements),
                    "active_capability_requirements": requirements,
                    "selection_provenance": provenance,
                    "leave_one_out_criticality": criticality_by_action[
                        problem.action_ids[action_position]
                    ],
                }
            )
    if len(result) != 100:
        raise RuntimeError("selected action row count differs")
    return result


def final_target_rows(
    problem: Problem,
    index: ModeIndex,
    selected: set[int],
) -> Iterable[dict[str, object]]:
    active = active_requirement_counts(selected, index)
    covered = coverage_flags(active, index)
    for action_position, action_id in enumerate(problem.action_ids):
        missing = missing_requirements(action_position, active, index)
        yield {
            "mode_id": index.mode_id,
            "action_group_id": action_id,
            "action_group_index": action_position,
            "representative_action": problem.action_labels[action_position],
            "selection_eligible": action_position in problem.eligible,
            "selected": action_position in selected,
            "covered": bool(covered[action_position]),
            "vacuously_covered": (
                action_position in index.zero_requirement_actions
            ),
            "active_requirement_count": len(
                index.requirements[action_position]
            ),
            "missing_requirement_count": len(missing),
            "missing_requirements": [
                {
                    "domain": index.requirement_records[value][0],
                    "canonical_capability_id": index.requirement_records[
                        value
                    ][1],
                    "canonical_name": index.requirement_names[value],
                    "requirement_level": {
                        "numerator": index.requirement_records[value][
                            2
                        ].numerator,
                        "denominator": index.requirement_records[value][
                            2
                        ].denominator,
                    },
                }
                for value in missing
            ],
            "market_work_economic_value_usd": decimal_text(
                problem.action_values[action_position]
            ),
            "everyday_life_annual_population_hours": decimal_text(
                problem.everyday_values[action_position]
            ),
        }


def mode_output_files(output: Path, mode_id: str) -> list[Path]:
    mode_root = output / mode_id
    return [
        mode_root / "selected_actions.jsonl.gz",
        mode_root / "selected_actions.csv",
        mode_root / "tier_results.json",
        mode_root / "coverage_snapshots.json",
        mode_root / "final_target_coverage.jsonl.gz",
        mode_root / "final_policy_unit_coverage.jsonl.gz",
        mode_root / "capability_family_coverage.json",
        mode_root / "leave_one_out_criticality.jsonl.gz",
        mode_root / "result.json",
    ]


def run_mode(
    mode_id: str,
    output: Path = DEFAULT_OUTPUT,
) -> dict[str, object]:
    problem = load_problem()
    index = build_mode_index(problem, mode_id)
    mode_root = output / mode_id
    mode_root.mkdir(parents=True, exist_ok=True)
    selected: set[int] = set()
    tier_choices: dict[str, list[int]] = {}
    tier_results: list[dict[str, object]] = []
    snapshots = [
        coverage_snapshot(problem, index, selected, "before_selection")
    ]

    k1_candidates = {
        position
        for position in problem.eligible
        if problem.action_values[position] > 0
    }
    choices, result = exact_batch_selection(
        problem,
        index,
        tier_id="k1_economic_core",
        selected=selected,
        candidate_actions=k1_candidates,
        unit_ids=problem.unit_ids_by_view["economic_value"],
        budget=TIER_BUDGETS["k1_economic_core"],
        objective="economic",
    )
    selected.update(choices)
    tier_choices["k1_economic_core"] = sorted(choices)
    tier_results.append(result)
    snapshots.append(result["coverage_after_tier"])

    strategic_candidates = {
        position
        for position in problem.eligible
        if problem.direct_mass_by_view["strategic_domain_breadth"][
            position
        ]
        > 0
    }
    choices, result = exact_batch_selection(
        problem,
        index,
        tier_id="k2_1_strategic_domains",
        selected=selected,
        candidate_actions=strategic_candidates,
        unit_ids=problem.unit_ids_by_view["strategic_domain_breadth"],
        budget=TIER_BUDGETS["k2_1_strategic_domains"],
        objective="maximin",
    )
    selected.update(choices)
    tier_choices["k2_1_strategic_domains"] = sorted(choices)
    tier_results.append(result)
    snapshots.append(result["coverage_after_tier"])

    stem_candidates = {
        position
        for position in problem.eligible
        if problem.direct_mass_by_view["stem_research_breadth"][position] > 0
    }
    choices, result = exact_batch_selection(
        problem,
        index,
        tier_id="k2_2_stem_research",
        selected=selected,
        candidate_actions=stem_candidates,
        unit_ids=problem.unit_ids_by_view["stem_research_breadth"],
        budget=TIER_BUDGETS["k2_2_stem_research"],
        objective="maximin",
    )
    selected.update(choices)
    tier_choices["k2_2_stem_research"] = sorted(choices)
    tier_results.append(result)
    snapshots.append(result["coverage_after_tier"])

    choices, result = sequential_policy_unit_tier(
        problem,
        index,
        tier_id="k3_soc_major_diversity",
        selected=selected,
        view_id="soc_major_breadth",
        budget=TIER_BUDGETS["k3_soc_major_diversity"],
        niche_only=False,
    )
    tier_choices["k3_soc_major_diversity"] = choices
    tier_results.append(result)
    snapshots.append(result["coverage_after_tier"])

    choices, result = sequential_policy_unit_tier(
        problem,
        index,
        tier_id="k4_niche_occupations",
        selected=selected,
        view_id="economic_value",
        budget=TIER_BUDGETS["k4_niche_occupations"],
        niche_only=True,
    )
    tier_choices["k4_niche_occupations"] = choices
    tier_results.append(result)
    snapshots.append(result["coverage_after_tier"])

    choices, result = sequential_family_tier(
        problem,
        index,
        selected=selected,
        budget=TIER_BUDGETS["k5_capability_family_fill"],
    )
    tier_choices["k5_capability_family_fill"] = choices
    tier_results.append(result)
    snapshots.append(result["coverage_after_tier"])

    if len(selected) != 100:
        raise RuntimeError(
            f"{mode_id} selected {len(selected)} unique actions, expected 100"
        )
    if not selected <= problem.eligible:
        raise RuntimeError("ineligible action entered portfolio")
    if {
        action
        for values in tier_choices.values()
        for action in values
    } != selected:
        raise RuntimeError("tier choices do not equal selected set")

    criticality = leave_one_out_rows(problem, index, selected)
    selected_rows = selected_action_rows(
        problem, index, tier_choices, tier_results, criticality
    )
    final_active = active_requirement_counts(selected, index)
    final_covered = coverage_flags(final_active, index)
    policy_rows = [
        unit_coverage_record(problem, unit_id, final_covered)
        for view_id in VIEW_IDS
        for unit_id in problem.unit_ids_by_view[view_id]
    ]
    family_rows = family_coverage(final_active, index)
    final_snapshot = snapshots[-1]
    result_record = {
        "release_id": RELEASE_ID,
        "mode_id": mode_id,
        "required_capability_domains": list(index.domains),
        "portfolio_action_count": len(selected),
        "tier_budgets": TIER_BUDGETS,
        "selected_action_group_ids": [
            problem.action_ids[position] for position in sorted(selected)
        ],
        "final_coverage": final_snapshot,
        "exact_solver_stage_count": sum(
            len(row.get("solver_stages", [])) for row in tier_results
        ),
        "all_exact_solver_stages_optimal": all(
            bool(stage["optimal"]) and float(stage["mip_gap"]) == 0.0
            for row in tier_results
            for stage in row.get("solver_stages", [])
        ),
    }

    files.write_jsonl_gz(
        mode_root / "selected_actions.jsonl.gz", selected_rows
    )
    csv_rows = []
    for row in selected_rows:
        provenance = row["selection_provenance"]
        critical = row["leave_one_out_criticality"]
        csv_rows.append(
            {
                "mode_id": row["mode_id"],
                "portfolio_display_sequence": row[
                    "portfolio_display_sequence"
                ],
                "tier_id": row["tier_id"],
                "tier_display_rank": row["tier_display_rank"],
                "joint_batch": row["joint_batch"],
                "sequential_step": provenance.get("step", ""),
                "active_policy_unit_or_family": provenance.get(
                    "active_policy_unit_id",
                    provenance.get("active_family_id", ""),
                ),
                "action_group_id": row["action_group_id"],
                "action_group_index": row["action_group_index"],
                "representative_action": row["representative_action"],
                "market_work_economic_value_usd": row[
                    "market_work_economic_value_usd"
                ],
                "everyday_life_annual_population_hours": row[
                    "everyday_life_annual_population_hours"
                ],
                "economic_value_occupation_count": row[
                    "economic_value_occupation_count"
                ],
                "active_requirement_count": row[
                    "active_requirement_count"
                ],
                "lost_economic_value_if_removed_usd": critical[
                    "lost_economic_value_usd"
                ],
                "lost_covered_actions_if_removed": critical[
                    "lost_covered_action_groups"
                ],
            }
        )
    write_csv(mode_root / "selected_actions.csv", csv_rows)
    write_json(mode_root / "tier_results.json", tier_results)
    write_json(mode_root / "coverage_snapshots.json", snapshots)
    files.write_jsonl_gz(
        mode_root / "final_target_coverage.jsonl.gz",
        final_target_rows(problem, index, selected),
    )
    files.write_jsonl_gz(
        mode_root / "final_policy_unit_coverage.jsonl.gz", policy_rows
    )
    write_json(mode_root / "capability_family_coverage.json", family_rows)
    files.write_jsonl_gz(
        mode_root / "leave_one_out_criticality.jsonl.gz", criticality
    )
    write_json(mode_root / "result.json", result_record)
    manifest = {
        "release_id": RELEASE_ID,
        "mode_id": mode_id,
        "inputs": [
            files.file_identity(path)
            for path in (
                PROTOCOL,
                ACTION_REQUIREMENTS,
                ACTION_VALUES,
                POLICY_UNITS,
                POLICY_EDGES,
                DIRECT_EQUIVALENCES,
                MODEL_RELEASE,
                ELIGIBILITY,
                ELIGIBILITY_RELEASE,
                Path(__file__),
            )
        ],
        "outputs": [
            files.file_identity(path)
            for path in mode_output_files(output, mode_id)
        ],
        "selected_action_groups": 100,
        "all_exact_solver_stages_optimal": result_record[
            "all_exact_solver_stages_optimal"
        ],
    }
    write_json(mode_root / "mode_manifest.json", manifest)
    return result_record


def compact_mode_summary(result: dict[str, object]) -> dict[str, object]:
    final = result["final_coverage"]
    views = final["views"]
    family_rows = [
        row
        for row in final["capability_families"]
        if row["coverage"] is not None
    ]
    family_fractions = [
        Decimal(str(row["coverage"]["decimal"])) for row in family_rows
    ]
    return {
        "mode_id": result["mode_id"],
        "required_capability_domains": result[
            "required_capability_domains"
        ],
        "selected_action_groups": result["portfolio_action_count"],
        "covered_action_groups": final["covered_action_groups"],
        "covered_action_group_fraction": fraction_record(
            Decimal(final["covered_action_groups"]) / Decimal(9_363)
        ),
        "covered_paid_work_action_groups": final[
            "covered_paid_work_action_groups"
        ],
        "economic_coverage": views["economic_value"][
            "aggregate_coverage"
        ],
        "strategic_minimum_unit_coverage": views[
            "strategic_domain_breadth"
        ]["minimum_unit_coverage"],
        "stem_minimum_unit_coverage": views["stem_research_breadth"][
            "minimum_unit_coverage"
        ],
        "soc_minimum_unit_coverage": views["soc_major_breadth"][
            "minimum_unit_coverage"
        ],
        "occupation_minimum_unit_coverage": views["economic_value"][
            "minimum_unit_coverage"
        ],
        "everyday_life_coverage": views["personal_time"][
            "aggregate_coverage"
        ],
        "minimum_capability_family_coverage": fraction_record(
            min(family_fractions)
        ),
        "all_exact_solver_stages_optimal": result[
            "all_exact_solver_stages_optimal"
        ],
    }


def markdown_report(
    summaries: list[dict[str, object]],
    overlap: dict[str, object],
    rows_by_mode: dict[str, list[dict[str, object]]],
) -> str:
    lines = [
        "# k1–k5 three-mode action-group selection",
        "",
        (
            "This is the frozen 100-slot pipeline run under three coverage "
            "definitions. The candidate pool, policy targets, budgets, "
            "sequence, and tie breaks are shared; only the active capability "
            "domains differ."
        ),
        "",
        "## Headline coverage",
        "",
        (
            "| Mode | Economy | Strategic min | STEM min | SOC min | "
            "Covered actions | Family min |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            "| {mode} | {economy}% | {strategic}% | {stem}% | {soc}% | "
            "{actions:,} | {family}% |".format(
                mode=row["mode_id"],
                economy=row["economic_coverage"]["percent"],
                strategic=row["strategic_minimum_unit_coverage"]["percent"],
                stem=row["stem_minimum_unit_coverage"]["percent"],
                soc=row["soc_minimum_unit_coverage"]["percent"],
                actions=row["covered_action_groups"],
                family=row["minimum_capability_family_coverage"]["percent"],
            )
        )
    lines.extend(
        [
            "",
            "## Cross-mode overlap",
            "",
            (
                f"All three portfolios share "
                f"**{overlap['three_way']['count']}** action groups."
            ),
            "",
            "| Pair | Shared actions | Jaccard |",
            "|---|---:|---:|",
        ]
    )
    for row in overlap["pairwise"]:
        lines.append(
            f"| {row['left_mode']} × {row['right_mode']} | "
            f"{row['intersection_count']} | {row['jaccard']:.4f} |"
        )
    for mode_id in MODE_ORDER:
        lines.extend(["", f"## {mode_id}", ""])
        grouped: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows_by_mode[mode_id]:
            grouped[str(row["tier_id"])].append(row)
        for tier_id in TIER_BUDGETS:
            lines.extend(["", f"### {tier_id}", ""])
            for row in grouped[tier_id]:
                suffix = ""
                provenance = row["selection_provenance"]
                if "active_policy_unit_label" in provenance:
                    suffix = (
                        f" — {provenance['active_policy_unit_label']}"
                    )
                elif "active_family_id" in provenance:
                    suffix = f" — {provenance['active_family_id']}"
                lines.append(
                    f"- {row['representative_action']} "
                    f"(`{row['action_group_index']}`){suffix}"
                )
    lines.extend(
        [
            "",
            "## Interpretation guardrails",
            "",
            (
                "- k1, k2.1, and k2.2 are unordered joint MILP batches. "
                "Their displayed order is only stable index order."
            ),
            (
                "- k3, k4, and k5 are sequential; their recorded step and "
                "active SOC, occupation, or family explain each choice."
            ),
            (
                "- Coverage uses only identical or directly confirmed "
                "same-domain capability equivalence at sufficient level; no "
                "transitive closure is used."
            ),
            (
                "- A result says that the portfolio supplies the modeled "
                "requirements, not that an environment or robot implementation "
                "already exists."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def assemble(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    results: dict[str, dict[str, object]] = {}
    rows_by_mode: dict[str, list[dict[str, object]]] = {}
    sets_by_mode: dict[str, set[str]] = {}
    for mode_id in MODE_ORDER:
        mode_root = output / mode_id
        manifest = mode_root / "mode_manifest.json"
        if not manifest.exists():
            raise RuntimeError(f"mode is not complete: {mode_id}")
        results[mode_id] = read_json(mode_root / "result.json")
        rows_by_mode[mode_id] = files.read_jsonl_gz(
            mode_root / "selected_actions.jsonl.gz"
        )
        sets_by_mode[mode_id] = {
            str(row["action_group_id"]) for row in rows_by_mode[mode_id]
        }
        if len(sets_by_mode[mode_id]) != 100:
            raise RuntimeError(f"{mode_id} does not contain 100 unique actions")

    pairwise = []
    for left_position, left in enumerate(MODE_ORDER):
        for right in MODE_ORDER[left_position + 1 :]:
            intersection = sets_by_mode[left] & sets_by_mode[right]
            union = sets_by_mode[left] | sets_by_mode[right]
            pairwise.append(
                {
                    "left_mode": left,
                    "right_mode": right,
                    "intersection_count": len(intersection),
                    "union_count": len(union),
                    "jaccard": len(intersection) / len(union),
                    "shared_action_group_ids": sorted(intersection),
                }
            )
    three_way_ids = set.intersection(
        *(sets_by_mode[mode_id] for mode_id in MODE_ORDER)
    )
    overlap = {
        "pairwise": pairwise,
        "three_way": {
            "count": len(three_way_ids),
            "action_group_ids": sorted(three_way_ids),
        },
    }

    action_row_by_mode = {
        mode_id: {
            str(row["action_group_id"]): row
            for row in rows_by_mode[mode_id]
        }
        for mode_id in MODE_ORDER
    }
    cross_mode_rows = []
    all_selected_ids = sorted(set.union(*sets_by_mode.values()))
    for action_id in all_selected_ids:
        available = [
            action_row_by_mode[mode_id][action_id]
            for mode_id in MODE_ORDER
            if action_id in action_row_by_mode[mode_id]
        ]
        exemplar = available[0]
        row: dict[str, object] = {
            "action_group_id": action_id,
            "action_group_index": exemplar["action_group_index"],
            "representative_action": exemplar["representative_action"],
            "mode_count": len(available),
        }
        for mode_id in MODE_ORDER:
            selected_row = action_row_by_mode[mode_id].get(action_id)
            row[f"{mode_id}_selected"] = selected_row is not None
            row[f"{mode_id}_tier"] = (
                selected_row["tier_id"] if selected_row else ""
            )
        cross_mode_rows.append(row)

    summaries = [
        compact_mode_summary(results[mode_id]) for mode_id in MODE_ORDER
    ]
    comparison = {
        "release_id": RELEASE_ID,
        "protocol_status": "frozen_before_optimization",
        "shared_total_budget": 100,
        "mode_summaries": summaries,
        "overlap": overlap,
        "union_selected_action_group_count": len(all_selected_ids),
        "tier_migration_action_count": sum(
            len(
                {
                    row[f"{mode_id}_tier"]
                    for mode_id in MODE_ORDER
                    if row[f"{mode_id}_selected"]
                }
            )
            > 1
            for row in cross_mode_rows
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "comparison.json", comparison)
    write_csv(output / "mode_summary.csv", summaries)
    write_csv(output / "cross_mode_actions.csv", cross_mode_rows)
    files.write_jsonl_gz(
        output / "cross_mode_actions.jsonl.gz", cross_mode_rows
    )
    write_text(
        output / "REPORT.md",
        markdown_report(summaries, overlap, rows_by_mode),
    )
    output_paths = [
        output / "comparison.json",
        output / "mode_summary.csv",
        output / "cross_mode_actions.csv",
        output / "cross_mode_actions.jsonl.gz",
        output / "REPORT.md",
    ]
    release = {
        "release_id": RELEASE_ID,
        "status": "complete",
        "protocol_frozen_before_optimization": True,
        "mode_count": 3,
        "portfolio_action_groups_per_mode": 100,
        "inputs": [
            files.file_identity(PROTOCOL),
            files.file_identity(Path(__file__)),
            *[
                files.file_identity(output / mode_id / "mode_manifest.json")
                for mode_id in MODE_ORDER
            ],
        ],
        "outputs": [files.file_identity(path) for path in output_paths],
        "all_exact_solver_stages_optimal": all(
            bool(results[mode_id]["all_exact_solver_stages_optimal"])
            for mode_id in MODE_ORDER
        ),
    }
    write_json(output / "release_manifest.json", release)
    return comparison


def validate_identity(identity: dict[str, object]) -> None:
    path = REPO_ROOT / str(identity["path"])
    if not path.exists():
        raise RuntimeError(f"manifest path does not exist: {path}")
    actual = files.file_identity(path)
    if (
        int(actual["bytes"]) != int(identity["bytes"])
        or str(actual["sha256"]) != str(identity["sha256"])
    ):
        raise RuntimeError(f"manifest identity differs: {path}")
    if "rows" in identity:
        rows = files.read_jsonl_gz(path)
        if len(rows) != int(identity["rows"]):
            raise RuntimeError(f"manifest row count differs: {path}")


def verify_mode(
    problem: Problem,
    mode_id: str,
    output: Path,
) -> dict[str, object]:
    mode_root = output / mode_id
    manifest = read_json(mode_root / "mode_manifest.json")
    if manifest.get("release_id") != RELEASE_ID:
        raise RuntimeError("mode manifest release ID differs")
    if manifest.get("mode_id") != mode_id:
        raise RuntimeError("mode manifest mode ID differs")
    for identity in manifest["inputs"]:
        validate_identity(identity)
    for identity in manifest["outputs"]:
        validate_identity(identity)

    selected_rows = files.read_jsonl_gz(
        mode_root / "selected_actions.jsonl.gz"
    )
    if len(selected_rows) != 100:
        raise RuntimeError(f"{mode_id} selected row count differs")
    selected_ids = [str(row["action_group_id"]) for row in selected_rows]
    if len(set(selected_ids)) != 100:
        raise RuntimeError(f"{mode_id} selected IDs are not unique")
    selected = {
        problem.action_position_by_id[action_id] for action_id in selected_ids
    }
    if not selected <= problem.eligible:
        raise RuntimeError(f"{mode_id} contains an ineligible action")
    tier_counts: defaultdict[str, int] = defaultdict(int)
    for row in selected_rows:
        tier_counts[str(row["tier_id"])] += 1
    if dict(tier_counts) != TIER_BUDGETS:
        raise RuntimeError(f"{mode_id} tier counts differ")

    tier_results = json.loads(
        (mode_root / "tier_results.json").read_text(encoding="utf-8")
    )
    if not isinstance(tier_results, list):
        raise RuntimeError(f"{mode_id} tier results are not a list")
    if len(tier_results) != len(TIER_BUDGETS):
        raise RuntimeError(f"{mode_id} tier result count differs")
    stages = [
        stage
        for tier in tier_results
        for stage in tier.get("solver_stages", [])
    ]
    if len(stages) != 8:
        raise RuntimeError(f"{mode_id} exact stage count differs")
    if any(
        not bool(stage["optimal"]) or float(stage["mip_gap"]) != 0.0
        for stage in stages
    ):
        raise RuntimeError(f"{mode_id} has a nonoptimal exact stage")

    index = build_mode_index(problem, mode_id)
    recomputed = coverage_snapshot(
        problem, index, selected, "k5_capability_family_fill"
    )
    recorded = read_json(mode_root / "result.json")["final_coverage"]
    if recomputed != recorded:
        raise RuntimeError(f"{mode_id} final coverage does not reproduce")
    target_rows = files.read_jsonl_gz(
        mode_root / "final_target_coverage.jsonl.gz"
    )
    if len(target_rows) != len(problem.actions):
        raise RuntimeError(f"{mode_id} target coverage row count differs")
    if sum(bool(row["covered"]) for row in target_rows) != int(
        recomputed["covered_action_groups"]
    ):
        raise RuntimeError(f"{mode_id} target coverage count differs")
    return {
        "mode_id": mode_id,
        "selected_action_groups": 100,
        "exact_solver_stages": len(stages),
        "all_exact_solver_stages_optimal": True,
        "final_coverage_reproduced": True,
        "manifest_verified": True,
    }


def verify(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    release = read_json(output / "release_manifest.json")
    if release.get("release_id") != RELEASE_ID:
        raise RuntimeError("release manifest ID differs")
    for identity in release["inputs"]:
        validate_identity(identity)
    for identity in release["outputs"]:
        validate_identity(identity)
    problem = load_problem()
    modes = [
        verify_mode(problem, mode_id, output) for mode_id in MODE_ORDER
    ]
    comparison = read_json(output / "comparison.json")
    if [row["mode_id"] for row in comparison["mode_summaries"]] != list(
        MODE_ORDER
    ):
        raise RuntimeError("comparison mode order differs")
    return {
        "status": "verified",
        "release_id": RELEASE_ID,
        "modes": modes,
        "root_manifest_verified": True,
    }


def preflight() -> dict[str, object]:
    problem = load_problem()
    mode_rows = []
    for mode_id in MODE_ORDER:
        index = build_mode_index(problem, mode_id)
        denominators = capability_family_denominators(index)
        mode_rows.append(
            {
                "mode_id": mode_id,
                "domains": list(index.domains),
                "distinct_requirement_thresholds": len(
                    index.requirement_records
                ),
                "requirement_occurrences": sum(
                    len(values) for values in index.requirements
                ),
                "requirement_supplier_incidence": sum(
                    len(values) for values in index.coverers
                ),
                "zero_requirement_actions": len(
                    index.zero_requirement_actions
                ),
                "capability_families": [
                    {
                        "family_id": family,
                        "incidence_weight": decimal_text(
                            denominators[family]
                        ),
                    }
                    for family in index.family_order
                ],
            }
        )
    return {
        "status": "prepared",
        "release_id": RELEASE_ID,
        "actions": len(problem.actions),
        "eligible_actions": len(problem.eligible),
        "paid_work_target_actions": sum(
            value > 0 for value in problem.action_values
        ),
        "policy_units_by_view": {
            view_id: len(problem.unit_ids_by_view[view_id])
            for view_id in VIEW_IDS
        },
        "tier_budgets": TIER_BUDGETS,
        "modes": mode_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("preflight")
    run_parser = subparsers.add_parser("run-mode")
    run_parser.add_argument("--mode", choices=MODE_ORDER, required=True)
    run_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    assemble_parser = subparsers.add_parser("assemble")
    assemble_parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT
    )
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    if arguments.command == "preflight":
        result = preflight()
    elif arguments.command == "run-mode":
        result = run_mode(arguments.mode, arguments.output)
    elif arguments.command == "assemble":
        result = assemble(arguments.output)
    elif arguments.command == "verify":
        result = verify(arguments.output)
    elif arguments.command == "build":
        for mode_id in MODE_ORDER:
            run_mode(mode_id, arguments.output)
        result = assemble(arguments.output)
    else:
        raise AssertionError("unreachable command")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
