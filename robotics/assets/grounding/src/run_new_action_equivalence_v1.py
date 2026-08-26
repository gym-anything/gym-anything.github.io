"""Find a physically equivalent corrected-action neighbor for each unmatched action."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

import run_action_reuse_adjudication_v1 as batch


GROUNDING_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE_ROOT = (
    GROUNDING_ROOT / "data" / "derived" / "unmatched_action_candidates_v1"
)
DEFAULT_OUTPUT = (
    GROUNDING_ROOT / "data" / "derived" / "new_action_equivalence_v1"
)
RELEASE_ID = "new-action-equivalence-v1"
DISPLAY_PREFIX = "gym-anything-new-action-equivalence-v1"
POSITIVE_DECISION = "equivalent_action"
NEGATIVE_DECISION = "distinct_action"
POSITIVE_SUMMARY_KEY = "actions_with_equivalent_candidate"
NEGATIVE_SUMMARY_KEY = "actions_without_equivalent_candidate"
FINAL_METHOD = (
    "Review nearest corrected-action neighbors with Gemini 3.5 "
    "Flash-Lite Batch and link only physically equivalent actions."
)

PROMPT = """For each numbered ANCHOR ACTION, decide whether one supplied CANDIDATE ACTION has exactly the same robot and physics capability requirements.

Two actions are physically equivalent only when replacing object instances, dimensions, poses, and numerical parameters preserves the atomic phase and direction, start and end relations, participant roles, functional tool geometry, contact sequence, controlled quantities, material or constitutive regime, topology behavior, sensing outcome, and physical completion condition.

Reject mere semantic similarity or partial overlap. Setup and execution are different; image capture and interpretation are different; insertion and extraction are different; attaching and transient contact are different; specific and unspecified mechanisms are different.

Return equivalent_action only when one candidate is physically equivalent. In matched_candidate_action_occurrence_id, copy that candidate's candidate_atomic_action_occurrence_id exactly. Return distinct_action with a null match when none qualifies. Choose at most one candidate. Return every action_number once and in order. Give one concrete sentence naming the decisive invariant or difference."""


class NewActionDecision(BaseModel):
    action_number: int
    decision: Literal["equivalent_action", "distinct_action"]
    matched_candidate_action_occurrence_id: str | None
    confidence: Literal["high", "medium", "low"]
    reason: str


class NewActionDecisionBatch(BaseModel):
    results: list[NewActionDecision]


def load_candidates(
    candidate_root: Path, _unused_capability_root: Path
) -> list[dict[str, object]]:
    rows = batch.read_jsonl_gz(candidate_root / "candidates.jsonl.gz")
    ids = [str(row["atomic_action_occurrence_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError("unmatched candidate input duplicates an anchor")
    return rows


def validate_result(
    group: list[dict[str, object]], result: NewActionDecisionBatch
) -> None:
    expected = {
        action_number: {
            str(value["candidate_atomic_action_occurrence_id"])
            for value in row["candidates"]
        }
        for action_number, row in enumerate(group, start=1)
    }
    observed = [value.action_number for value in result.results]
    if (
        len(observed) != len(expected)
        or set(observed) != set(expected)
        or len(observed) != len(set(observed))
    ):
        raise RuntimeError("response does not cover every anchor once")
    for value in result.results:
        matched = value.matched_candidate_action_occurrence_id
        if value.decision == "equivalent_action":
            if matched not in expected[value.action_number]:
                raise RuntimeError(
                    "equivalence result names a non-candidate action"
                )
        elif matched is not None:
            raise RuntimeError("distinct-action result must use a null match")
        if len(value.reason.strip()) < 10:
            raise RuntimeError("equivalence reason is empty")


def finalize(output: Path) -> dict[str, object]:
    manifest = batch.read_json(batch.manifest_path(output))
    shards = manifest["shards"]
    if any(row.get("local_state") != "validated" for row in shards):
        raise RuntimeError("all new-action equivalence shards must validate")
    rows = batch.load_action_index(output)
    groups = batch.action_groups(rows, batch.ACTIONS_PER_REQUEST)
    decisions: dict[str, dict[str, object]] = {}
    usage = Counter()
    for shard in shards:
        validation = shard["validation"]
        path = batch.REPO_ROOT / str(
            validation["validated_file"]["path"]
        )
        if batch.file_identity(path) != validation["validated_file"]:
            raise RuntimeError("validated response identity changed")
        for record in batch.read_jsonl_gz(path):
            group_index = int(record["group_index"])
            for decision in record["result"]["results"]:
                action_number = int(decision["action_number"])
                if not 1 <= action_number <= len(groups[group_index]):
                    raise RuntimeError(
                        "final action number is outside request"
                    )
                occurrence_id = str(
                    groups[group_index][action_number - 1][
                        "atomic_action_occurrence_id"
                    ]
                )
                if occurrence_id in decisions:
                    raise RuntimeError(
                        "duplicate final equivalence decision"
                    )
                decisions[occurrence_id] = {
                    "atomic_action_occurrence_id": occurrence_id,
                    **decision,
                }
            for key, value in (record.get("usage") or {}).items():
                if isinstance(value, int):
                    usage[key] += value
    expected_ids = {
        str(row["atomic_action_occurrence_id"]) for row in rows
    }
    if set(decisions) != expected_ids:
        raise RuntimeError("final equivalence decisions are incomplete")
    decision_rows = [
        decisions[str(row["atomic_action_occurrence_id"])] for row in rows
    ]
    decision_path = output / "decisions.jsonl.gz"
    batch.write_jsonl_gz(decision_path, decision_rows)
    counts = Counter(str(row["decision"]) for row in decision_rows)
    confidence = Counter(str(row["confidence"]) for row in decision_rows)
    input_tokens = int(
        usage.get("prompt_token_count", usage.get("promptTokenCount", 0))
    )
    output_tokens = int(
        usage.get(
            "candidates_token_count",
            usage.get("candidatesTokenCount", 0),
        )
    ) + int(
        usage.get(
            "thoughts_token_count", usage.get("thoughtsTokenCount", 0)
        )
    )
    estimated_cost = (
        input_tokens * batch.INPUT_PRICE_PER_MILLION
        + output_tokens * batch.OUTPUT_PRICE_PER_MILLION
    ) / 1_000_000
    summary = {
        "release_id": RELEASE_ID,
        "status": "completed",
        "actions": len(decision_rows),
        "decision_counts": dict(sorted(counts.items())),
        "confidence_counts": dict(sorted(confidence.items())),
        POSITIVE_SUMMARY_KEY: counts.get(POSITIVE_DECISION, 0),
        NEGATIVE_SUMMARY_KEY: counts.get(NEGATIVE_DECISION, 0),
        "usage": dict(sorted(usage.items())),
        "estimated_batch_list_price_usd": round(estimated_cost, 6),
        "weights_used": False,
        "all_actions_decided_once": True,
    }
    summary_path = output / "summary.json"
    batch.write_json_atomic(summary_path, summary)
    release = {
        **summary,
        "method": FINAL_METHOD,
        "inputs": [
            manifest["candidate_release"],
            manifest["protocol"],
            manifest["action_index"],
            batch.file_identity(Path(__file__).resolve()),
        ],
        "outputs": [
            batch.file_identity(decision_path),
            batch.file_identity(summary_path),
            batch.file_identity(batch.manifest_path(output)),
        ],
    }
    release_path = output / "release_manifest.json"
    batch.write_json_atomic(release_path, release)
    manifest["status"] = "completed"
    manifest["release_manifest"] = batch.file_identity(release_path)
    batch.save_manifest(output, manifest)
    return {
        **summary,
        "output": output.resolve()
        .relative_to(batch.REPO_ROOT.resolve())
        .as_posix(),
        "release_manifest": batch.file_identity(release_path),
    }


def configure() -> None:
    batch.SYSTEM_PROMPT = PROMPT
    batch.PROMPT_SHA256 = hashlib.sha256(
        PROMPT.encode("utf-8")
    ).hexdigest()
    batch.ReuseDecision = NewActionDecision
    batch.ReuseDecisionBatch = NewActionDecisionBatch
    batch.load_candidates = load_candidates
    batch.validate_result = validate_result
    batch.finalize = finalize
    batch.DEFAULT_CANDIDATE_ROOT = DEFAULT_CANDIDATE_ROOT
    # The reused runner records a second release identity during preparation.
    # Point it to the same immutable candidate release; no capabilities are read.
    batch.DEFAULT_CAPABILITY_ROOT = DEFAULT_CANDIDATE_ROOT
    batch.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    batch.RELEASE_ID = RELEASE_ID
    batch.DISPLAY_PREFIX = DISPLAY_PREFIX


if __name__ == "__main__":
    configure()
    batch.main()
