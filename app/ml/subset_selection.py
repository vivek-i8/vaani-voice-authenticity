"""Deterministic speaker-aware class-balanced subset selection for VAANI V2.

Used by the compute-efficient training strategy (Source of Truth, Section 5
amendment): initial fusion-head training runs on a bounded subset of the TRAIN
partition instead of all ~18K clips, with configurable caps so scaling to the
full partition requires no redesign.

Guarantees:
- Deterministic: identical inputs always produce an identical subset (no RNG;
  ordering is fully specified by sorted speaker IDs and sorted clip filenames).
- Speaker-aware: clips are allocated per speaker proportionally to that
  speaker's share of each class, so every TRAIN speaker remains represented.
- Class-balanced: bonafide/spoof counts are equalized up to availability.
- Partition-safe: operates within a single partition dict; never mixes
  partitions. TEST and REFERENCE-INDEX are never passed here by callers.
"""

import copy


BONAFIDE_LABEL = "bonafide"
SPOOF_LABEL = "spoof"


def _clip_label(clip: dict) -> str:
    return clip["label"]


def _class_items(
    partition: dict, label: str
) -> list[tuple[str, dict]]:
    """Collect (speaker_id, clip) pairs of one class, deterministically ordered.

    Ordering: ascending (str(speaker_id), clip file). This makes every downstream
    tie-break reproducible without randomness.
    """
    items: list[tuple[str, dict]] = []
    for speaker_id in sorted(partition.keys(), key=str):
        clips = [
            c
            for c in partition[speaker_id]["clips"]
            if _clip_label(c) == label
        ]
        for clip in sorted(clips, key=lambda c: str(c["file"])):
            items.append((speaker_id, clip))
    return items


def _allocate_proportionally(
    per_speaker_counts: dict[str, int], target: int
) -> dict[str, int]:
    """Largest-remainder allocation of `target` items across speakers.

    Speakers contribute proportionally to their available count, capped by
    availability; unallocated remainder is redistributed to speakers with
    remaining headroom, iterating until the target is met or exhausted.
    Deterministic: ties broken by ascending speaker id.
    """
    speakers = sorted(per_speaker_counts.keys(), key=str)
    total_available = sum(per_speaker_counts.values())
    alloc = {s: 0 for s in speakers}
    remaining = min(target, total_available)

    while remaining > 0:
        pool = [s for s in speakers if alloc[s] < per_speaker_counts[s]]
        if not pool:
            break
        pool_capacity_total = sum(
            per_speaker_counts[s] - alloc[s] for s in pool
        )
        # Proportional share of this round's remaining quota.
        raw = {
            s: (per_speaker_counts[s] - alloc[s]) * remaining / pool_capacity_total
            for s in pool
        }
        # Floor + largest remainders (ties: smaller speaker id first).
        give = {s: int(raw[s]) for s in pool}
        leftovers = remaining - sum(give.values())
        order = sorted(pool, key=lambda s: (-(raw[s] - int(raw[s])), str(s)))
        for s in order[:leftovers]:
            give[s] += 1
        progressed = False
        for s in pool:
            allowed = min(give[s], per_speaker_counts[s] - alloc[s])
            if allowed > 0:
                alloc[s] += allowed
                remaining -= allowed
                progressed = True
        if not progressed:
            break
    return alloc


def select_balanced_subset(partition: dict, cap: int) -> dict:
    """Select a deterministic, class-balanced, speaker-aware subset.

    Args:
        partition: split partition dict mapping speaker_id ->
            {"speaker": str, "clips": [{"file": str, "label": str}, ...]}
        cap: maximum number of clips in the subset.

    Returns:
        New partition dict with the same structure containing at most `cap`
        clips, bonafide/spoof balanced as evenly as availability allows,
        every speaker represented proportionally. Returns a deep copy when
        cap >= total clips.
    """
    if cap <= 0:
        return {}

    total_clips = sum(len(v["clips"]) for v in partition.values())
    if cap >= total_clips:
        return copy.deepcopy(partition)

    bonafide_items = _class_items(partition, BONAFIDE_LABEL)
    spoof_items = _class_items(partition, SPOOF_LABEL)
    n_bonafide = len(bonafide_items)
    n_spoof = len(spoof_items)

    # Equal halves; surplus capacity goes to the other class.
    target_bonafide = min(n_bonafide, cap // 2)
    target_spoof = min(n_spoof, cap - target_bonafide)
    leftover = cap - target_bonafide - target_spoof
    target_bonafide += min(leftover, max(0, n_bonafide - target_bonafide))

    selected_by_class: dict[str, set[tuple[str, str]]] = {
        BONAFIDE_LABEL: set(),
        SPOOF_LABEL: set(),
    }
    for label, items, target in (
        (BONAFIDE_LABEL, bonafide_items, target_bonafide),
        (SPOOF_LABEL, spoof_items, target_spoof),
    ):
        per_speaker: dict[str, int] = {}
        items_by_speaker: dict[str, list[dict]] = {}
        for speaker_id, clip in items:
            key = str(speaker_id)
            per_speaker[key] = per_speaker.get(key, 0) + 1
            items_by_speaker.setdefault(key, []).append(clip)

        alloc = _allocate_proportionally(per_speaker, target)
        chosen = selected_by_class[label]
        for speaker_id, count in alloc.items():
            for clip in items_by_speaker[speaker_id][:count]:
                chosen.add((speaker_id, str(clip["file"])))

    subset: dict = {}
    for speaker_id, speaker_data in partition.items():
        key = str(speaker_id)
        kept = [
            c
            for c in speaker_data["clips"]
            if (key, str(c["file"])) in selected_by_class[_clip_label(c)]
        ]
        if kept:
            subset[speaker_id] = {"speaker": speaker_data["speaker"], "clips": kept}
    return subset


def subset_stats(subset_partition: dict) -> dict:
    """Return {speakers, clips, bonafide, spoof} counts for a subset."""
    bonafide = 0
    spoof = 0
    clips = 0
    for data in subset_partition.values():
        for clip in data["clips"]:
            clips += 1
            if _clip_label(clip) == BONAFIDE_LABEL:
                bonafide += 1
            else:
                spoof += 1
    return {
        "speakers": len(subset_partition),
        "clips": clips,
        "bonafide": bonafide,
        "spoof": spoof,
    }
