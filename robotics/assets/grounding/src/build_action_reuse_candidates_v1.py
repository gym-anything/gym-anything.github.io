"""Retrieve existing action groups that may match each corrected action.

Cosine similarity and shared source IDs retrieve candidates. Neither signal
establishes physical equivalence or authorizes capability reuse.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np


GROUNDING_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = GROUNDING_ROOT.parent
DEFAULT_NEW_ROOT = (
    GROUNDING_ROOT / "data" / "derived" / "atomic_action_decomposition_v2_final"
)
DEFAULT_OLD_ROOT = (
    GROUNDING_ROOT / "data" / "derived" / "physical_action_catalog_v1"
)
DEFAULT_PROFILE_ROOT = (
    GROUNDING_ROOT / "data" / "derived" / "action_reuse_embedding_profiles_v1"
)
DEFAULT_EMBEDDING_ROOT = (
    GROUNDING_ROOT / "data" / "derived" / "action_reuse_embeddings_v1"
)
DEFAULT_OUTPUT = (
    GROUNDING_ROOT / "data" / "derived" / "action_reuse_candidates_v1"
)
RELEASE_ID = "action-reuse-candidates-v1"
TOP_GLOBAL = 10
# A shared source normally contributes one group and never more than 28 in
# this corpus. Keep all of them so retrieval cannot discard a source-local
# match before adjudication.
TOP_SHARED_SOURCE = 0
BLOCK_SIZE = 512


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def read_jsonl_gz(path: Path) -> list[dict[str, object]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl_gz(
    path: Path, rows: Iterable[dict[str, object]]
) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with temporary.open("wb") as raw:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, mtime=0
        ) as compressed:
            with io.TextIOWrapper(
                compressed, encoding="utf-8", newline="\n"
            ) as handle:
                for row in rows:
                    handle.write(canonical_json(row) + "\n")
                    count += 1
    os.replace(temporary, path)
    return {**file_identity(path), "rows": count}


def profile_target(profile_id: str) -> tuple[str, str]:
    new_prefix = "action-reuse-profile-v1:new:"
    old_prefix = "action-reuse-profile-v1:old:"
    if profile_id.startswith(new_prefix):
        return "new", profile_id.removeprefix(new_prefix)
    if profile_id.startswith(old_prefix):
        return "old", profile_id.removeprefix(old_prefix)
    raise RuntimeError(f"unexpected action-reuse profile ID: {profile_id}")


def embedding_positions(
    embedding_index: list[dict[str, object]],
) -> tuple[list[int], list[str], list[int], list[str]]:
    new_positions: list[int] = []
    new_ids: list[str] = []
    old_positions: list[int] = []
    old_ids: list[str] = []
    for row in embedding_index:
        position = int(row["embedding_index"])
        kind, target_id = profile_target(str(row["profile_id"]))
        if kind == "new":
            new_positions.append(position)
            new_ids.append(target_id)
        else:
            old_positions.append(position)
            old_ids.append(target_id)
    return new_positions, new_ids, old_positions, old_ids


def normalized_rows(matrix: np.ndarray) -> np.ndarray:
    result = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(result, axis=1, keepdims=True)
    if not bool(np.all(np.isfinite(norms))) or bool(np.any(norms == 0)):
        raise RuntimeError("embedding matrix contains an invalid vector")
    return result / norms


def normalized_action(value: object) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).casefold()))


def retrieve_top_old(
    matrix: np.ndarray,
    new_positions: list[int],
    old_positions: list[int],
    top_k: int,
    block_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    if top_k < 1 or top_k > len(old_positions):
        raise ValueError("invalid old-candidate count")
    old = normalized_rows(matrix[old_positions])
    candidate_indices = np.empty(
        (len(new_positions), top_k), dtype=np.int32
    )
    candidate_scores = np.empty(
        (len(new_positions), top_k), dtype=np.float32
    )
    for start in range(0, len(new_positions), block_size):
        end = min(len(new_positions), start + block_size)
        new = normalized_rows(matrix[new_positions[start:end]])
        similarities = new @ old.T
        partial = np.argpartition(
            similarities, kth=similarities.shape[1] - top_k, axis=1
        )[:, -top_k:]
        partial_scores = np.take_along_axis(
            similarities, partial, axis=1
        )
        order = np.argsort(-partial_scores, axis=1)
        candidate_indices[start:end] = np.take_along_axis(
            partial, order, axis=1
        )
        candidate_scores[start:end] = np.take_along_axis(
            partial_scores, order, axis=1
        )
    return candidate_indices, candidate_scores


def candidate_detail(
    group: dict[str, object],
    members: list[dict[str, object]],
    similarity: float,
    retrieval_reasons: list[str],
) -> dict[str, object]:
    examples = []
    for row in sorted(
        members, key=lambda value: str(value["occurrence_id"])
    )[:2]:
        examples.append(
            {
                "action": row["action"],
                "start_state": row["start_state"],
                "end_state": row["end_state"],
                "object_or_person": row["object_or_person"],
                "tool": row["tool"],
                "physical_behavior": row["physical_behavior"],
            }
        )
    return {
        "old_group_id": group["group_id"],
        "canonical_label": group["canonical_label"],
        "signature": group["signature"],
        "examples": examples,
        "embedding_cosine_similarity": round(float(similarity), 8),
        "retrieval_reasons": sorted(retrieval_reasons),
    }


def derive_candidate_rows(
    new_rows: list[dict[str, object]],
    old_groups: list[dict[str, object]],
    old_occurrences: list[dict[str, object]],
    new_ids: list[str],
    old_ids: list[str],
    top_indices: np.ndarray,
    top_scores: np.ndarray,
    matrix: np.ndarray,
    new_positions: list[int],
    old_positions: list[int],
    top_shared_source: int = TOP_SHARED_SOURCE,
) -> list[dict[str, object]]:
    new_by_id = {
        str(row["atomic_action_occurrence_id"]): row for row in new_rows
    }
    old_by_id = {str(row["group_id"]): row for row in old_groups}
    members: dict[str, list[dict[str, object]]] = defaultdict(list)
    source_groups: dict[str, set[str]] = defaultdict(set)
    exact_action_groups: dict[str, set[str]] = defaultdict(set)
    for row in old_occurrences:
        if row.get("catalog_status") == "grouped" and row.get("group_id"):
            group_id = str(row["group_id"])
            members[group_id].append(row)
            source_groups[str(row["source_unit_uid"])].add(group_id)
            exact_action_groups[normalized_action(row["action"])].add(group_id)
    for group_id, group in old_by_id.items():
        exact_action_groups[
            normalized_action(group["canonical_label"])
        ].add(group_id)
    if set(new_ids) != set(new_by_id):
        raise RuntimeError("new embedding index does not cover corrected actions")
    if set(old_ids) != set(old_by_id):
        raise RuntimeError("old embedding index does not cover old groups")
    old_position_by_id = {
        group_id: old_positions[index]
        for index, group_id in enumerate(old_ids)
    }
    old_local_by_id = {
        group_id: index for index, group_id in enumerate(old_ids)
    }
    normalized_matrix = normalized_rows(matrix)
    rows: list[dict[str, object]] = []
    for new_index, occurrence_id in enumerate(new_ids):
        new = new_by_id[occurrence_id]
        selected: dict[str, dict[str, object]] = {}
        for rank, (local_index, score) in enumerate(
            zip(top_indices[new_index], top_scores[new_index], strict=True),
            start=1,
        ):
            group_id = old_ids[int(local_index)]
            selected[group_id] = {
                "similarity": float(score),
                "reasons": [f"global_embedding_top_{rank}"],
            }
        same_source = sorted(source_groups.get(str(new["source_unit_uid"]), set()))
        if same_source:
            source_scored = []
            new_vector = normalized_matrix[new_positions[new_index]]
            for group_id in same_source:
                old_vector = normalized_matrix[old_position_by_id[group_id]]
                source_scored.append(
                    (float(new_vector @ old_vector), group_id)
                )
            source_scored.sort(key=lambda value: (-value[0], value[1]))
            selected_source = (
                source_scored
                if top_shared_source == 0
                else source_scored[:top_shared_source]
            )
            for rank, (score, group_id) in enumerate(selected_source, start=1):
                if group_id in selected:
                    selected[group_id]["reasons"].append(
                        f"shared_source_top_{rank}"
                    )
                else:
                    selected[group_id] = {
                        "similarity": score,
                        "reasons": [f"shared_source_top_{rank}"],
                    }
        exact_groups = sorted(
            exact_action_groups.get(normalized_action(new["action"]), set())
        )
        new_vector = normalized_matrix[new_positions[new_index]]
        for group_id in exact_groups:
            score = float(
                new_vector @ normalized_matrix[old_position_by_id[group_id]]
            )
            if group_id in selected:
                selected[group_id]["reasons"].append(
                    "exact_normalized_action"
                )
            else:
                selected[group_id] = {
                    "similarity": score,
                    "reasons": ["exact_normalized_action"],
                }
        ordered = sorted(
            selected,
            key=lambda group_id: (
                -float(selected[group_id]["similarity"]),
                group_id,
            ),
        )
        candidates = [
            candidate_detail(
                old_by_id[group_id],
                members[group_id],
                float(selected[group_id]["similarity"]),
                list(selected[group_id]["reasons"]),
            )
            for group_id in ordered
        ]
        rows.append(
            {
                "atomic_action_occurrence_id": occurrence_id,
                "source_unit_uid": new["source_unit_uid"],
                "action": new["action"],
                "start_state": new["start_state"],
                "end_state": new["end_state"],
                "object_or_person": new["object_or_person"],
                "tool_or_effector": new["tool_or_effector"],
                "support": new["support"],
                "candidate_count": len(candidates),
                "shared_source_candidate_count": sum(
                    any(
                        str(reason).startswith("shared_source")
                        for reason in candidate["retrieval_reasons"]
                    )
                    for candidate in candidates
                ),
                "candidates": candidates,
            }
        )
    return rows


def build(
    new_root: Path = DEFAULT_NEW_ROOT,
    old_root: Path = DEFAULT_OLD_ROOT,
    profile_root: Path = DEFAULT_PROFILE_ROOT,
    embedding_root: Path = DEFAULT_EMBEDDING_ROOT,
    output: Path = DEFAULT_OUTPUT,
    top_global: int = TOP_GLOBAL,
    top_shared_source: int = TOP_SHARED_SOURCE,
    block_size: int = BLOCK_SIZE,
) -> dict[str, object]:
    new_path = new_root / "atomic_actions.jsonl.gz"
    old_group_path = old_root / "action_groups.jsonl.gz"
    old_occurrence_path = old_root / "action_occurrences.jsonl.gz"
    index_path = embedding_root / "embedding_index.jsonl.gz"
    matrix_path = embedding_root / "embeddings_float32.npy"
    new_rows = read_jsonl_gz(new_path)
    old_groups = read_jsonl_gz(old_group_path)
    old_occurrences = read_jsonl_gz(old_occurrence_path)
    embedding_index = read_jsonl_gz(index_path)
    matrix = np.load(matrix_path, mmap_mode="r")
    new_positions, new_ids, old_positions, old_ids = embedding_positions(
        embedding_index
    )
    top_indices, top_scores = retrieve_top_old(
        matrix,
        new_positions,
        old_positions,
        top_global,
        block_size,
    )
    rows = derive_candidate_rows(
        new_rows,
        old_groups,
        old_occurrences,
        new_ids,
        old_ids,
        top_indices,
        top_scores,
        matrix,
        new_positions,
        old_positions,
        top_shared_source,
    )
    output.mkdir(parents=True, exist_ok=True)
    candidate_path = output / "candidates.jsonl.gz"
    candidate_artifact = write_jsonl_gz(candidate_path, rows)
    candidate_counts = [int(row["candidate_count"]) for row in rows]
    shared_counts = [int(row["shared_source_candidate_count"]) for row in rows]
    max_similarities = [
        float(row["candidates"][0]["embedding_cosine_similarity"])
        for row in rows
    ]
    summary = {
        "release_id": RELEASE_ID,
        "status": "completed",
        "method": (
            "Retrieve the ten nearest existing action groups by Gemini "
            "embedding cosine similarity, then add every group from the same "
            "source record and every exact normalized action-label match. "
            "Retrieval never authorizes reuse."
        ),
        "new_action_occurrences": len(rows),
        "old_action_groups": len(old_groups),
        "top_global": top_global,
        "top_shared_source": top_shared_source,
        "candidate_links": sum(candidate_counts),
        "candidate_count_minimum": min(candidate_counts),
        "candidate_count_mean": round(
            sum(candidate_counts) / len(candidate_counts), 6
        ),
        "candidate_count_maximum": max(candidate_counts),
        "actions_with_shared_source_candidate": sum(
            count > 0 for count in shared_counts
        ),
        "maximum_similarity_distribution": {
            "minimum": round(min(max_similarities), 8),
            "mean": round(
                sum(max_similarities) / len(max_similarities), 8
            ),
            "maximum": round(max(max_similarities), 8),
        },
        "weights_used": False,
        "merges_performed": False,
        "inputs": [
            file_identity(new_path),
            file_identity(new_root / "release_manifest.json"),
            file_identity(old_group_path),
            file_identity(old_occurrence_path),
            file_identity(old_root / "release_manifest.json"),
            file_identity(profile_root / "release_manifest.json"),
            file_identity(matrix_path),
            file_identity(index_path),
            file_identity(embedding_root / "release_manifest.json"),
            file_identity(Path(__file__).resolve()),
        ],
        "outputs": [candidate_artifact],
    }
    summary_path = output / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    release = {
        **summary,
        "outputs": [candidate_artifact, file_identity(summary_path)],
    }
    release_path = output / "release_manifest.json"
    release_path.write_text(
        json.dumps(release, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return {
        **{
            key: summary[key]
            for key in (
                "status",
                "new_action_occurrences",
                "old_action_groups",
                "candidate_links",
                "candidate_count_mean",
                "actions_with_shared_source_candidate",
                "maximum_similarity_distribution",
            )
        },
        "output": output.relative_to(REPO_ROOT).as_posix(),
        "release_manifest": file_identity(release_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-root", type=Path, default=DEFAULT_NEW_ROOT)
    parser.add_argument("--old-root", type=Path, default=DEFAULT_OLD_ROOT)
    parser.add_argument("--profile-root", type=Path, default=DEFAULT_PROFILE_ROOT)
    parser.add_argument(
        "--embedding-root", type=Path, default=DEFAULT_EMBEDDING_ROOT
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--top-global", type=int, default=TOP_GLOBAL)
    parser.add_argument(
        "--top-shared-source", type=int, default=TOP_SHARED_SOURCE
    )
    parser.add_argument("--block-size", type=int, default=BLOCK_SIZE)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                args.new_root,
                args.old_root,
                args.profile_root,
                args.embedding_root,
                args.output,
                args.top_global,
                args.top_shared_source,
                args.block_size,
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
