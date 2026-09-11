# VAANI

VAANI is a voice authenticity analysis service. Upload a short audio clip and it returns a Human, AI, or Inconclusive verdict with per-model scores, acoustic features, comparable reference examples, and a reliability report.

## What it does

VAANI runs two independent classifiers on each clip and combines their outputs with a deterministic rule table. One classifier is a fusion head trained by this project on Wav2Vec2 embeddings plus three acoustic features. The other is the published Spectra-AASIST3 anti-spoofing model, used as an independent second opinion. When the two signals disagree, when a score falls in an ambiguous band, or when the fusion head's output entropy is high, the API returns Inconclusive instead of forcing a guess. Reference retrieval finds the closest clips in the training dataset by cosine similarity so a reader can compare evidence. Explanations come from a deterministic engine that reads the structured evidence object. No generative model produces any part of the output.

The intended use is analyzing short speech clips when you want the basis for a verdict to be inspectable. It is not a forensic tool and should not be the only basis for a high-stakes decision.

## V2

`main` is V2, the current version. V1 is retired and preserved on the `v1-legacy` branch.

V2 replaced the V1 design (single model, LLM-generated explanations) with the multi-signal pipeline described here.

## How it works

1. Upload an audio file through the frontend or POST it to the API. The backend accepts formats the installed audio libraries can decode, including WAV, MP3, FLAC, and M4A. Audio is resampled to 16 kHz mono, clips under 3 seconds are rejected, and clips above 5 seconds are truncated. Max upload size is 20 MB.
2. The fusion signal extracts a 1024-dimensional Wav2Vec2 embedding (mean pooling over the last hidden state) and three acoustic features (pitch variance, spectral centroid drift, zero-crossing rate variance). The 1027-dimensional vector is standardized with a scaler fitted on training data, then classified by the fusion head.
3. The Spectra-AASIST3 signal scores the raw waveform independently. If its weights are unavailable, the pipeline runs in degraded mode: the VAANI signal alone decides, and the response is labeled `degraded`.
4. The ensemble applies a disclosed rule table with two thresholds: scores at 0.60 or higher in p(bona fide) direction count as Human, at 0.40 or lower as AI, in between is ambiguous. Fusion-head entropy above 0.55 forces Inconclusive. Agreement between signals determines the verdict; disagreement returns Inconclusive.
5. Reference retrieval embeds the query with the same Wav2Vec2 backbone and returns up to 3 nearest neighbors with cosine similarity at 0.5 or above, drawn from 1,420 reference-index clips that are excluded from training and evaluation.
6. The explanation engine turns the structured evidence into summary, technical analysis, and recommendation text. Identical input produces identical output.

## Model

- Backbone: `facebook/wav2vec2-large-xlsr-53`, frozen, 1024-dim mean-pooled embeddings
- Fusion head: `Linear(1027, 256) -> ReLU -> Dropout(0.2) -> Linear(256, 128) -> ReLU -> Dropout(0.2) -> Linear(128, 2)`, trained by this project
- Second signal: `lab260/Spectra-AASIST3` at commit `bc0ded88` (Apache-2.0), used as published
- Input: mono audio resampled to 16 kHz, 3 to 5 seconds
- Decision: deterministic rule table, thresholds `agreement_threshold=0.60`, `entropy_threshold=0.55`
- Reference retrieval: brute-force cosine similarity over 1,420 L2-normalized embeddings, top 3, minimum similarity 0.5
- Scaler: `StandardScaler` fitted on the 18,013-clip training subset

Evaluation on the In-the-Wild test split (8 speakers, 7,206 clips), produced by `app/ml/evaluate.py` and stored in `models/vaani_model/eval_report.json`:

| Condition | EER | Samples |
|---|---|---|
| Clean | 2.4573% | 7,206 |
| Noisy | 2.4573% | 7,206 |
| Compressed | 53.8818% | 7,206 |

Clean and noisy share the same EER because the evaluation protocol adds synthetic noise at low amplitude; the fusion-head scores change little under it. The compressed condition quantizes audio to 16-bit and degrades near random chance, so compressed-audio results should not be relied on. EER is the equal error rate. The compressed number is the honest result of this protocol and is reported as-is.

## API

Base URL defaults to `http://127.0.0.1:8000`. Interactive docs at `/docs`.

### POST /api/analyze

Multipart form field `file` containing an audio clip.

```json
{
  "verdict": "Human",
  "confidence": 0.78,
  "confidence_note": "model-reported confidence, not a validated probability of correctness",
  "entropy": 0.21,
  "ensemble": {
    "agreement": "agree",
    "vaani_signal": { "score": 0.81, "prediction": "Human" },
    "spectra_signal": { "score": 0.75, "prediction": "Human", "available": true },
    "available": true
  },
  "signals": {
    "pitch_variance": 0.0012,
    "spectral_drift": 1432.5,
    "zcr_variance": 0.018
  },
  "reference_examples": [
    { "label": "bonafide", "similarity": 0.86, "source": "In-the-Wild", "source_id": "12.wav", "speaker_id": "..." }
  ],
  "reference_note": "Compared against 1,420 reference clips from In-the-Wild dataset",
  "explanation": {
    "summary": "Both signals agree: the audio appears to be authentic human speech.",
    "evidence_cited": ["vaani_signal", "spectra_signal", "reference_examples"],
    "technical_analysis": "VAANI score: 0.812 (prediction: Human). Spectra score: 0.753 (prediction: Human). ...",
    "recommendation": "No additional action required based on this analysis alone."
  },
  "status": "ok",
  "degraded": false
}
```

`verdict` is `Human`, `AI`, or `Inconclusive`. `confidence` averages the two p(bona fide) scores. `degraded` is true when the ensemble ran with the VAANI signal only. Error responses use FastAPI's `{"detail": "..."}` shape with status 400 (bad input), 413 (over 20 MB), or 500.

Example call:

```bash
curl -F "file=@clip.wav" http://127.0.0.1:8000/api/analyze
```

### GET /api/model-card

Returns model identity, threshold constants, evaluation metrics by condition (from `models/vaani_model/eval_report.json`, or `evaluation_status: "unavailable"` if absent), and known limitations. Consumed by the frontend Reliability tab.

### GET /api/health

Returns `status` (`ok` or `partial`), per-model load flags, and the torch device in use.

## Local development

Prerequisites: Python 3.11 or later, Node.js 18 or later. The first backend start downloads the two pretrained models from HuggingFace (about 2.6 GB total), so allow disk space and time.

Backend:

```bash
python -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload     # serves http://127.0.0.1:8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev                       # serves http://localhost:3000
```

Environment variables (both optional):

- Backend: none required. Models load from HuggingFace by repo id.
- Frontend: `VITE_API_BASE_URL` points the client at the backend. Defaults to same-origin requests (`/api/...`). See `frontend/.env.example`.

## Testing

```bash
python -m pytest tests/ -v
```

43 tests pass, 1 skipped by design (an integration test that needs the real models). Coverage: ensemble truth table, explanation engine output shape and determinism, fusion head shapes and probability properties, scaler round-trip, embedding cache config hashing, deterministic subset selection, and API route tests with FastAPI's test client.

## Data and model provenance

Training and evaluation use the In-the-Wild Audio Deepfake Dataset (Müller et al., 2022): 31,779 clips, 54 speakers, CC-BY-SA-4.0. The raw audio is not included in this repository; see `datasets/README.md` for download, the committed speaker-disjoint split (`data/splits/in_the_wild_speaker_split.json`), and preparation commands. Dataset audio retains its own license and is not covered by this repository's license.

Third-party models, used as published:

- `facebook/wav2vec2-large-xlsr-53`, Apache-2.0 (VAANI signal backbone)
- `facebook/wav2vec2-xls-r-300m`, Apache-2.0 (SSL encoder inside Spectra-AASIST3)
- `lab260/Spectra-AASIST3`, Apache-2.0 (second signal, pinned at commit `bc0ded88`)

Spectra-AASIST3's `model.py` is vendored with modification in `app/ml/vendor/` under Apache-2.0. The vendored files retain their upstream provenance notes.

## License

This project is licensed under the Apache License, Version 2.0. See the `LICENSE` file for the full text.

Third-party models and the dataset keep their own licenses. The In-the-Wild dataset is CC-BY-SA-4.0. Apache-2.0 in this repository covers the project's original code and model work only.
