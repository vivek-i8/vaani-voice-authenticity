"""Deterministic evidence-interpretation engine for VAANI V2.

Consumes structured evidence object and produces deterministic,
evidence-grounded explanations. Never determines or modifies the verdict.

Architecture (Section 12 of Source of Truth):
  Evidence Object -> Deterministic Engine -> Explanation Output

Rules:
- Identical input always produces identical output
- Never changes, overrides, or re-derives the verdict
- Never invents evidence, scores, or probabilities
- Never frames reference examples as proof
- Requires no remote API or LLM
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def generate_explanation(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Generate deterministic explanation from structured evidence.

    Args:
        evidence: Structured evidence object containing:
            - verdict: str (Human|AI|Inconclusive)
            - vaani_signal: dict with model_score, prediction, entropy
            - spectra_signal: dict with model_score, prediction, available
            - agreement: str (agree|disagree|single-model-only)
            - acoustic_features: dict
            - reference_examples: list
            - reference_note: str

    Returns:
        Dict with summary, evidence_cited, technical_analysis, recommendation
    """
    try:
        return _compose_explanation(evidence)
    except Exception as e:
        logger.error(f"Explanation engine error: {e}")
        return _fallback_explanation(evidence)


def _compose_explanation(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Compose explanation from evidence (deterministic)."""
    verdict = evidence.get("verdict", "Inconclusive")
    agreement = evidence.get("agreement", "unknown")
    vaani = evidence.get("vaani_signal", {})
    spectra = evidence.get("spectra_signal", {})
    reference_examples = evidence.get("reference_examples", [])
    reference_note = evidence.get("reference_note", "")

    evidence_cited = []

    # Summary
    if agreement == "agree":
        if verdict == "Human":
            summary = "Both signals agree: the audio appears to be authentic human speech."
        elif verdict == "AI":
            summary = "Both signals agree: the audio shows characteristics of synthetic speech."
        else:
            summary = f"Both signals agree, but the result is {verdict}."
        evidence_cited.extend(["vaani_signal", "spectra_signal"])
    elif agreement == "disagree":
        summary = f"The signals disagree. VAANI says {vaani.get('prediction', '?')}, Spectra says {spectra.get('prediction', '?')}. The verdict is Inconclusive."
        evidence_cited.extend(["vaani_signal", "spectra_signal"])
    else:
        # single-model-only
        summary = f"Only the VAANI signal was available. Result: {verdict}."
        evidence_cited.append("vaani_signal")

    # Technical analysis
    parts = []
    parts.append(f"VAANI score: {vaani.get('model_score', 0):.3f} (prediction: {vaani.get('prediction', '?')})")
    if spectra.get("available", False):
        parts.append(f"Spectra score: {spectra.get('model_score', 0):.3f} (prediction: {spectra.get('prediction', '?')})")
    else:
        parts.append("Spectra-AASIST3: unavailable")

    acoustic = vaani.get("acoustic_features", {})
    if acoustic:
        parts.append(f"Acoustic: pitch_var={acoustic.get('pitch_variance', 0):.4f}, spectral_drift={acoustic.get('spectral_drift', 0):.2f}")

    if reference_examples:
        evidence_cited.append("reference_examples")
        parts.append(f"Reference examples: {len(reference_examples)} comparable clips found")
    elif reference_note:
        parts.append(f"Reference: {reference_note}")

    technical_analysis = ". ".join(parts) + "."

    # Recommendation
    if verdict == "Inconclusive":
        recommendation = "The analysis was inconclusive. Consider providing a clearer audio sample or seeking additional verification."
    elif verdict == "AI":
        recommendation = "Treat this audio with caution. Verify the speaker through another channel."
    else:
        recommendation = "No additional action required based on this analysis alone."

    return {
        "summary": summary,
        "evidence_cited": evidence_cited,
        "technical_analysis": technical_analysis,
        "recommendation": recommendation,
    }


def _fallback_explanation(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal fallback when the engine errors. Still evidence-grounded."""
    verdict = evidence.get("verdict", "Inconclusive")
    vaani_score = evidence.get("vaani_signal", {}).get("model_score", 0)

    return {
        "summary": f"Analysis result: {verdict} (VAANI score: {vaani_score:.3f})",
        "evidence_cited": ["vaani_signal"],
        "technical_analysis": "Explanation engine encountered an internal error.",
        "recommendation": "Consult the raw analysis data.",
    }
