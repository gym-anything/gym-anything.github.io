"""Map the frozen robot-task eligibility policy onto the final action catalog.

Existing action groups inherit their prior frozen decision by stable group ID.
New corrected action groups are evaluated with the same frozen deterministic
label rule.  Sealed positive holdout groups are not evaluated and remain
quarantined from selection.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

import build_action_reuse_candidates_v1 as files
import classify_robot_task_eligibility as legacy


GROUNDING_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = GROUNDING_ROOT.parent
DERIVED_ROOT = GROUNDING_ROOT / "data" / "derived"

FINAL_GROUP_ROOT = DERIVED_ROOT / "deduplicated_action_groups_v3"
FINAL_GROUPS = FINAL_GROUP_ROOT / "action_groups.jsonl.gz"
FINAL_GROUP_RELEASE = FINAL_GROUP_ROOT / "release_manifest.json"

FINAL_MODEL_ROOT = DERIVED_ROOT / "final_action_value_model_v1"
FINAL_REQUIREMENTS = FINAL_MODEL_ROOT / "action_capability_requirements.jsonl.gz"
FINAL_MODEL_RELEASE = FINAL_MODEL_ROOT / "release_manifest.json"

LEGACY_ROOT = DERIVED_ROOT / "robot_task_eligibility_v1"
LEGACY_DECISIONS = LEGACY_ROOT / "eligibility_decisions.jsonl.gz"
LEGACY_RELEASE = LEGACY_ROOT / "release_manifest.json"

POLICY = GROUNDING_ROOT / "manifests" / "robot_task_eligibility_v1.json"
HOLDOUT = GROUNDING_ROOT / "manifests" / "capability_selection_holdout_v1.json"

DEFAULT_OUTPUT = DERIVED_ROOT / "final_action_eligibility_v1"
RELEASE_ID = "final-action-eligibility-v1"

ELIGIBLE = "eligible_external_physical_result"
INELIGIBLE = "ineligible_internal_human_biology"
QUARANTINED = "quarantined_sealed_holdout"


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


def output_paths(output: Path) -> dict[str, Path]:
    return {
        "decisions": output / "final_action_eligibility.jsonl.gz",
        "eligible": output / "eligible_action_groups.jsonl.gz",
        "excluded": output / "excluded_action_groups.jsonl.gz",
        "quarantined": output / "quarantined_action_groups.jsonl.gz",
        "audit": output / "boundary_audit.json",
        "summary": output / "summary.json",
        "manifest": output / "release_manifest.json",
    }


def derive() -> dict[str, object]:
    groups = files.read_jsonl_gz(FINAL_GROUPS)
    requirements = files.read_jsonl_gz(FINAL_REQUIREMENTS)
    old_decisions = files.read_jsonl_gz(LEGACY_DECISIONS)
    policy = read_json(POLICY)
    holdout = read_json(HOLDOUT)

    if len(groups) != 9_363 or len(requirements) != 9_363:
        raise RuntimeError("final action catalog must contain 9,363 groups")
    group_by_id = {
        str(row["action_group_id"]): row
        for row in groups
    }
    if len(group_by_id) != len(groups):
        raise RuntimeError("final action group IDs are not unique")
    old_by_group = {
        str(row["group_id"]): row
        for row in old_decisions
    }
    if len(old_by_group) != len(old_decisions):
        raise RuntimeError("legacy eligibility group IDs are not unique")

    positive_rows = holdout.get("positive_action_groups")
    if not isinstance(positive_rows, list):
        raise RuntimeError("positive holdout rows are missing")
    holdout_ids = {str(row["group_id"]) for row in positive_rows}
    if len(holdout_ids) != 10:
        raise RuntimeError("positive holdout must contain ten action groups")

    decisions: list[dict[str, object]] = []
    for expected_index, requirement in enumerate(requirements):
        if int(requirement["action_group_index"]) != expected_index:
            raise RuntimeError("final action indices are not contiguous")
        group_id = str(requirement["action_group_id"])
        group = group_by_id.get(group_id)
        if group is None:
            raise RuntimeError(f"requirements reference unknown group: {group_id}")
        label = str(requirement["representative_action"])
        if label != str(group["representative_action"]):
            raise RuntimeError(f"representative action differs: {group_id}")
        origin = str(group["group_origin"])

        inherited_group_id: str | None = None
        if origin == "existing_action_group":
            if group_id in old_by_group:
                inherited = old_by_group[group_id]
                result = {
                    "decision": str(inherited["decision"]),
                    "category": str(inherited["category"]),
                    "rule": str(inherited["rule"]),
                    "rationale": str(inherited["rationale"]),
                }
                decision_source = "inherited_frozen_v1_decision"
                inherited_group_id = group_id
            elif group_id in holdout_ids:
                result = {
                    "decision": QUARANTINED,
                    "category": "sealed_positive_holdout",
                    "rule": "holdout_not_evaluated",
                    "rationale": (
                        "The prior positive holdout has no development "
                        "eligibility decision and remains quarantined."
                    ),
                }
                decision_source = "sealed_holdout_quarantine"
            else:
                raise RuntimeError(
                    "existing final group has neither a frozen decision nor "
                    f"a sealed-holdout identity: {group_id}"
                )
        elif origin == "new_corrected_action_group":
            result = legacy.classify_label(label, policy)
            decision_source = "frozen_policy_on_new_corrected_label"
        else:
            raise RuntimeError(f"unexpected final group origin: {origin}")

        decision = str(result["decision"])
        if decision == ELIGIBLE:
            selection_status = "eligible"
        elif decision == INELIGIBLE:
            selection_status = "excluded"
        elif decision == QUARANTINED:
            selection_status = "quarantined"
        else:
            raise RuntimeError(f"unexpected eligibility decision: {decision}")

        decisions.append(
            {
                "action_group_index": expected_index,
                "action_group_id": group_id,
                "representative_action": label,
                "group_origin": origin,
                "primary_old_group_id": group["primary_old_group_id"],
                "decision": decision,
                "selection_status": selection_status,
                "selection_eligible": selection_status == "eligible",
                "category": result["category"],
                "rule": result["rule"],
                "rationale": result["rationale"],
                "decision_source": decision_source,
                "inherited_group_id": inherited_group_id,
                "policy_id": policy["policy_id"],
            }
        )

    if {str(row["action_group_id"]) for row in decisions} != set(group_by_id):
        raise RuntimeError("final eligibility does not cover every final group")

    eligible = [
        row for row in decisions if row["selection_status"] == "eligible"
    ]
    excluded = [
        row for row in decisions if row["selection_status"] == "excluded"
    ]
    quarantined = [
        row for row in decisions if row["selection_status"] == "quarantined"
    ]
    if len(eligible) + len(excluded) + len(quarantined) != len(decisions):
        raise RuntimeError("final eligibility partition does not conserve rows")

    source_counts = Counter(str(row["decision_source"]) for row in decisions)
    origin_counts = Counter(str(row["group_origin"]) for row in decisions)
    exclusion_categories = Counter(
        str(row["category"]) for row in excluded
    )
    summary = {
        "release_id": RELEASE_ID,
        "status": "completed",
        "final_action_groups": len(decisions),
        "eligible_action_groups": len(eligible),
        "excluded_action_groups": len(excluded),
        "quarantined_action_groups": len(quarantined),
        "unresolved_action_groups": 0,
        "group_origins": dict(sorted(origin_counts.items())),
        "decision_sources": dict(sorted(source_counts.items())),
        "excluded_by_category": dict(sorted(exclusion_categories.items())),
        "policy_id": policy["policy_id"],
        "default_for_ambiguity": policy["default_for_ambiguity"],
        "sealed_holdout_evaluated": False,
    }
    expected = {
        "final_action_groups": 9_363,
        "eligible_action_groups": 9_354,
        "excluded_action_groups": 0,
        "quarantined_action_groups": 9,
    }
    for field, value in expected.items():
        if summary[field] != value:
            raise RuntimeError(
                f"final eligibility count changed for {field}: "
                f"{summary[field]} != {value}"
            )

    audit = {
        "purpose": (
            "Show every final-catalog exclusion and quarantine, and make the "
            "inheritance versus new-label policy application explicit."
        ),
        "invariants": {
            "all_final_action_groups_decided_once": True,
            "sealed_holdout_evaluated": False,
            "unresolved_action_groups": 0,
            "eligibility_partition_conserves_rows": True,
        },
        "excluded_rows": excluded,
        "quarantined_rows": quarantined,
        "new_corrected_policy_exclusions": [
            row
            for row in excluded
            if row["group_origin"] == "new_corrected_action_group"
        ],
    }
    return {
        "decisions": decisions,
        "eligible": eligible,
        "excluded": excluded,
        "quarantined": quarantined,
        "summary": summary,
        "audit": audit,
    }


def build_manifest(
    output: Path,
    summary: dict[str, object],
) -> dict[str, object]:
    paths = output_paths(output)
    return {
        "release_id": RELEASE_ID,
        "status": "completed",
        "method": (
            "Inherit frozen eligibility decisions for stable existing group "
            "IDs; apply the same frozen deterministic label policy to new "
            "corrected groups; quarantine sealed holdouts without evaluating "
            "them."
        ),
        "inputs": [
            files.file_identity(path)
            for path in (
                FINAL_GROUPS,
                FINAL_GROUP_RELEASE,
                FINAL_REQUIREMENTS,
                FINAL_MODEL_RELEASE,
                LEGACY_DECISIONS,
                LEGACY_RELEASE,
                POLICY,
                HOLDOUT,
                Path(__file__).resolve(),
            )
        ],
        "outputs": [
            files.file_identity(paths[name])
            for name in (
                "decisions",
                "eligible",
                "excluded",
                "quarantined",
                "audit",
                "summary",
            )
        ],
        "metrics": summary,
    }


def build(output: Path) -> dict[str, object]:
    derived = derive()
    paths = output_paths(output)
    files.write_jsonl_gz(paths["decisions"], derived["decisions"])
    files.write_jsonl_gz(paths["eligible"], derived["eligible"])
    files.write_jsonl_gz(paths["excluded"], derived["excluded"])
    files.write_jsonl_gz(paths["quarantined"], derived["quarantined"])
    write_json(paths["audit"], derived["audit"])
    write_json(paths["summary"], derived["summary"])
    manifest = build_manifest(output, derived["summary"])
    write_json(paths["manifest"], manifest)
    return manifest


def verify(output: Path) -> dict[str, object]:
    paths = output_paths(output)
    for path in paths.values():
        if not path.is_file():
            raise RuntimeError(f"final eligibility output is missing: {path}")
    derived = derive()
    for name in ("decisions", "eligible", "excluded", "quarantined"):
        if files.read_jsonl_gz(paths[name]) != derived[name]:
            raise RuntimeError(f"final eligibility {name} rows differ")
    if read_json(paths["audit"]) != derived["audit"]:
        raise RuntimeError("final eligibility boundary audit differs")
    if read_json(paths["summary"]) != derived["summary"]:
        raise RuntimeError("final eligibility summary differs")
    expected_manifest = build_manifest(output, derived["summary"])
    if read_json(paths["manifest"]) != expected_manifest:
        raise RuntimeError("final eligibility release manifest differs")
    return {
        **derived["summary"],
        "status": "verified",
        "manifest_sha256": files.sha256_file(paths["manifest"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "verify"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = (
        build(args.output)
        if args.command == "build"
        else verify(args.output)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
