"""Unit tests for deterministic subset selection."""
import pytest

from app.ml.subset_selection import select_balanced_subset, subset_stats


def _make_partition(per_speaker_clips):
    """per_speaker_clips: {speaker_id: [(file, label), ...]} -> partition dict."""
    return {
        sid: {
            "speaker": f"spk_{sid}",
            "clips": [{"file": f, "label": lbl} for f, lbl in clips],
        }
        for sid, clips in per_speaker_clips.items()
    }


def _partition_from_stats(speakers_bonafide, speakers_spoof, seed_offset=0):
    """Build a partition with n bonafide and m spoof clips per speaker."""
    part = {}
    fid = 0
    for i in range(len(speakers_bonafide)):
        clips = [
            {"file": f"{fid + j}.wav", "label": "bonafide"}
            for j in range(speakers_bonafide[i])
        ]
        fid += speakers_bonafide[i]
        if i < len(speakers_spoof):
            clips += [
                {"file": f"{fid + j}.wav", "label": "spoof"}
                for j in range(speakers_spoof[i])
            ]
            fid += speakers_spoof[i]
        part[str(i + seed_offset)] = {"speaker": f"spk{i}", "clips": clips}
    return part


class TestSelectBalancedSubset:

    def test_respects_cap(self):
        part = _partition_from_stats([30] * 5, [20] * 5)
        sub = select_balanced_subset(part, 50)
        assert subset_stats(sub)["clips"] == 50

    def test_class_balanced(self):
        part = _partition_from_stats([30] * 5, [20] * 5)
        s = subset_stats(select_balanced_subset(part, 40))
        assert s["bonafide"] == 20
        assert s["spoof"] == 20

    def test_all_speakers_represented(self):
        part = _partition_from_stats([30] * 10, [20] * 10)
        sub = select_balanced_subset(part, 60)
        assert subset_stats(sub)["speakers"] == 10

    def test_proportional_allocation(self):
        # Speaker 0 has double the clips of speaker 1; should get ~double share.
        part = _partition_from_stats([40, 20], [40, 20])
        s = subset_stats(select_balanced_subset(part, 20))
        counts = {}
        for sid, data in select_balanced_subset(part, 20).items():
            counts[sid] = len(data["clips"])
        # proportional: speaker "0" ~13-14, speaker "1" ~6-7
        assert counts["0"] > counts["1"]
        assert abs(counts["0"] - 2 * counts["1"]) <= 2

    def test_deterministic(self):
        part = _partition_from_stats([25] * 6, [15] * 6)
        files1 = sorted(
            c["file"] for d in select_balanced_subset(part, 48).values() for c in d["clips"]
        )
        files2 = sorted(
            c["file"] for d in select_balanced_subset(part, 48).values() for c in d["clips"]
        )
        assert files1 == files2

    def test_cap_ge_total_returns_copy(self):
        part = _partition_from_stats([3, 3], [2, 2])
        sub = select_balanced_subset(part, 999)
        assert subset_stats(sub)["clips"] == 10
        # deep copy: mutating subset must not touch original
        next(iter(sub.values()))["clips"].clear()
        assert sum(len(d["clips"]) for d in part.values()) == 10

    def test_zero_cap_empty(self):
        part = _partition_from_stats([5], [5])
        assert select_balanced_subset(part, 0) == {}

    def test_uneven_classes_fills_surplus(self):
        # Only 8 spoof available; cap 30 -> 15 bonafide + min(15, 8) spoof,
        # surplus goes to bonafide.
        part = _partition_from_stats([30], [8])
        s = subset_stats(select_balanced_subset(part, 30))
        assert s["spoof"] == 8
        assert s["bonafide"] == 22

    def test_no_label_mixing_within_clip_identity(self):
        part = _partition_from_stats([10, 10], [10, 10])
        sub = select_balanced_subset(part, 20)
        labels = {c["label"] for d in sub.values() for c in d["clips"]}
        assert labels <= {"bonafide", "spoof"}
        files = [c["file"] for d in sub.values() for c in d["clips"]]
        assert len(files) == len(set(files))
