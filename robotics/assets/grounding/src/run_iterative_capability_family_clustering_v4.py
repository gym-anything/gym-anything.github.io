"""Run two-pass family clustering with a complete-link embedding guard."""

from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

import run_iterative_capability_family_clustering_v1 as implementation
import run_iterative_capability_family_clustering_v2 as v2
import run_iterative_capability_family_clustering_v3 as v3


REPO_ROOT = Path(__file__).resolve().parents[2]
GROUNDING_ROOT = REPO_ROOT / "grounding"
V3_PROTOCOL = (
    GROUNDING_ROOT
    / "experiments"
    / "iterative_capability_family_clustering_v3"
    / "protocol.json"
)
V4_PROTOCOL = (
    GROUNDING_ROOT
    / "experiments"
    / "iterative_capability_family_clustering_v4"
    / "protocol.json"
)
RECOVERY_PROTOCOL = (
    V4_PROTOCOL.parent / "structural_recovery_protocol.json"
)
COST_SUPPLEMENT = (
    V4_PROTOCOL.parent / "cost_control_supplement.json"
)
V4_OUTPUT = (
    GROUNDING_ROOT
    / "data"
    / "derived"
    / "iterative_capability_family_clustering_v4"
)
EXPERIMENT_ID = "iterative-capability-family-clustering-v4"
PRIOR_EXTERNAL_SPEND_USD = 0.145053
THRESHOLDS = {
    1: 0.90,
    2: 0.88,
    3: 0.86,
    4: 0.84,
}
_ROUND_VECTOR_CACHE: dict[
    tuple[str, int], dict[str, np.ndarray]
] = {}


def proposal_failure_count(
    output: Path, case_id: str
) -> int:
    return sum(
        row["case_id"] == case_id
        and row.get("pass", "pass_a") == "pass_a"
        and row["status"] == "invalid_or_failed_response"
        for row in implementation.all_attempt_records(output)
    )


def recovery_subcases(
    case: dict[str, object],
    pass_name: str,
) -> list[dict[str, object]]:
    members = sorted(
        case["members"], key=lambda row: str(row["alias"])
    )
    result = []
    for offset in range(0, len(members), 25):
        value = deepcopy(case)
        part = offset // 25 + 1
        value["case_id"] = (
            f"{case['case_id']}:recovery:{pass_name}:part-{part:02d}"
        )
        value["members"] = members[offset : offset + 25]
        value["member_count"] = len(value["members"])
        value["leaf_count"] = sum(
            int(row["leaf_count"]) for row in value["members"]
        )
        value["structural_recovery"] = {
            "parent_case_id": str(case["case_id"]),
            "pass": pass_name,
            "part": part,
            "no_cross_part_merges": True,
        }
        result.append(value)
    if (
        not result
        or max(int(row["member_count"]) for row in result) > 25
    ):
        raise RuntimeError("recovery subcase sizing failed")
    return result


def recover_proposals(
    output: Path,
    env_file: Path,
    round_index: int,
) -> dict[str, object]:
    supplement = implementation.read_json(RECOVERY_PROTOCOL)
    if (
        supplement["status"] != "frozen_before_recovery_calls"
        or supplement["parent_protocol_sha256"]
        != implementation.semantic.file_identity(V4_PROTOCOL)[
            "sha256"
        ]
    ):
        raise RuntimeError("structural recovery protocol is invalid")
    cases = implementation.read_jsonl_gz(
        implementation.cases_path(output, round_index)
    )
    selected = [
        case
        for case in cases
        if not implementation.response_path(
            output, round_index, str(case["case_id"])
        ).is_file()
        and proposal_failure_count(
            output, str(case["case_id"])
        )
        >= 5
    ]
    if not selected:
        return {
            "status": "no_cases_require_proposal_recovery",
            "round": round_index,
        }
    subcases = [
        subcase
        for case in selected
        for subcase in recovery_subcases(case, "pass_a")
    ]
    call_result = asyncio.run(
        implementation.call_cases_async(
            output, env_file, subcases
        )
    )
    synthesized = []
    for case in selected:
        parts = recovery_subcases(case, "pass_a")
        missing = [
            str(part["case_id"])
            for part in parts
            if not implementation.response_path(
                output, round_index, str(part["case_id"])
            ).is_file()
        ]
        if missing:
            raise RuntimeError(
                f"recovery subcases remain missing: {missing}"
            )
        groups = []
        uncertain = False
        notes = []
        identities = []
        for part in parts:
            path = implementation.response_path(
                output, round_index, str(part["case_id"])
            )
            record = implementation.read_json(path)
            part_groups = implementation.canonical_groups(
                record["response"], part
            )
            groups.extend(part_groups)
            uncertain = uncertain or bool(
                record["response"]["uncertain"]
            )
            note = implementation.normalize_text(
                record["response"]["uncertainty_note"]
            )
            if note:
                notes.append(note)
            identities.append(
                implementation.semantic.file_identity(path)
            )
        groups.sort(key=lambda row: tuple(row["members"]))
        payload = {
            "case_id": str(case["case_id"]),
            "groups": groups,
            "uncertain": uncertain,
            "uncertainty_note": " | ".join(notes),
        }
        implementation.canonical_groups(payload, case)
        target = implementation.response_path(
            output, round_index, str(case["case_id"])
        )
        implementation.semantic.write_json_atomic(
            target,
            {
                "request": implementation.request_identity(
                    protocol_settings_v4(), case
                ),
                "response": payload,
                "canonical_groups": groups,
                "usage": None,
                "structural_recovery": {
                    "supplement": (
                        "iterative-capability-family-clustering-"
                        "v4-structural-recovery-v1"
                    ),
                    "no_cross_subcase_merges": True,
                    "subcase_ids": [
                        str(part["case_id"]) for part in parts
                    ],
                    "subcase_response_files": identities,
                },
            },
        )
        synthesized.append(str(case["case_id"]))
    result = {
        "status": "proposal_recovery_completed",
        "round": round_index,
        "recovered_parent_cases": synthesized,
        "recovery_subcases": len(subcases),
        "call_result": call_result,
    }
    implementation.semantic.write_json_atomic(
        implementation.round_root(output, round_index)
        / "proposal_structural_recovery.json",
        result,
    )
    return result


def review_failure_count(
    output: Path, case_id: str
) -> int:
    return sum(
        row["case_id"] == case_id
        and row.get("pass")
        == "pass_b_adversarial_refinement"
        and row["status"] == "invalid_or_failed_response"
        for row in implementation.all_attempt_records(output)
    )


def sliced_proposal_groups(
    proposal_groups: list[dict[str, object]],
    allowed_aliases: set[str],
) -> list[dict[str, object]]:
    result = []
    for group in proposal_groups:
        members = sorted(
            set(str(alias) for alias in group["members"])
            & allowed_aliases
        )
        if members:
            result.append(
                {
                    "members": members,
                    "group_name": str(group["group_name"]),
                    "shared_core": str(group["shared_core"]),
                }
            )
    result.sort(key=lambda row: tuple(row["members"]))
    return result


def recover_reviews(
    output: Path,
    env_file: Path,
    round_index: int,
) -> dict[str, object]:
    supplement = implementation.read_json(RECOVERY_PROTOCOL)
    if (
        supplement["status"] != "frozen_before_recovery_calls"
        or supplement["parent_protocol_sha256"]
        != implementation.semantic.file_identity(V4_PROTOCOL)[
            "sha256"
        ]
    ):
        raise RuntimeError("structural recovery protocol is invalid")
    cases = implementation.read_jsonl_gz(
        implementation.cases_path(output, round_index)
    )
    selected = []
    for case in cases:
        _, _, proposal_digest = v3.proposal_record(output, case)
        target = v3.review_response_path(
            output, case, proposal_digest
        )
        if (
            not target.is_file()
            and review_failure_count(
                output, str(case["case_id"])
            )
            >= 5
        ):
            selected.append(case)
    if not selected:
        return {
            "status": "no_cases_require_review_recovery",
            "round": round_index,
        }

    subcases = []
    for case in selected:
        _, proposal_groups, _ = v3.proposal_record(output, case)
        for part in recovery_subcases(case, "pass_b"):
            allowed = {
                str(member["alias"])
                for member in part["members"]
            }
            groups = sliced_proposal_groups(
                proposal_groups, allowed
            )
            payload = {
                "case_id": str(part["case_id"]),
                "groups": groups,
                "uncertain": False,
                "uncertainty_note": "",
            }
            implementation.canonical_groups(payload, part)
            target = implementation.response_path(
                output, round_index, str(part["case_id"])
            )
            implementation.semantic.write_json_atomic(
                target,
                {
                    "request": implementation.request_identity(
                        protocol_settings_v4(), part
                    ),
                    "response": payload,
                    "canonical_groups": groups,
                    "usage": None,
                    "structural_recovery": {
                        "synthetic_slice_of_parent_proposal": True,
                        "parent_case_id": str(case["case_id"]),
                    },
                },
            )
            subcases.append(part)
    call_result = asyncio.run(
        v3.run_reviews_async(output, env_file, subcases)
    )
    synthesized = []
    for case in selected:
        _, proposal_groups, proposal_digest = v3.proposal_record(
            output, case
        )
        parts = recovery_subcases(case, "pass_b")
        groups = []
        uncertain = False
        notes = []
        identities = []
        for part in parts:
            _, _, part_digest = v3.proposal_record(output, part)
            path = v3.review_response_path(
                output, part, part_digest
            )
            if not path.is_file():
                raise RuntimeError(
                    f"review recovery response is missing: {path}"
                )
            record = implementation.read_json(path)
            part_groups = implementation.canonical_groups(
                record["response"], part
            )
            groups.extend(part_groups)
            uncertain = uncertain or bool(
                record["response"]["uncertain"]
            )
            note = implementation.normalize_text(
                record["response"]["uncertainty_note"]
            )
            if note:
                notes.append(note)
            identities.append(
                implementation.semantic.file_identity(path)
            )
        groups.sort(key=lambda row: tuple(row["members"]))
        payload = {
            "case_id": str(case["case_id"]),
            "groups": groups,
            "uncertain": uncertain,
            "uncertainty_note": " | ".join(notes),
        }
        implementation.canonical_groups(payload, case)
        v3.validate_refinement(groups, proposal_groups)
        target = v3.review_response_path(
            output, case, proposal_digest
        )
        implementation.semantic.write_json_atomic(
            target,
            {
                "request": v3.review_request_identity(
                    protocol_settings_v4(),
                    case,
                    proposal_groups,
                ),
                "response": payload,
                "canonical_groups": groups,
                "proposal_groups": proposal_groups,
                "usage": None,
                "structural_recovery": {
                    "supplement": (
                        "iterative-capability-family-clustering-"
                        "v4-structural-recovery-v1"
                    ),
                    "no_cross_subcase_merges": True,
                    "subcase_ids": [
                        str(part["case_id"]) for part in parts
                    ],
                    "subcase_review_response_files": identities,
                },
            },
        )
        synthesized.append(str(case["case_id"]))
    result = {
        "status": "review_recovery_completed",
        "round": round_index,
        "recovered_parent_cases": synthesized,
        "recovery_subcases": len(subcases),
        "call_result": call_result,
    }
    implementation.semantic.write_json_atomic(
        implementation.round_root(output, round_index)
        / "review_structural_recovery.json",
        result,
    )
    return result


def protocol_settings_v4() -> dict[str, object]:
    override = implementation.read_json(V4_PROTOCOL)
    v3_identity = implementation.semantic.file_identity(V3_PROTOCOL)
    if (
        v3_identity["sha256"]
        != override["base_protocol"]["sha256"]
        or override["experiment_id"] != EXPERIMENT_ID
        or override["status"] != "frozen_before_api_calls"
    ):
        raise RuntimeError("v4 protocol inheritance is invalid")
    protocol = deepcopy(v2.protocol_settings_v2())
    v3_override = implementation.read_json(V3_PROTOCOL)
    protocol["experiment_id"] = EXPERIMENT_ID
    protocol["status"] = "frozen_before_api_calls"
    protocol["review_partitioner"] = v3_override[
        "review_partitioner"
    ]
    protocol["v3_override_record"] = v3_override
    protocol["v4_override_record"] = override
    observed = {
        int(key): float(value)
        for key, value in override["geometric_guard"][
            "cosine_threshold_by_round"
        ].items()
    }
    if observed != THRESHOLDS:
        raise RuntimeError("v4 threshold schedule differs")
    cost_supplement = implementation.read_json(COST_SUPPLEMENT)
    if (
        cost_supplement["status"]
        != "frozen_before_round_2_calls"
        or cost_supplement["parent_protocol_sha256"]
        != implementation.semantic.file_identity(V4_PROTOCOL)[
            "sha256"
        ]
        or bool(cost_supplement["semantic_changes"])
    ):
        raise RuntimeError("v4 cost supplement is invalid")
    protocol["cost_control"]["operational_maximum_attempts"] = int(
        cost_supplement["new_operational_attempt_ceiling"]
    )
    protocol["cost_control"]["user_authorized_maximum_usd"] = float(
        cost_supplement[
            "remaining_v4_authorization_after_prior_versions_usd"
        ]
    )
    protocol["cost_control_supplement"] = cost_supplement
    return protocol


def complete_link_subgroups(
    aliases: list[str],
    member_by_alias: dict[str, dict[str, object]],
    vector_by_node: dict[str, np.ndarray],
    threshold: float,
) -> list[list[str]]:
    if len(aliases) <= 1:
        return [sorted(aliases)]
    vectors = np.stack(
        [
            vector_by_node[
                str(member_by_alias[alias]["node_id"])
            ]
            for alias in aliases
        ],
        axis=0,
    )
    distances = np.clip(1.0 - vectors @ vectors.T, 0.0, 2.0)
    np.fill_diagonal(distances, 0.0)
    tree = linkage(
        squareform(distances, checks=False),
        method="complete",
        optimal_ordering=True,
    )
    labels = fcluster(
        tree,
        t=1.0 - threshold,
        criterion="distance",
    )
    groups = [
        sorted(
            alias
            for alias, label in zip(aliases, labels, strict=True)
            if int(label) == cluster
        )
        for cluster in sorted({int(value) for value in labels})
    ]
    groups.sort(key=tuple)
    for group in groups:
        if len(group) < 2:
            continue
        local = np.stack(
            [
                vector_by_node[
                    str(member_by_alias[alias]["node_id"])
                ]
                for alias in group
            ],
            axis=0,
        )
        minimum = float(
            (local @ local.T)[
                np.triu_indices(len(local), k=1)
            ].min()
        )
        if minimum + 1e-6 < threshold:
            raise RuntimeError(
                "complete-link output violates threshold"
            )
    return groups


def guarded_partition(
    output: Path,
    round_index: int,
    case: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    review_groups, review_record = v3.effective_review_partition(
        output, round_index, case
    )
    cache_key = (str(output.resolve()), round_index)
    vector_by_node = _ROUND_VECTOR_CACHE.get(cache_key)
    if vector_by_node is None:
        previous_nodes = implementation.read_jsonl_gz(
            implementation.nodes_path(output, round_index - 1)
        )
        previous_vectors = np.load(
            implementation.embeddings_path(
                output, round_index - 1
            ),
            mmap_mode="r",
        )
        vector_by_node = {
            str(node["node_id"]): previous_vectors[index]
            for index, node in enumerate(previous_nodes)
        }
        _ROUND_VECTOR_CACHE[cache_key] = vector_by_node
    member_by_alias = {
        str(member["alias"]): member
        for member in case["members"]
    }
    threshold = THRESHOLDS[round_index]
    guarded = []
    for reviewed in review_groups:
        for aliases in complete_link_subgroups(
            list(reviewed["members"]),
            member_by_alias,
            vector_by_node,
            threshold,
        ):
            guarded.append(
                {
                    "members": aliases,
                    "group_name": str(reviewed["group_name"]),
                    "shared_core": str(reviewed["shared_core"]),
                }
            )
    guarded.sort(key=lambda row: tuple(row["members"]))
    expected = {
        str(member["alias"]) for member in case["members"]
    }
    observed = [
        alias for group in guarded for alias in group["members"]
    ]
    if (
        set(observed) != expected
        or len(observed) != len(set(observed))
    ):
        raise RuntimeError("guarded partition does not conserve aliases")
    return guarded, review_record


def configure() -> None:
    implementation.EXPERIMENT_ID = EXPERIMENT_ID
    implementation.EXPERIMENT_ROOT = V4_PROTOCOL.parent
    implementation.PROTOCOL = V4_PROTOCOL
    implementation.DEFAULT_OUTPUT = V4_OUTPUT
    implementation.protocol_settings = protocol_settings_v4
    implementation.USE_CUMULATIVE_THEORETICAL_ATTEMPT_COST_BOUND = (
        False
    )
    implementation.EXPERIMENT_DRIVER_SOURCE = Path(__file__).resolve()
    implementation.ADDITIONAL_PROTOCOL_INPUTS = [
        RECOVERY_PROTOCOL,
        COST_SUPPLEMENT,
    ]
    implementation.load_effective_partition = guarded_partition
    implementation.effective_partition_input_paths = (
        v3.effective_review_input_paths
    )
    v3.ACTIVE_PROTOCOL = V4_PROTOCOL
    v3.PRIOR_EXTERNAL_SPEND_USD = PRIOR_EXTERNAL_SPEND_USD
    v3.protocol_settings_v3 = protocol_settings_v4


def guarded_pilot_report(output: Path) -> dict[str, object]:
    selected = set(implementation.pilot_case_ids(output))
    cases = [
        case
        for case in implementation.read_jsonl_gz(
            implementation.cases_path(output, 1)
        )
        if str(case["case_id"]) in selected
    ]
    rows = []
    for case in cases:
        reviewed, _ = v3.effective_review_partition(
            output, 1, case
        )
        guarded, _ = guarded_partition(output, 1, case)
        rows.append(
            {
                "case_id": str(case["case_id"]),
                "domain": str(case["domain"]),
                "members": int(case["member_count"]),
                "pass_b_groups": len(reviewed),
                "guarded_groups": len(guarded),
                "guarded_multi_node_groups": sum(
                    len(group["members"]) > 1
                    for group in guarded
                ),
                "guarded_merged_input_nodes": sum(
                    len(group["members"])
                    for group in guarded
                    if len(group["members"]) > 1
                ),
            }
        )
    report = {
        "status": "pending_manual_semantic_audit",
        "round": 1,
        "threshold": THRESHOLDS[1],
        "cases": rows,
        "cost": implementation.cost_summary(
            output, protocol_settings_v4()
        ),
        "prior_experimental_spend_usd": (
            PRIOR_EXTERNAL_SPEND_USD
        ),
    }
    implementation.semantic.write_json_atomic(
        output / "guarded_pilot_report.json", report
    )
    return report


def main() -> None:
    configure()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "prepare",
            "pilot-propose",
            "pilot-review",
            "pilot-report",
            "run-propose",
            "recover-propose",
            "run-review",
            "recover-review",
            "materialize",
            "verify",
            "cost",
        ),
    )
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument(
        "--output", type=Path, default=V4_OUTPUT
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=implementation.DEFAULT_ENV_FILE,
    )
    arguments = parser.parse_args()
    if arguments.command == "prepare":
        result = implementation.prepare(arguments.output)
    elif arguments.command == "pilot-propose":
        result = implementation.run_pilot(
            arguments.output, arguments.env_file
        )
    elif arguments.command == "pilot-review":
        result = v3.run_reviews(
            arguments.output,
            arguments.env_file,
            1,
            True,
        )
    elif arguments.command == "pilot-report":
        result = guarded_pilot_report(arguments.output)
    elif arguments.command == "run-propose":
        result = implementation.run_round_calls(
            arguments.output,
            arguments.env_file,
            arguments.round,
        )
    elif arguments.command == "recover-propose":
        result = recover_proposals(
            arguments.output,
            arguments.env_file,
            arguments.round,
        )
    elif arguments.command == "run-review":
        result = v3.run_reviews(
            arguments.output,
            arguments.env_file,
            arguments.round,
            False,
        )
    elif arguments.command == "recover-review":
        result = recover_reviews(
            arguments.output,
            arguments.env_file,
            arguments.round,
        )
    elif arguments.command == "materialize":
        result = implementation.materialize_round(
            arguments.output, arguments.round
        )
    elif arguments.command == "verify":
        result = implementation.verify_round(
            arguments.output, arguments.round
        )
    elif arguments.command == "cost":
        result = implementation.cost_summary(
            arguments.output, protocol_settings_v4()
        )
        result["prior_experimental_spend_usd"] = (
            PRIOR_EXTERNAL_SPEND_USD
        )
        result["all_experiment_spend_usd"] = round(
            float(result["known_standard_list_price_usd"])
            + PRIOR_EXTERNAL_SPEND_USD,
            6,
        )
    else:
        raise AssertionError("unreachable command")
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
