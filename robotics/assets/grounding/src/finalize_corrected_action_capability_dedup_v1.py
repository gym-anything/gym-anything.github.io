"""Materialize the corrected action capability catalog.

Existing canonical capability groups are fixed. Exact normalized-name matches
reuse them directly. Net-new profiles may join an existing group or one another
only when every cross-pair has three confirmed equivalence decisions.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import build_action_reuse_candidates_v1 as files
import build_capability_semantic_profiles as semantic


GROUNDING_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = GROUNDING_ROOT.parent
DERIVED_ROOT = GROUNDING_ROOT / "data" / "derived"

OLD_ROOT = DERIVED_ROOT / "simulation_capability_dedup_final_full_v2"
OLD_CANONICAL = OLD_ROOT / "canonical_capabilities.jsonl.gz"
OLD_PROFILE_MAP = OLD_ROOT / "profile_to_canonical.jsonl.gz"
OLD_RELEASE = OLD_ROOT / "release_manifest.json"

PROFILE_ROOT = DERIVED_ROOT / "corrected_action_capability_profiles_v1"
NET_NEW_PROFILES = PROFILE_ROOT / "net_new_profiles.jsonl.gz"
EXACT_MATCHES = PROFILE_ROOT / "exact_old_profile_matches.jsonl.gz"
MENTION_MAP = PROFILE_ROOT / "mention_profile_map.jsonl.gz"
PROFILE_RELEASE = PROFILE_ROOT / "release_manifest.json"

CANDIDATE_ROOT = (
    DERIVED_ROOT / "corrected_action_capability_review_candidates_v1"
)
COMBINED_INDEX = CANDIDATE_ROOT / "combined_embedding_index.jsonl.gz"
CANDIDATE_RELEASE = CANDIDATE_ROOT / "release_manifest.json"

RELATION_ROOT = (
    DERIVED_ROOT / "corrected_action_capability_relation_review_batch_v1"
)
RELATION_EDGES = RELATION_ROOT / "relation_edges.jsonl.gz"
RELATION_RELEASE = RELATION_ROOT / "release_manifest.json"

HANDOFF_ROOT = DERIVED_ROOT / "action_capability_handoff_v1"
HANDOFF = HANDOFF_ROOT / "action_group_capabilities.jsonl.gz"
HANDOFF_RELEASE = HANDOFF_ROOT / "release_manifest.json"

DEFAULT_OUTPUT = (
    DERIVED_ROOT / "corrected_action_capability_dedup_final_v1"
)
RELEASE_ID = "corrected-action-capability-dedup-final-v1"
DOMAINS = ("physics_capabilities", "robot_capabilities")


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def new_canonical_id(domain: str, profile_ids: set[str]) -> str:
    digest = hashlib.sha256(
        f"{domain}\0".encode("utf-8")
        + "\0".join(sorted(profile_ids)).encode("utf-8")
    ).hexdigest()[:32]
    return f"canonical-capability-v1:{digest}"


def representative_profile(
    profile_ids: set[str],
    profiles: dict[str, dict[str, object]],
) -> dict[str, object]:
    return min(
        (profiles[profile_id] for profile_id in profile_ids),
        key=lambda row: (
            -int(row["mention_count"]),
            -int(row["action_count"]),
            len(str(row["normalized_name"]).split()),
            len(str(row["normalized_name"])),
            str(row["normalized_name"]),
            str(row["profile_id"]),
        ),
    )


def seeded_complete_link_clusters(
    old_profile_to_canonical: dict[str, str],
    new_profile_ids: set[str],
    index_rows: list[dict[str, object]],
    confirmed_edges: list[dict[str, object]],
) -> tuple[
    list[dict[str, object]],
    dict[str, str],
    int,
]:
    """Extend fixed old groups using only complete confirmed cross-links."""

    old_members: dict[str, set[str]] = defaultdict(set)
    for profile_id, canonical_id in old_profile_to_canonical.items():
        old_members[canonical_id].add(profile_id)

    clusters: dict[str, set[str]] = {}
    old_ids: dict[str, set[str]] = {}
    owner: dict[str, str] = {}
    for canonical_id, members in old_members.items():
        cluster_id = f"old:{canonical_id}"
        clusters[cluster_id] = set(members)
        old_ids[cluster_id] = {canonical_id}
        for profile_id in members:
            owner[profile_id] = cluster_id
    for profile_id in sorted(new_profile_ids):
        cluster_id = f"new:{profile_id}"
        clusters[cluster_id] = {profile_id}
        old_ids[cluster_id] = set()
        owner[profile_id] = cluster_id

    indexed_profile_ids = [
        str(row["profile_id"]) for row in index_rows
    ]
    if len(indexed_profile_ids) != len(set(indexed_profile_ids)):
        raise RuntimeError("combined embedding index contains duplicate profiles")
    if set(indexed_profile_ids) != set(owner):
        raise RuntimeError("combined embedding index differs from profile universe")

    positive: set[tuple[str, str]] = set()
    for edge in confirmed_edges:
        left = indexed_profile_ids[int(edge["left_index"])]
        right = indexed_profile_ids[int(edge["right_index"])]
        positive.add((left, right))
        positive.add((right, left))

    applied_merges = 0
    ordered = sorted(
        confirmed_edges,
        key=lambda edge: (
            -float(edge["cosine_similarity"]),
            str(edge["domain"]),
            int(edge["left_index"]),
            int(edge["right_index"]),
        ),
    )
    for edge in ordered:
        left = indexed_profile_ids[int(edge["left_index"])]
        right = indexed_profile_ids[int(edge["right_index"])]
        left_owner = owner[left]
        right_owner = owner[right]
        if left_owner == right_owner:
            continue

        # The established catalog is an input, not a target for revision.
        if old_ids[left_owner] and old_ids[right_owner]:
            continue
        if not all(
            (first, second) in positive
            for first in clusters[left_owner]
            for second in clusters[right_owner]
        ):
            continue

        merged_members = clusters[left_owner] | clusters[right_owner]
        merged_old_ids = old_ids[left_owner] | old_ids[right_owner]
        keep = min(left_owner, right_owner)
        drop = right_owner if keep == left_owner else left_owner
        clusters[keep] = merged_members
        old_ids[keep] = merged_old_ids
        if drop != keep:
            del clusters[drop]
            del old_ids[drop]
        for profile_id in merged_members:
            owner[profile_id] = keep
        applied_merges += 1

    rows = [
        {
            "members": set(members),
            "old_canonical_ids": set(old_ids[cluster_id]),
        }
        for cluster_id, members in clusters.items()
    ]
    rows.sort(key=lambda row: min(row["members"]))
    return rows, owner, applied_merges


def build(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    required = (
        OLD_CANONICAL,
        OLD_PROFILE_MAP,
        OLD_RELEASE,
        NET_NEW_PROFILES,
        EXACT_MATCHES,
        MENTION_MAP,
        PROFILE_RELEASE,
        COMBINED_INDEX,
        CANDIDATE_RELEASE,
        RELATION_EDGES,
        RELATION_RELEASE,
        HANDOFF,
        HANDOFF_RELEASE,
    )
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"missing required input: {path}")

    old_canonical_rows = files.read_jsonl_gz(OLD_CANONICAL)
    old_profile_rows = files.read_jsonl_gz(OLD_PROFILE_MAP)
    net_new_rows = files.read_jsonl_gz(NET_NEW_PROFILES)
    exact_rows = files.read_jsonl_gz(EXACT_MATCHES)
    mention_rows = files.read_jsonl_gz(MENTION_MAP)
    index_rows = files.read_jsonl_gz(COMBINED_INDEX)
    relation_rows = files.read_jsonl_gz(RELATION_EDGES)
    handoff_rows = files.read_jsonl_gz(HANDOFF)

    old_canonical_by_id = {
        str(row["canonical_capability_id"]): row
        for row in old_canonical_rows
    }
    old_profile_by_id = {
        str(row["profile_id"]): row for row in old_profile_rows
    }
    new_profile_by_id = {
        str(row["profile_id"]): row for row in net_new_rows
    }
    if (
        len(old_canonical_by_id) != len(old_canonical_rows)
        or len(old_profile_by_id) != len(old_profile_rows)
        or len(new_profile_by_id) != len(net_new_rows)
    ):
        raise RuntimeError("input identifiers are not unique")
    if set(old_profile_by_id) & set(new_profile_by_id):
        raise RuntimeError("net-new profiles overlap the old catalog")
    old_profile_ids = set(old_profile_by_id)
    new_profile_ids = set(new_profile_by_id)

    old_profile_to_canonical = {
        profile_id: str(row["canonical_capability_id"])
        for profile_id, row in old_profile_by_id.items()
    }
    confirmed = [
        row
        for row in relation_rows
        if bool(row["triple_confirmed_equivalent"])
    ]
    clusters, _, applied_merges = seeded_complete_link_clusters(
        old_profile_to_canonical,
        new_profile_ids,
        index_rows,
        confirmed,
    )

    exact_by_profile = {
        str(row["profile_id"]): row for row in exact_rows
    }
    if len(exact_by_profile) != len(exact_rows):
        raise RuntimeError("exact-match profiles are not unique")
    if not set(exact_by_profile) <= set(old_profile_by_id):
        raise RuntimeError("exact matches do not resolve to old profiles")

    all_profile_domain = {
        profile_id: str(row["domain"])
        for profile_id, row in old_profile_by_id.items()
    }
    all_profile_domain.update(
        {
            profile_id: str(row["domain"])
            for profile_id, row in new_profile_by_id.items()
        }
    )
    all_profile_name = {
        profile_id: str(row["normalized_name"])
        for profile_id, row in old_profile_by_id.items()
    }
    all_profile_name.update(
        {
            profile_id: str(row["normalized_name"])
            for profile_id, row in new_profile_by_id.items()
        }
    )

    index_profile_ids = [
        str(row["profile_id"]) for row in index_rows
    ]
    confirmed_by_profiles: dict[
        frozenset[str], dict[str, object]
    ] = {}
    for edge in confirmed:
        left = index_profile_ids[int(edge["left_index"])]
        right = index_profile_ids[int(edge["right_index"])]
        confirmed_by_profiles[frozenset((left, right))] = edge

    profile_mapping: dict[str, dict[str, object]] = {}
    cluster_records: list[dict[str, object]] = []
    canonical_ids_seen: set[str] = set()
    old_extended_count = 0
    new_profiles_mapped_to_old = 0
    for cluster in clusters:
        members = set(cluster["members"])
        domains = {all_profile_domain[profile_id] for profile_id in members}
        if len(domains) != 1:
            raise RuntimeError("canonical cluster crosses capability domains")
        domain = domains.pop()
        old_ids = set(cluster["old_canonical_ids"])
        if len(old_ids) > 1:
            raise RuntimeError("canonical cluster merges established groups")
        old_members = members & old_profile_ids
        new_members = members & new_profile_ids

        if old_ids:
            canonical_id = next(iter(old_ids))
            old_row = old_canonical_by_id[canonical_id]
            canonical_name = str(old_row["canonical_name"])
            canonical_profile_id = str(old_row["canonical_profile_id"])
            if new_members:
                old_extended_count += 1
                new_profiles_mapped_to_old += len(new_members)
        else:
            representative = representative_profile(
                new_members, new_profile_by_id
            )
            canonical_id = new_canonical_id(domain, new_members)
            canonical_name = str(representative["normalized_name"])
            canonical_profile_id = str(representative["profile_id"])
            old_row = None
        if canonical_id in canonical_ids_seen:
            raise RuntimeError("canonical ID collision")
        canonical_ids_seen.add(canonical_id)

        aliases: list[dict[str, object]] = []
        old_alias_by_profile = (
            {
                str(alias["profile_id"]): alias
                for alias in old_row["aliases"]
            }
            if old_row is not None
            else {}
        )
        for profile_id in sorted(
            members,
            key=lambda value: (
                value != canonical_profile_id,
                all_profile_name[value],
                value,
            ),
        ):
            if profile_id in old_profile_by_id:
                prior = old_alias_by_profile[profile_id]
                exact = exact_by_profile.get(profile_id)
                aliases.append(
                    {
                        **copy.deepcopy(prior),
                        "source": "existing_profile",
                        "old_mention_count": int(prior["mention_count"]),
                        "new_exact_mention_count": (
                            int(exact["new_mention_count"])
                            if exact is not None
                            else 0
                        ),
                        "new_exact_action_group_count": (
                            int(exact["new_action_count"])
                            if exact is not None
                            else 0
                        ),
                    }
                )
            else:
                profile = new_profile_by_id[profile_id]
                aliases.append(
                    {
                        "profile_id": profile_id,
                        "name": profile["normalized_name"],
                        "mention_count": int(profile["mention_count"]),
                        "action_count": int(profile["action_count"]),
                        "selected_as_canonical": (
                            profile_id == canonical_profile_id
                        ),
                        "source": "net_new_profile",
                    }
                )

        old_pair_count = 0
        new_review_edges: list[dict[str, object]] = []
        ordered_members = sorted(members)
        for position, left in enumerate(ordered_members):
            for right in ordered_members[position + 1 :]:
                left_old = old_profile_to_canonical.get(left)
                right_old = old_profile_to_canonical.get(right)
                if left_old is not None and left_old == right_old:
                    old_pair_count += 1
                    continue
                edge = confirmed_by_profiles.get(frozenset((left, right)))
                if edge is None:
                    raise RuntimeError(
                        "canonical cluster lacks complete cross-pair evidence"
                    )
                new_review_edges.append(edge)
        required_pairs = math.comb(len(members), 2)
        if old_pair_count + len(new_review_edges) != required_pairs:
            raise RuntimeError("complete-link evidence accounting differs")
        scores = [
            float(edge["cosine_similarity"]) for edge in new_review_edges
        ]

        old_mention_count = (
            int(old_row["mention_count"]) if old_row is not None else 0
        )
        new_mention_count = sum(
            int(new_profile_by_id[profile_id]["mention_count"])
            for profile_id in new_members
        ) + sum(
            int(exact_by_profile[profile_id]["new_mention_count"])
            for profile_id in old_members
            if profile_id in exact_by_profile
        )
        record = {
            "canonical_capability_id": canonical_id,
            "domain": domain,
            "canonical_name": canonical_name,
            "canonical_profile_id": canonical_profile_id,
            "catalog_origin": (
                "existing_catalog" if old_ids else "new_canonical"
            ),
            "member_profile_count": len(members),
            "old_member_profile_count": len(old_members),
            "new_member_profile_count": len(new_members),
            "old_mention_count": old_mention_count,
            "new_mention_count": new_mention_count,
            "mention_count": old_mention_count + new_mention_count,
            "aliases": aliases,
            "pairwise_confirmation": {
                "required_pairs": required_pairs,
                "old_catalog_confirmed_pairs": old_pair_count,
                "new_triple_confirmed_pairs": len(new_review_edges),
                "confirmed_pairs": old_pair_count + len(new_review_edges),
                "minimum_new_review_cosine_similarity": (
                    round(min(scores), 8) if scores else None
                ),
                "mean_new_review_cosine_similarity": (
                    round(sum(scores) / len(scores), 8)
                    if scores
                    else None
                ),
                "maximum_new_review_cosine_similarity": (
                    round(max(scores), 8) if scores else None
                ),
                "complete_link_verified": True,
            },
        }
        cluster_records.append(record)
        for profile_id in members:
            profile_mapping[profile_id] = {
                "profile_id": profile_id,
                "domain": domain,
                "normalized_name": all_profile_name[profile_id],
                "profile_source": (
                    "existing_profile"
                    if profile_id in old_profile_by_id
                    else "net_new_profile"
                ),
                "canonical_capability_id": canonical_id,
                "canonical_name": canonical_name,
                "member_profile_count": len(members),
            }

    if len(profile_mapping) != len(old_profile_rows) + len(net_new_rows):
        raise RuntimeError("profile mapping is incomplete")
    for profile_id, old_row in old_profile_by_id.items():
        if (
            profile_mapping[profile_id]["canonical_capability_id"]
            != old_row["canonical_capability_id"]
        ):
            raise RuntimeError("existing canonical mapping changed")

    mapped_mentions: list[dict[str, object]] = []
    new_action_accumulators: dict[
        tuple[str, str, str], dict[str, object]
    ] = {}
    for mention in mention_rows:
        mapped = profile_mapping[str(mention["profile_id"])]
        row = {
            **mention,
            "canonical_capability_id": mapped[
                "canonical_capability_id"
            ],
            "canonical_name": mapped["canonical_name"],
        }
        mapped_mentions.append(row)
        key = (
            str(mention["group_id"]),
            str(mention["domain"]),
            str(mapped["canonical_capability_id"]),
        )
        accumulator = new_action_accumulators.get(key)
        if accumulator is None:
            accumulator = {
                "canonical_capability_id": mapped[
                    "canonical_capability_id"
                ],
                "canonical_name": mapped["canonical_name"],
                "mention_count": 0,
                "sample_indices": set(),
                "source_profile_ids": set(),
            }
            new_action_accumulators[key] = accumulator
        accumulator["mention_count"] = int(
            accumulator["mention_count"]
        ) + 1
        accumulator["sample_indices"].add(int(mention["sample_index"]))
        accumulator["source_profile_ids"].add(str(mention["profile_id"]))

    action_rows: list[dict[str, object]] = []
    assignment_counts: Counter[str] = Counter()
    canonical_action_groups: dict[str, set[str]] = defaultdict(set)
    accumulators_by_group_domain: dict[
        tuple[str, str], list[dict[str, object]]
    ] = defaultdict(list)
    for (group_id, domain, _), accumulator in (
        new_action_accumulators.items()
    ):
        accumulators_by_group_domain[(group_id, domain)].append(accumulator)
    for action_group_index, handoff in enumerate(
        sorted(handoff_rows, key=lambda row: str(row["action_group_id"]))
    ):
        group_id = str(handoff["action_group_id"])
        assignment_kind = str(handoff["capability_assignment_kind"])
        domains: dict[str, list[dict[str, object]]] = {}
        if assignment_kind == "reused_canonical_capabilities":
            source = handoff["reused_canonical_capabilities"]
            for domain in DOMAINS:
                domains[domain] = copy.deepcopy(source[domain])
        elif assignment_kind == (
            "generated_candidates_pending_semantic_deduplication"
        ):
            for domain in DOMAINS:
                values = []
                for accumulator in accumulators_by_group_domain[
                    (group_id, domain)
                ]:
                    values.append(
                        {
                            "canonical_capability_id": accumulator[
                                "canonical_capability_id"
                            ],
                            "canonical_name": accumulator[
                                "canonical_name"
                            ],
                            "mention_count": accumulator["mention_count"],
                            "sample_indices": sorted(
                                accumulator["sample_indices"]
                            ),
                            "source_profile_ids": sorted(
                                accumulator["source_profile_ids"]
                            ),
                        }
                    )
                values.sort(
                    key=lambda row: (
                        str(row["canonical_name"]),
                        str(row["canonical_capability_id"]),
                    )
                )
                domains[domain] = values
        else:
            raise RuntimeError(
                f"unexpected capability assignment: {assignment_kind}"
            )
        assignment_counts.update([assignment_kind])
        action_row = {
            "action_group_index": action_group_index,
            "action_group_id": group_id,
            "representative_action": handoff["representative_action"],
            "representative_action_occurrence_id": handoff[
                "representative_action_occurrence_id"
            ],
            "action_occurrence_count": handoff[
                "action_occurrence_count"
            ],
            "group_origin": handoff["group_origin"],
            "physics_capabilities": domains["physics_capabilities"],
            "robot_capabilities": domains["robot_capabilities"],
        }
        action_rows.append(action_row)
        for domain in DOMAINS:
            for capability in domains[domain]:
                canonical_action_groups[
                    str(capability["canonical_capability_id"])
                ].add(group_id)

    canonical_ids = {
        str(row["canonical_capability_id"]) for row in cluster_records
    }
    if any(
        canonical_id not in canonical_ids
        for canonical_id in canonical_action_groups
    ):
        raise RuntimeError("action mapping references unknown capability")
    for record in cluster_records:
        group_ids = sorted(
            canonical_action_groups[
                str(record["canonical_capability_id"])
            ]
        )
        record["action_group_count"] = len(group_ids)
        record["action_group_ids"] = group_ids

    final_canonical_by_profile = {
        profile_id: str(row["canonical_capability_id"])
        for profile_id, row in profile_mapping.items()
    }
    edge_dispositions: list[dict[str, object]] = []
    for edge in confirmed:
        left_id = index_profile_ids[int(edge["left_index"])]
        right_id = index_profile_ids[int(edge["right_index"])]
        same = (
            final_canonical_by_profile[left_id]
            == final_canonical_by_profile[right_id]
        )
        edge_dispositions.append(
            {
                **edge,
                "left_profile_id": left_id,
                "right_profile_id": right_id,
                "same_final_canonical_capability": same,
                "disposition": (
                    "used_in_complete_link_cluster"
                    if same
                    else "retained_pairwise_only"
                ),
            }
        )

    cluster_records.sort(
        key=lambda row: (
            str(row["domain"]),
            str(row["canonical_name"]),
            str(row["canonical_capability_id"]),
        )
    )
    profile_rows = sorted(
        profile_mapping.values(),
        key=lambda row: (
            str(row["domain"]),
            str(row["normalized_name"]),
            str(row["profile_id"]),
        ),
    )
    mapped_mentions.sort(key=lambda row: int(row["mention_index"]))
    edge_dispositions.sort(key=lambda row: str(row["id"]))

    output.mkdir(parents=True, exist_ok=True)
    canonical_path = output / "canonical_capabilities.jsonl.gz"
    profile_path = output / "profile_to_canonical.jsonl.gz"
    mention_path = output / "mention_to_canonical.jsonl.gz"
    action_path = output / "action_group_canonical_capabilities.jsonl.gz"
    disposition_path = output / "confirmed_edge_dispositions.jsonl.gz"
    artifacts = [
        files.write_jsonl_gz(canonical_path, cluster_records),
        files.write_jsonl_gz(profile_path, profile_rows),
        files.write_jsonl_gz(mention_path, mapped_mentions),
        files.write_jsonl_gz(action_path, action_rows),
        files.write_jsonl_gz(disposition_path, edge_dispositions),
    ]

    canonical_by_domain = Counter(
        str(row["domain"]) for row in cluster_records
    )
    new_cluster_sizes = Counter(
        int(row["new_member_profile_count"])
        for row in cluster_records
        if row["catalog_origin"] == "new_canonical"
    )
    relation_summary = read_json(RELATION_ROOT / "summary.json")
    summary = {
        "release_id": RELEASE_ID,
        "status": "completed",
        "method": (
            "Preserve every existing canonical group. Add a net-new profile "
            "only when every cross-pair in the resulting cluster was "
            "triple-confirmed equivalent."
        ),
        "old_profiles": len(old_profile_rows),
        "old_canonical_capabilities": len(old_canonical_rows),
        "corrected_exact_old_profile_matches": len(exact_rows),
        "net_new_profiles": len(net_new_rows),
        "combined_profiles": len(profile_rows),
        "starting_canonical_units": (
            len(old_canonical_rows) + len(net_new_rows)
        ),
        "canonical_capabilities": len(cluster_records),
        "canonical_capabilities_by_domain": dict(
            sorted(canonical_by_domain.items())
        ),
        "new_canonical_capabilities": sum(
            row["catalog_origin"] == "new_canonical"
            for row in cluster_records
        ),
        "existing_canonical_capabilities_extended": old_extended_count,
        "new_profiles_mapped_to_existing_canonical": (
            new_profiles_mapped_to_old
        ),
        "new_profile_reduction": (
            len(old_canonical_rows)
            + len(net_new_rows)
            - len(cluster_records)
        ),
        "applied_complete_link_merges": applied_merges,
        "new_canonical_cluster_size_distribution": {
            str(size): count
            for size, count in sorted(new_cluster_sizes.items())
        },
        "triple_confirmed_equivalent_edges": len(confirmed),
        "confirmed_edges_internal_to_final_clusters": sum(
            bool(row["same_final_canonical_capability"])
            for row in edge_dispositions
        ),
        "confirmed_edges_retained_pairwise_only": sum(
            not bool(row["same_final_canonical_capability"])
            for row in edge_dispositions
        ),
        "new_mentions_mapped": len(mapped_mentions),
        "action_groups_mapped": len(action_rows),
        "reused_existing_action_groups": assignment_counts[
            "reused_canonical_capabilities"
        ],
        "new_generated_action_groups": assignment_counts[
            "generated_candidates_pending_semantic_deduplication"
        ],
        "semantic_deduplication_cost_usd": relation_summary[
            "all_in_semantic_deduplication_usd"
        ],
        "existing_profile_canonical_ids_changed": 0,
        "unconfirmed_pair_used_inside_cluster": 0,
    }
    summary_path = output / "summary.json"
    semantic.write_json_atomic(summary_path, summary)
    release = {
        **summary,
        "inputs": [
            *[files.file_identity(path) for path in required],
            files.file_identity(RELATION_ROOT / "summary.json"),
            files.file_identity(Path(__file__).resolve()),
        ],
        "outputs": [
            *artifacts,
            files.file_identity(summary_path),
        ],
    }
    semantic.write_json_atomic(output / "release_manifest.json", release)
    return {
        **summary,
        "output": output.relative_to(REPO_ROOT).as_posix(),
    }


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
    canonical = files.read_jsonl_gz(
        output / "canonical_capabilities.jsonl.gz"
    )
    profiles = files.read_jsonl_gz(
        output / "profile_to_canonical.jsonl.gz"
    )
    mentions = files.read_jsonl_gz(
        output / "mention_to_canonical.jsonl.gz"
    )
    actions = files.read_jsonl_gz(
        output / "action_group_canonical_capabilities.jsonl.gz"
    )
    dispositions = files.read_jsonl_gz(
        output / "confirmed_edge_dispositions.jsonl.gz"
    )
    if (
        len(canonical) != int(summary["canonical_capabilities"])
        or len(profiles) != int(summary["combined_profiles"])
        or len(mentions) != int(summary["new_mentions_mapped"])
        or len(actions) != int(summary["action_groups_mapped"])
        or len(dispositions)
        != int(summary["triple_confirmed_equivalent_edges"])
    ):
        raise RuntimeError("verified row counts differ")

    canonical_ids = {
        str(row["canonical_capability_id"]) for row in canonical
    }
    if len(canonical_ids) != len(canonical):
        raise RuntimeError("canonical IDs are not unique")
    profile_by_id = {
        str(row["profile_id"]): row for row in profiles
    }
    if len(profile_by_id) != len(profiles):
        raise RuntimeError("profile IDs are not unique")
    if any(
        str(row["canonical_capability_id"]) not in canonical_ids
        for row in profiles
    ):
        raise RuntimeError("profile references unknown canonical capability")
    for row in canonical:
        confirmation = row["pairwise_confirmation"]
        if (
            int(confirmation["required_pairs"])
            != int(confirmation["confirmed_pairs"])
            or not bool(confirmation["complete_link_verified"])
        ):
            raise RuntimeError("canonical cluster is not complete-link")
    if any(
        str(row["canonical_capability_id"])
        != str(profile_by_id[str(row["profile_id"])][
            "canonical_capability_id"
        ])
        for row in mentions
    ):
        raise RuntimeError("mention mapping differs from profile mapping")
    if [int(row["action_group_index"]) for row in actions] != list(
        range(len(actions))
    ):
        raise RuntimeError("action-group index is not contiguous")
    for action in actions:
        for domain in DOMAINS:
            if any(
                str(row["canonical_capability_id"]) not in canonical_ids
                for row in action[domain]
            ):
                raise RuntimeError(
                    "action references unknown canonical capability"
                )

    old_profiles = files.read_jsonl_gz(OLD_PROFILE_MAP)
    for old in old_profiles:
        current = profile_by_id[str(old["profile_id"])]
        if (
            current["canonical_capability_id"]
            != old["canonical_capability_id"]
        ):
            raise RuntimeError("existing canonical mapping changed")
    return {
        "status": "verified",
        "release_id": RELEASE_ID,
        "combined_profiles": len(profiles),
        "canonical_capabilities": len(canonical),
        "new_profile_reduction": int(summary["new_profile_reduction"]),
        "new_mentions_mapped": len(mentions),
        "action_groups_mapped": len(actions),
        "existing_profile_canonical_ids_changed": 0,
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
