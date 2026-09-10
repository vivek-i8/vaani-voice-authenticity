"""Model card endpoint for the Reliability tab.

Returns model identity, evaluation status, thresholds, and known limitations.
If evaluation has not been run, returns explicit "unavailable" status.
"""
import json
import os
from fastapi import APIRouter

router = APIRouter(tags=["model-card"])

METADATA_PATH = "models/vaani_model/metadata.json"
EVAL_REPORT_PATH = "models/vaani_model/eval_report.json"


def _load_json(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


@router.get("/api/model-card")
async def get_model_card():
    """Return the model card for the Reliability tab."""
    metadata = _load_json(METADATA_PATH)
    eval_report = _load_json(EVAL_REPORT_PATH)

    # Base model card
    card = {
        "model_version": "VAANI V2",
        "dataset": "In-the-Wild Audio Deepfake Dataset",
        "split_method": "Speaker-disjoint 4-way split (train/validation/test/reference-index)",
        "spectra_commit": "bc0ded888080ddad493177bb53aa6f5b95219d7c",
        "threshold_constants": {
            "agreement_threshold": 0.60,
            "entropy_threshold": 0.55,
            "min_reference_similarity": 0.5,
        },
        "evaluation": None,
        "known_limitations": [
            "Performance varies significantly by audio quality and recording conditions",
            "The Inconclusive verdict may appear for ambiguous audio — this is a designed behavior, not a failure",
            "This system is not a forensic tool and should not be used as the sole basis for high-stakes decisions",
            "Evaluation has not yet been run on the real In-the-Wild dataset",
        ],
    }

    # Add metadata if available
    if metadata:
        card["training_date"] = metadata.get("training_date")
        card["train_samples"] = metadata.get("data", {}).get("train_samples")

    # Add evaluation if available
    if eval_report and eval_report.get("status") == "complete":
        conditions = eval_report.get("conditions", {})
        card["evaluation"] = {}
        for condition in ["clean", "noisy", "compressed"]:
            if condition in conditions:
                c = conditions[condition]
                card["evaluation"][condition] = {
                    "eer": c.get("eer", -1) / 100 if c.get("eer", -1) >= 0 else None,
                    "accuracy": None,  # Not computed in current evaluate.py
                    "fpr": None,
                    "fnr": None,
                    "n_samples": c.get("n_samples", 0),
                }
        card["evaluation_timestamp"] = eval_report.get("timestamp")
        # Remove the "evaluation not run" limitation if we have real data
        card["known_limitations"] = [
            l for l in card["known_limitations"]
            if "not yet been run" not in l
        ]
    else:
        card["evaluation_status"] = "unavailable"

    return card
