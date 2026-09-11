# VAANI V1

⚠️ **This V1 branch is no longer maintained. VAANI V2 on `main` is the current and recommended version.**

V1 is the original VAANI implementation: a voice authenticity detector that classifies short audio clips as human or AI-generated. It was previously deployed on AWS, with an EC2 backend and Amazon Bedrock generating the explanations. That deployment is retired, so this branch exists for historical and engineering reference only.

The code still runs locally on CPU. The one structural change from the original is the explanation provider: Bedrock was replaced with an OpenRouter-compatible provider behind the same `LLMService` interface, so no AWS account is needed.

## How it works

1. Audio is resampled to 16 kHz mono with librosa.
2. A frozen `facebook/wav2vec2-large-xlsr-53` backbone produces a 1024-dimensional mean-pooled embedding.
3. Three acoustic features are computed: pitch variance, spectral-centroid drift, and zero-crossing-rate variance.
4. The combined 1027-dimensional vector is standardized with a fitted `StandardScaler` and passed through the fusion head (1027 → 256 → 64 → 2, dropout 0.3, softmax).
5. Entropy above 0.55 returns `Inconclusive`. Otherwise the class with the higher probability wins, `Human` or `AI`.

Model artifacts live in `models/vaani_model/` (`fusion_head.pth`, `scaler.pkl`, `metadata.json`, `training_curves.png`).

## Project structure

```
app/
  api/            # active /api/analyze/ route, deprecated /api/v1/* routes
  audio/          # validation and resampling
  core/           # settings, device selection
  llm/            # LLMService, OpenRouter provider, mock provider
  ml/             # inference pipeline, fusion head, acoustic features
  services/       # legacy single and batch clip analysis
frontend/
  client/         # React and Vite app
models/
  vaani_model/    # trained artifacts
tests/            # offline test suite
```

## Running locally

Backend needs Python 3.10 or newer:

```
python -m venv venv
venv\Scripts\activate          # bash: source venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend serves http://127.0.0.1:8000, with API docs at http://127.0.0.1:8000/docs.

The first run downloads the Wav2Vec2 backbone (`facebook/wav2vec2-large-xlsr-53`, about 1.2 GB) from Hugging Face and caches it. Later runs work offline. On Windows, if the console throws `UnicodeEncodeError` on the emoji log output, run with `PYTHONUTF8=1`.

The frontend needs Node.js 18 or newer:

```
cd frontend
npm install
npm run dev
```

It runs at http://localhost:3000 and calls the backend at http://127.0.0.1:8000 by default. Set `VITE_API_BASE_URL` to point elsewhere (see `frontend/.env.example`).

## Configuration

Backend settings live in `.env` (copy `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `USE_LLM` | `false` | `false` means deterministic mock explanations, no API key needed |
| `OPENROUTER_API_KEY` | empty | required when `USE_LLM=true` |
| `OPENROUTER_MODEL` | `anthropic/claude-3.5-sonnet` | any OpenRouter-compatible model id |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter-compatible endpoint |

Every response carries `explanation_source`, which says what produced the explanation: `mock` when no provider was called, `claude` when the configured provider responded, `fallback` when the provider failed and the deterministic built-in text was returned instead.

## API

Active endpoint: `POST /api/analyze/`, multipart form with the file in the `file` field:

```json
{
  "label": "Human | AI | Inconclusive",
  "confidence": 0.0,
  "entropy": 0.0,
  "signals": { "pitch_variance": 0.0, "spectral_drift": 0.0, "zcr_variance": 0.0 },
  "explanation": { "summary": "...", "technical_analysis": "...", "recommendation": "...", "model": "..." },
  "explanation_source": "claude | mock | fallback"
}
```

The deprecated `POST /api/v1/analyze`, `POST /api/v1/analyze/batch`, and `GET /api/v1/health` routes are kept for historical compatibility.

## Accuracy and training data

`metadata.json` records 90.0% test accuracy from the original training run. That is a historical training result on a small dataset (8 base clips, augmented), not a re-validated benchmark. The datasets are not in this repository; see `datasets/README.md` for their sources. Real-world audio with background noise, compression, or unusual microphones can shift the acoustic feature distributions and change results.

## Tests

```
python -m pytest tests/ -v
```

The suite runs offline. No API key and no model download are needed.
