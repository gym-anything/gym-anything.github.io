"""Build final corrected-action groups from independently confirmed matches."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import build_action_reuse_candidates_v1 as reuse


GROUNDING_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REUSE_ROOT = (
    GROUNDING_ROOT / "data" / "derived" / "action_reuse_final_v1"
)
DEFAULT_EQUIVALENCE_ROOT = (
    GROUNDING_ROOT / "data" / "derived" / "new_action_equivalence_v1"
)
DEFAULT_CONFIRMATION_ROOT = (
    GROUNDING_ROOT
    / "data"
    / "derived"
    / "new_action_equivalence_confirmation_v1"
)
DEFAULT_OUTPUT = (
    GROUNDING_ROOT / "data" / "derived" / "deduplicated_action_groups_v1"
)
RELEASE_ID = "deduplicated-action-groups-v1"


class DisjointSet:
    def __init__(self, values: list[str]) -> None:
        self.parent = {value: value for value in values}
        self.size = {value: 1 for value in values}

    def find(self, value: str) -> str:
        root = value
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[value] != value:
            parent = self.parent[value]
            self.parent[value] = root
            value = parent
        return root

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.size[left_root] < self.size[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        self.size[left_root] += self.size[right_root]


def unique_by_id(
    rows: list[dict[str, object]], label: str
) -> dict[str, dict[str, object]]:
    result = {
        str(row["atomic_action_occurrence_id"]): row for row in rows
    }
    if len(result) != len(rows):
        raise RuntimeError(f"{label} duplicates an action occurrence")
    return result


def new_group_id(occurrence_ids: list[str]) -> str:
    digest = hashlib.sha256(
        "\n".join(sorted(occurrence_ids)).encode("utf-8")
    ).hexdigest()[:32]
    return f"corrected-action-group-v1:{digest}"


def build(
    reuse_root: Path,
    equivalence_root: Path,
    confirmation_root: Path,
    output: Path,
    release_id: str = RELEASE_ID,
) -> dict[str, object]:
    reuse_root = reuse_root.resolve()
    equivalence_root = equivalence_root.resolve()
    confirmation_root = confirmation_root.resolve()
    output = output.resolve()
    reuse_path = reuse_root / "occurrence_reuse_map.jsonl.gz"
    equivalence_path = equivalence_root / "decisions.jsonl.gz"
    confirmation_path = confirmation_root / "decisions.jsonl.gz"
    actions = reuse.read_jsonl_gz(reuse_path)
    action_by_id = unique_by_id(actions, "reuse map")
    all_ids = set(action_by_id)
    unmatched_ids = {
        occurrence_id
        for occurrence_id, row in action_by_id.items()
        if row["reuse_status"] != "confirmed_existing_group"
    }
    equivalence = unique_by_id(
        reuse.read_jsonl_gz(equivalence_path), "equivalence decisions"
    )
    confirmations = unique_by_id(
        reuse.read_jsonl_gz(confirmation_path),
        "equivalence confirmations",
    )
    if set(equivalence) != unmatched_ids:
        raise RuntimeError(
            "equivalence decisions do not cover every unmatched action"
        )
    proposed_ids = {
        occurrence_id
        for occurrence_id, row in equivalence.items()
        if row["decision"] == "equivalent_action"
    }
    if set(confirmations) != proposed_ids:
        raise RuntimeError(
            "confirmation decisions do not cover every proposed match"
        )

    sets = DisjointSet(sorted(all_ids))
    by_old_group: dict[str, list[str]] = defaultdict(list)
    for occurrence_id, row in action_by_id.items():
        old_group_id = row["confirmed_old_group_id"]
        if old_group_id is not None:
            by_old_group[str(old_group_id)].append(occurrence_id)
    for group_ids in by_old_group.values():
        anchor = group_ids[0]
        for occurrence_id in group_ids[1:]:
            sets.union(anchor, occurrence_id)

    confirmed_edges: list[tuple[str, str]] = []
    rejected_edges = 0
    for occurrence_id in sorted(proposed_ids):
        first = equivalence[occurrence_id]
        confirmation = confirmations[occurrence_id]
        candidate_id = str(
            first["matched_candidate_action_occurrence_id"]
        )
        if candidate_id not in all_ids:
            raise RuntimeError(
                f"equivalence candidate is not a corrected action: "
                f"{candidate_id}"
            )
        confirmed = (
            confirmation["decision"] == "equivalent_action"
            and confirmation["matched_candidate_action_occurrence_id"]
            == candidate_id
        )
        if confirmed:
            sets.union(occurrence_id, candidate_id)
            confirmed_edges.append((occurrence_id, candidate_id))
        else:
            rejected_edges += 1

    component_ids: dict[str, list[str]] = defaultdict(list)
    for occurrence_id in sorted(all_ids):
        component_ids[sets.find(occurrence_id)].append(occurrence_id)
    components = sorted(
        component_ids.values(), key=lambda ids: min(ids)
    )
    group_rows = []
    occurrence_rows = []
    old_alias_components = 0
    new_groups = 0
    for ids in components:
        old_counts = Counter(
            str(action_by_id[occurrence_id]["confirmed_old_group_id"])
            for occurrence_id in ids
            if action_by_id[occurrence_id][
                "confirmed_old_group_id"
            ]
            is not None
        )
        if old_counts:
            primary_old_group = sorted(
                old_counts, key=lambda value: (-old_counts[value], value)
            )[0]
            group_id = primary_old_group
            origin = "existing_action_group"
            if len(old_counts) > 1:
                old_alias_components += 1
        else:
            primary_old_group = None
            group_id = new_group_id(ids)
            origin = "new_corrected_action_group"
            new_groups += 1
        representative_id = min(ids)
        representative = action_by_id[representative_id]
        group_rows.append(
            {
                "action_group_id": group_id,
                "group_origin": origin,
                "primary_old_group_id": primary_old_group,
                "old_group_aliases": sorted(old_counts),
                "action_occurrence_count": len(ids),
                "source_count": len(
                    {
                        str(action_by_id[value]["source_unit_uid"])
                        for value in ids
                    }
                ),
                "representative_action_occurrence_id": representative_id,
                "representative_action": representative["action"],
                "atomic_action_occurrence_ids": ids,
            }
        )
        for occurrence_id in ids:
            row = action_by_id[occurrence_id]
            occurrence_rows.append(
                {
                    **row,
                    "action_group_id": group_id,
                    "group_origin": origin,
                    "primary_old_group_id": primary_old_group,
                    "old_group_aliases": sorted(old_counts),
                }
            )
    occurrence_rows.sort(
        key=lambda row: str(row["atomic_action_occurrence_id"])
    )
    if (
        len(occurrence_rows) != len(actions)
        or {
            str(row["atomic_action_occurrence_id"])
            for row in occurrence_rows
        }
        != all_ids
    ):
        raise RuntimeError("final grouping dropped or duplicated an action")

    output.mkdir(parents=True, exist_ok=True)
    group_path = output / "action_groups.jsonl.gz"
    occurrence_path = output / "occurrence_group_map.jsonl.gz"
    group_artifact = reuse.write_jsonl_gz(group_path, group_rows)
    occurrence_artifact = reuse.write_jsonl_gz(
        occurrence_path, occurrence_rows
    )
    summary = {
        "release_id": release_id,
        "status": "completed",
        "action_occurrences": len(occurrence_rows),
        "action_groups": len(group_rows),
        "existing_action_groups": len(group_rows) - new_groups,
        "new_action_groups": new_groups,
        "confirmed_new_equivalence_edges": len(confirmed_edges),
        "rejected_new_equivalence_edges": rejected_edges,
        "components_with_multiple_old_group_aliases": old_alias_components,
        "all_actions_present_once": True,
        "all_source_and_weight_fields_preserved": True,
        "weights_used_for_matching": False,
        "inputs": [
            reuse.file_identity(reuse_path),
            reuse.file_identity(reuse_root / "release_manifest.json"),
            reuse.file_identity(equivalence_path),
            reuse.file_identity(
                equivalence_root / "release_manifest.json"
            ),
            reuse.file_identity(confirmation_path),
            reuse.file_identity(
                confirmation_root / "release_manifest.json"
            ),
            reuse.file_identity(Path(__file__).resolve()),
        ],
        "outputs": [group_artifact, occurrence_artifact],
    }
    summary_path = output / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    release = {
        **summary,
        "method": (
            "Group actions only through an independently confirmed old-group "
            "match or an independently confirmed corrected-action pair. "
            "Preserve every occurrence and source link."
        ),
        "outputs": [
            group_artifact,
            occurrence_artifact,
            reuse.file_identity(summary_path),
        ],
    }
    release_path = output / "release_manifest.json"
    release_path.write_text(
        json.dumps(release, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return {
        "status": "completed",
        "action_occurrences": len(occurrence_rows),
        "action_groups": len(group_rows),
        "existing_action_groups": len(group_rows) - new_groups,
        "new_action_groups": new_groups,
        "confirmed_new_equivalence_edges": len(confirmed_edges),
        "output": output.relative_to(reuse.REPO_ROOT.resolve()).as_posix(),
        "release_manifest": reuse.file_identity(release_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse-root", type=Path, default=DEFAULT_REUSE_ROOT)
    parser.add_argument(
        "--equivalence-root",
        type=Path,
        default=DEFAULT_EQUIVALENCE_ROOT,
    )
    parser.add_argument(
        "--confirmation-root",
        type=Path,
        default=DEFAULT_CONFIRMATION_ROOT,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--release-id", default=RELEASE_ID)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                args.reuse_root,
                args.equivalence_root,
                args.confirmation_root,
                args.output,
                args.release_id,
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
