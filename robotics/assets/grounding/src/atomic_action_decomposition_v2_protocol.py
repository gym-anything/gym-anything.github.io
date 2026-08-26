"""Prompt, schema, and validation for the lossless action decomposition."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel


PROTOCOL_VERSION = 2

PROMPT = """Convert each source description into the complete set of atomic physical actions that a general-purpose robot would need to perform the described real-world activity.

This is a decomposition task, not a filtering task. Return exactly one result for every input source, preserve every source_unit_uid exactly, and keep the results in the same order as the inputs.

An atomic physical action is one reusable embodied operation with one main observable physical or sensing transition. Examples of the right level are: insert a key into a keyway; rotate a key until a lock releases; hold a vessel under an outlet; pour liquid to a marked level; cut a specimen into sections; position a sensor against a surface; scan a probe across a region; track moving material with a camera; detach a fastener; align a replacement part; tighten a fastener. Do not return an entire job such as repair a machine, prepare a sample, clean a kitchen, perform an experiment, or play a sport as one action. Do not split actions into muscles, joint trajectories, finger trajectories, or controller commands.

Each action label must name exactly one operation. Do not connect two operations with "and," "or," "then," a comma, or a second active verb. An object may contain alternatives when the physical operation is identical, such as "insert a disc or tape into a player." The following pairs define the required granularity only; they are not a vocabulary to copy:
The response is automatically rejected when "and," "or," or "then" is followed by a second operation in an action label. Split it before returning.

- Wrong: "grasp an item and place it in a cart." Separate it into grasp the item, lift or transport the item if required, and place the item in the cart.
- Wrong: "transport a box to storage and set it down." Separate transport the box from place the box on the storage surface.
- Wrong: "wipe counters and wash or load dishes." Return separate wiping, washing, and loading operations.
- Wrong: "prepare food using kitchen tools." This repeats an umbrella task. Return the actual operations supported by the examples and ordinary procedure, such as rinse an ingredient, peel an ingredient, cut an ingredient, mix ingredients, or transfer food into a cooking vessel.
- Wrong: "loosen lug nuts and raise the vehicle." These are unrelated state transitions and must be separate actions.
- Wrong: "unlatch and open a door" or "open a fuel door and remove its cap." A latch, door, cap, cover, or other separately moving mechanism has its own state transition.
- Wrong: "perform exercises" or "play a sport." Return the characteristic physical operations supported by the activity and its examples, such as lower the body into a squat, extend the body from a squat, strike a ball, catch a ball, or steer a bicycle.

A continuous controlled operation such as steering a moving vehicle, wiping one surface, mixing material, or tracking one process may remain one action. Simultaneous controls that are inseparable parts of that one operation may be named in its tool or support fields, but must not be disguised as a sequence of separate operations.

For every source:

1. Read the complete source text and every supplied example. Identify every stated verb, object, alternative, and physical outcome.
For an everyday-life source, treat the supplied examples as separate activities or alternatives, not as interchangeable synonyms. Evaluate every example on its own. A category that is usually passive can still contain a physical example: for example, sleeping is passive, but getting up requires changing the body from a lying or seated posture to standing. If any supplied example has a robot-relevant physical or sensing action, return actions_found and include it; use coverage_check to state which other examples are nonphysical. Never let the short category label override a more specific physical example.
Do not compress several physical examples into a new umbrella label. Decompose each physical example, then remove only exact duplicate operations.
2. Split conjunctions and alternatives. Every named task phase must be accounted for. If a description says prepare, install, maintain, or repair equipment, cover the distinct physical operations implied by each applicable activity rather than returning one combined label or covering only some of the verbs.
3. Expand broad task verbs into the ordinary physical procedure needed to carry them out. For example, preparing and analyzing a laboratory sample may require retrieving it, placing it on a work surface, dividing or transferring it, adding a reagent, mounting it in a holder, positioning or focusing the instrument, scanning the sample, and acquiring a measurement. Do not stop after preparation and omit the physical instrument operations implied by analysis. The exact actions must follow the source and ordinary professional practice; this example is a guide to the required level of detail, not a list to copy into unrelated tasks.
4. Deliberate embodied inspection, sensing, measurement, scanning, monitoring, aiming, alignment, and verification count. They count when a sensor is moved or placed, and they also count when a stationary camera or other sensor deliberately observes or tracks a physical process. Return the physical sensor positioning, observation, tracking, or measurement operation; exclude only the later mental interpretation of the data.
5. Operating physical equipment counts. Include the ordinary loading, positioning, actuation, regulation, unloading, or shutdown operations that are required by the described task. Do not invent optional or unrelated work.
6. Use ordinary real-world knowledge when a short occupational description omits routine physical steps. Mark those actions ordinary_procedure. Never discard a physical source merely because its tool, material, or exact procedure is not fully specified; use "unspecified" for a genuinely unknown field.
7. Mark a source no_robot_physical_action only when the described activity itself contains no meaningful physical operation for a robot. Purely mental work, purely digital information work, passive states such as sleeping, and internal human biological functions such as swallowing qualify. Incidental walking, typing, or holding posture does not make an otherwise nonphysical task physical. Physical care or manipulation performed on another person does count.
The word "incidental" must not erase a physical method that the source explicitly names. Handwriting, signing, drawing, sketching, marking physical media, handling paper, operating named physical buttons, pedals, switches, scanners, or machines, making deliberate gestures or hand signs, and walking or escorting when locomotion is the task all count. Include an explicitly named physical alternative even when the same high-level information task could also be completed digitally. Internal human ingestion and other biological functions still do not count.
8. Keep each action label short, concrete, independently testable, and limited to one operation. Each action must state the affected object or person, the tool or robot effector, a visible start state, a visible end state, and what wording or ordinary procedure supports it. If the start-to-end description contains an intermediate physical result that could be tested separately, split it.
9. Do not use a fixed vocabulary. Generate the actions required by the source. Do not merge distinct operations merely because they are related.
10. In coverage_check, create one item for each stated verb, conjunction branch, alternative, example, or broad task phase. Use covered_by_actions with the exact action order or orders that cover it. Use no_robot_physical_action with an empty action_orders list only for a described part that is genuinely nonphysical.

Before returning, check every source again against every verb, conjunction, alternative, example, and ordinary physical phase. The coverage_check must show that none was skipped. Add anything physically required that is missing. A source may have an empty actions list only when its status is no_robot_physical_action, and its reason must state why."""

PROMPT_SHA256 = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()

# This is an atomicity grammar check, not an allowed-action vocabulary.  It
# catches a connector followed by an obvious second operation while allowing
# alternatives in the affected object, such as "disc or tape".
SECOND_OPERATION_AFTER_CONNECTOR = re.compile(
    r"\b(?:and|then)\s+(?:"
    r"adjust|aim|align|apply|arrange|attach|bend|carry|catch|clean|close|"
    r"connect|cut|detach|dispense|drag|drill|drop|fasten|fill|focus|fold|"
    r"grasp|grind|hold|insert|inspect|lift|load|lock|loosen|"
    r"measure|mix|mount|move|open|peel|pick|place|position|pour|press|"
    r"pull|push|raise|read|release|remove|replace|rinse|rotate|scan|"
    r"scrape|secure|slice|stack|steer|stir|strike|tighten|track|"
    r"transfer|transport|turn|unfasten|unlatch|unlock|unload|wash|wipe|"
    r"wrap"
    r")\b",
    re.IGNORECASE,
)


class AtomicAction(BaseModel):
    order: int
    action: str
    object_or_person: str
    tool_or_effector: str
    start_state: str
    end_state: str
    evidence_basis: Literal["explicit_source", "ordinary_procedure"]
    support: str


class CoverageItem(BaseModel):
    source_part: str
    disposition: Literal[
        "covered_by_actions",
        "no_robot_physical_action",
    ]
    action_orders: list[int]
    reason: str


class SourceDecomposition(BaseModel):
    source_unit_uid: str
    status: Literal["actions_found", "no_robot_physical_action"]
    reason: str
    coverage_check: list[CoverageItem]
    actions: list[AtomicAction]


class DecompositionBatch(BaseModel):
    results: list[SourceDecomposition]


def source_payload(source: dict[str, object]) -> dict[str, object]:
    """Return only the source evidence the model is allowed to use."""

    return {
        "source_unit_uid": str(source["source_unit_uid"]),
        "source_kind": str(source["source_kind"]),
        "source_text": str(source["source_text"]),
        "context_label": str(source.get("context_label", "")),
        "examples": list(source.get("examples", [])),
    }


def request_contents(sources: list[dict[str, object]]) -> str:
    return (
        PROMPT
        + "\n\nSource descriptions:\n"
        + json.dumps(
            [source_payload(source) for source in sources],
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


def validate_result(
    sources: list[dict[str, object]],
    result: DecompositionBatch,
) -> None:
    expected_ids = [str(source["source_unit_uid"]) for source in sources]
    actual_ids = [row.source_unit_uid for row in result.results]
    if actual_ids != expected_ids:
        missing = sorted(set(expected_ids) - set(actual_ids))
        extras = sorted(set(actual_ids) - set(expected_ids))
        duplicates = sorted(
            uid for uid, count in Counter(actual_ids).items() if count > 1
        )
        raise ValueError(
            "response must contain every source exactly once and in input "
            f"order; missing={missing}, extras={extras}, duplicates={duplicates}"
        )

    for row in result.results:
        if not row.reason.strip():
            raise ValueError(f"blank source reason: {row.source_unit_uid}")
        if not row.coverage_check:
            raise ValueError(
                f"source coverage check is blank: {row.source_unit_uid}"
            )
        if row.status == "actions_found" and not row.actions:
            raise ValueError(
                f"actions_found source has no actions: {row.source_unit_uid}"
            )
        if row.status == "no_robot_physical_action" and row.actions:
            raise ValueError(
                "no_robot_physical_action source has actions: "
                f"{row.source_unit_uid}"
            )
        orders = [action.order for action in row.actions]
        if orders != list(range(1, len(row.actions) + 1)):
            raise ValueError(
                f"action orders are not contiguous: {row.source_unit_uid}"
            )
        for action in row.actions:
            values = (
                action.action,
                action.object_or_person,
                action.tool_or_effector,
                action.start_state,
                action.end_state,
                action.support,
            )
            if any(not value.strip() for value in values):
                raise ValueError(
                    f"blank action field: {row.source_unit_uid}/{action.order}"
                )
            if action.start_state.strip().casefold() == action.end_state.strip().casefold():
                raise ValueError(
                    f"unchanged action state: {row.source_unit_uid}/{action.order}"
                )
            if SECOND_OPERATION_AFTER_CONNECTOR.search(action.action):
                raise ValueError(
                    "action label contains a second operation: "
                    f"{row.source_unit_uid}/{action.order}/{action.action}"
                )
        covered_orders: set[int] = set()
        for item in row.coverage_check:
            if not item.source_part.strip() or not item.reason.strip():
                raise ValueError(
                    f"blank coverage field: {row.source_unit_uid}"
                )
            if item.disposition == "covered_by_actions":
                if not item.action_orders:
                    raise ValueError(
                        f"covered source part has no action: {row.source_unit_uid}"
                    )
                if any(order not in orders for order in item.action_orders):
                    raise ValueError(
                        f"coverage cites unknown action: {row.source_unit_uid}"
                    )
                covered_orders.update(item.action_orders)
            elif item.action_orders:
                raise ValueError(
                    f"nonphysical source part cites action: {row.source_unit_uid}"
                )
        if row.status == "actions_found" and covered_orders != set(orders):
            raise ValueError(
                f"coverage does not cite every action: {row.source_unit_uid}"
            )
        if (
            row.status == "no_robot_physical_action"
            and any(
                item.disposition != "no_robot_physical_action"
                for item in row.coverage_check
            )
        ):
            raise ValueError(
                f"nonphysical source has covered part: {row.source_unit_uid}"
            )
