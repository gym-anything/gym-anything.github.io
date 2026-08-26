"""Merge the complete base decomposition with its bounded recall review."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

import atomic_action_decomposition_v2_protocol as protocol
import prepare_atomic_action_recall_audit_v1 as recall_selection


GROUNDING_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = GROUNDING_ROOT.parent
BASE = (
    GROUNDING_ROOT
    / "data"
    / "derived"
    / "atomic_action_decomposition_v2_verified"
)
AUDIT = (
    GROUNDING_ROOT
    / "data"
    / "derived"
    / "atomic_action_decomposition_v2_recall_audit"
)
DEFAULT_OUTPUT = (
    GROUNDING_ROOT
    / "data"
    / "derived"
    / "atomic_action_decomposition_v2_final"
)


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def file_identity(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {
        "path": path.resolve().relative_to(REPO_ROOT.resolve()).as_posix(),
        "bytes": size,
        "sha256": digest.hexdigest(),
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def iter_jsonl_gz(path: Path) -> Iterator[dict[str, object]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise RuntimeError(f"invalid row in {path}")
                yield row


def read_summary(root: Path) -> dict[str, object]:
    value = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid summary: {root}")
    return value


def load_decompositions(root: Path) -> list[dict[str, object]]:
    rows = list(iter_jsonl_gz(root / "source_decompositions.jsonl.gz"))
    ids = [str(row["source"]["source_unit_uid"]) for row in rows]
    if any(not uid for uid in ids) or len(ids) != len(set(ids)):
        raise RuntimeError(f"empty or duplicate source IDs: {root}")
    for index, row in enumerate(rows):
        if int(row["source_index"]) != index:
            raise RuntimeError(f"source order is non-contiguous: {root}")
        decomposition = protocol.SourceDecomposition.model_validate(
            row["decomposition"]
        )
        protocol.validate_result(
            [row["source"]],
            protocol.DecompositionBatch(results=[decomposition]),
        )
    return rows


def build(
    base: Path,
    audit: Path,
    output: Path,
) -> dict[str, object]:
    base_rows = load_decompositions(base)
    audit_rows = load_decompositions(audit)
    audit_by_id = {
        str(row["source"]["source_unit_uid"]): row for row in audit_rows
    }
    expected_audit_ids = set(
        recall_selection.disagreement_source_ids(
            recall_selection.OLD_CLEANUP,
            base / "source_decompositions.jsonl.gz",
        )
    )
    if set(audit_by_id) != expected_audit_ids:
        raise RuntimeError("recall audit does not cover the exact disagreement set")
    base_by_id = {
        str(row["source"]["source_unit_uid"]): row for row in base_rows
    }
    if any(
        base_by_id[uid]["decomposition"]["status"]
        != "no_robot_physical_action"
        for uid in audit_by_id
    ):
        raise RuntimeError("recall audit attempts to replace a base action result")

    output.mkdir(parents=True, exist_ok=True)
    source_path = output / "source_decompositions.jsonl.gz"
    action_path = output / "atomic_actions.jsonl.gz"
    source_temp = source_path.with_suffix(source_path.suffix + ".tmp")
    action_temp = action_path.with_suffix(action_path.suffix + ".tmp")
    status_counts: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    action_count = 0
    replaced = 0
    with gzip.open(
        source_temp, "wt", encoding="utf-8", newline="\n"
    ) as source_handle, gzip.open(
        action_temp, "wt", encoding="utf-8", newline="\n"
    ) as action_handle:
        for source_index, base_row in enumerate(base_rows):
            source = base_row["source"]
            uid = str(source["source_unit_uid"])
            chosen = audit_by_id.get(uid, base_row)
            if uid in audit_by_id:
                if chosen["source"] != source:
                    raise RuntimeError(f"audit source fields changed: {uid}")
                replaced += 1
            decomposition = protocol.SourceDecomposition.model_validate(
                chosen["decomposition"]
            )
            output_row = {
                "source_index": source_index,
                "source": source,
                "decomposition": decomposition.model_dump(mode="json"),
                "result_origin": (
                    "recall_audit" if uid in audit_by_id else "base_decomposition"
                ),
            }
            source_handle.write(canonical_json(output_row) + "\n")
            status_counts[decomposition.status] += 1
            kind_counts[str(source["source_kind"])] += 1
            for action in decomposition.actions:
                action_handle.write(
                    canonical_json(
                        {
                            "atomic_action_occurrence_id": (
                                f"atomic-action-v2-final:{source_index:05d}:"
                                f"{action.order:03d}"
                            ),
                            "source_index": source_index,
                            "source_unit_uid": uid,
                            "source_kind": source["source_kind"],
                            "source_text": source["source_text"],
                            "context_label": source.get("context_label", ""),
                            "weight_axis": source.get("weight_axis", ""),
                            "weight_value": source.get("weight_value", ""),
                            "result_origin": (
                                "recall_audit"
                                if uid in audit_by_id
                                else "base_decomposition"
                            ),
                            **action.model_dump(mode="json"),
                        }
                    )
                    + "\n"
                )
                action_count += 1
    os.replace(source_temp, source_path)
    os.replace(action_temp, action_path)

    base_summary = read_summary(base)
    audit_summary = read_summary(audit)
    summary = {
        "release_id": "atomic_action_decomposition_v2_final",
        "source_rows": len(base_rows),
        "source_kind_counts": dict(sorted(kind_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "atomic_action_rows": action_count,
        "all_sources_retained": True,
        "missing_source_rows": 0,
        "duplicate_source_rows": 0,
        "base_sources_replaced_by_bounded_recall_audit": replaced,
        "recall_audit_status_counts": audit_summary["status_counts"],
        "old_physical_new_empty_disagreements_before_audit": len(audit_rows),
        "old_physical_new_empty_disagreements_after_audit": int(
            audit_summary["status_counts"].get(
                "no_robot_physical_action",
                0,
            )
        ),
        "batch_api_cost_usd": round(
            float(base_summary["batch_api_cost_usd"])
            + float(audit_summary["batch_api_cost_usd"]),
            6,
        ),
        "base_prompt_sha256": base_summary["prompt_sha256"],
        "recall_audit_prompt_sha256": audit_summary["prompt_sha256"],
    }
    summary_path = output / "summary.json"
    write_json(summary_path, summary)
    release = {
        "release_id": "atomic_action_decomposition_v2_final",
        "created_at": now_utc(),
        "complete": True,
        "source_count": len(base_rows),
        "action_count": action_count,
        "base_release": file_identity(base / "release_manifest.json"),
        "recall_audit_release": file_identity(audit / "release_manifest.json"),
        "source_decompositions": file_identity(source_path),
        "atomic_actions": file_identity(action_path),
        "summary": file_identity(summary_path),
    }
    write_json(output / "release_manifest.json", release)
    result = verify(output)
    return {**summary, "verification": result}


def verify(output: Path) -> dict[str, object]:
    release = json.loads(
        (output / "release_manifest.json").read_text(encoding="utf-8")
    )
    if release.get("complete") is not True:
        raise RuntimeError("final release is not complete")
    for field in (
        "base_release",
        "recall_audit_release",
        "source_decompositions",
        "atomic_actions",
        "summary",
    ):
        identity = release.get(field)
        if not isinstance(identity, dict):
            raise RuntimeError(f"missing release identity: {field}")
        path = REPO_ROOT / str(identity["path"])
        if not path.exists() or file_identity(path) != identity:
            raise RuntimeError(f"release identity failed: {field}")

    rows = load_decompositions(output)
    action_counts: Counter[int] = Counter()
    action_ids: set[str] = set()
    action_rows = 0
    for row in rows:
        action_counts[int(row["source_index"])] = len(
            row["decomposition"]["actions"]
        )
    for row in iter_jsonl_gz(output / "atomic_actions.jsonl.gz"):
        action_id = str(row["atomic_action_occurrence_id"])
        if action_id in action_ids:
            raise RuntimeError("duplicate final action ID")
        action_ids.add(action_id)
        source_index = int(row["source_index"])
        if (
            source_index < 0
            or source_index >= len(rows)
            or row["source_unit_uid"]
            != rows[source_index]["source"]["source_unit_uid"]
        ):
            raise RuntimeError("final action references the wrong source")
        action_counts[source_index] -= 1
        action_rows += 1
    if any(count != 0 for count in action_counts.values()):
        raise RuntimeError("source and flat action counts differ")
    if len(rows) != int(release["source_count"]):
        raise RuntimeError("final source count differs")
    if action_rows != int(release["action_count"]):
        raise RuntimeError("final action count differs")
    return {
        "status": "verified",
        "source_rows": len(rows),
        "unique_source_rows": len(
            {row["source"]["source_unit_uid"] for row in rows}
        ),
        "missing_source_rows": 0,
        "duplicate_source_rows": 0,
        "atomic_action_rows": action_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--base", type=Path, default=BASE)
    build_parser.add_argument("--audit", type=Path, default=AUDIT)
    build_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = (
        build(args.base, args.audit, args.output)
        if args.command == "build"
        else verify(args.output)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
