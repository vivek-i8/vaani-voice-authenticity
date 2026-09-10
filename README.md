# VAANI V2 — Multi-Signal Voice Authenticity Analysis

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![PyTorch](https://img.shields.io/badge/PyTorch-DeepLearning-ee4c2c)
![React](https://img.shields.io/badge/React-Frontend-61dafb)
![License](https://img.shields.io/badge/License-MIT-green)

VAANI V2 is a transparent, evidence-grounded voice authenticity analysis system. It uses **multi-signal analysis** — combining a custom interpretable fusion model with an independent anti-spoofing checkpoint — to produce verdicts backed by retrievable evidence and honest reliability reporting.

**This is not a commercial-grade deepfake detector.** Independent benchmarking shows even large open-source efforts trained on 100K+ utterances score near-random against modern voice cloning. VAANI's goal is transparent, evidence-based analysis: multiple independent signals, retrievable comparison evidence, and reproducible reliability reporting. See the Reliability tab and model card below for actual evaluation metrics by audio condition.

---

## Model Card

| Metric | Clean | Noisy | Compressed |
|---|---|---|---|
| EER | **2.4573%** | **2.4573%** | **53.8818%** |
| Test speakers | \8 | \8 | \8 |
| Conditions | Clean | Noisy | Compressed (mp3/flac) |

*Evaluation on the In-the-Wild test split (8 speakers, 7,206 clips). Thresholds: agreement_threshold=0.60, entropy_threshold=0.55. EER = Equal Error Rate. Clean and noisy conditions use the same EER due to evaluation protocol.*

---

## Architecture

```
Audio Upload
  ↓
Validation / Preprocessing (3-5s, 16kHz, mono)
  ↓
┌─────────────────────────────┐
│  VAANI Fusion Signal        │  ← Wav2Vec2 embeddings + acoustic features
│  (custom trained model)     │     → 2-class probability
├─────────────────────────────┤
│  Spectra-AASIST3 Signal     │  ← Independent anti-spoofing checkpoint
│  (frozen, published)        │     → 2-class probability
└─────────────────────────────┘
  ↓
Deterministic Ensemble Truth Table
  ↓
Reference Evidence Retrieval (nearest-neighbor cosine similarity)
  ↓
Structured Evidence Object
  ↓
Deterministic Explanation Engine
  ↓
API Response → Verdict / Evidence / Reliability UI
```

### Key Design Decisions

- **No generative LLM** — explanations are deterministic and evidence-grounded
- **No paid APIs** — all inference runs locally
- **No AWS / Bedrock / Claude** — V2 removed all paid cloud dependencies
- **Zero ongoing cost** — designed for Oracle Always Free A1 + Cloudflare Pages
- **Evidence, not proof** — reference examples are comparable evidence, never framed as confirmation

---

## How It Works

1. **Upload** a short audio clip (3-5 seconds, WAV/MP3/M4A/FLAC)
2. **Two independent signals** analyze the audio separately
3. **Deterministic ensemble** combines signals using a disclosed truth table
4. **Reference evidence** retrieves comparable clips from the training dataset
5. **Deterministic explanation** interprets the structured evidence (no AI generation)
6. **Results** displayed in three tabs: Verdict, Evidence, Reliability

### Verdict

Shows the classification label, model-reported confidence, and any uncertainty triggers. The confidence score is model-reported confidence — not a validated probability of correctness.

### Evidence

Shows per-model scores, ensemble agreement/disagreement, acoustic features, and nearest-neighbor reference examples with similarity scores. Reference examples are explicitly labeled as comparable evidence, not proof.

### Reliability

Shows the model card, evaluation metrics by audio condition (clean/noisy/compressed), known limitations, and methodology disclosure.

---

## Dataset

VAANI V2 uses the **In-the-Wild Audio Deepfake Dataset** (Müller et al., 2022).

- Source: [https://github.com/RUB-SysSec/In_the_Wild_Audio_Deepfake_Dataset](https://github.com/RUB-SysSec/In_the_Wild_Audio_Deepfake_Dataset)
- License: CC-BY-SA-4.0
- The raw dataset is **not included** in this repository

The dataset is split into four speaker-disjoint partitions:
- **Training** — fusion head training
- **Validation** — threshold tuning only
- **Testing** — final evaluation only (never used for tuning)
- **Reference Index** — evidence retrieval (excluded from training and evaluation)

See `datasets/README.md` for detailed dataset preparation instructions.

---

## Setup

### Backend

```bash
# Clone
git clone https://github.com/vivek-i8/vaani-voice-authenticity.git
cd vaani-voice-authenticity

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Start backend
uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`
API docs at `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`

### Dataset Preparation

```bash
# 1. Download In-the-Wild dataset (see datasets/README.md)
# 2. Generate speaker-disjoint split
python -m app.ml.create_dataset_split --dataset-dir datasets/in_the_wild

# 3. GPU benchmark/pilot (300-500 clips) — required before large runs
python -m app.ml.benchmark_gpu --split data/splits/in_the_wild_speaker_split.json

# 4. Retrain fusion head on deterministic balanced TRAIN subset
#    (--train-cap/--val-cap configurable; omit for full partitions once justified)
python -m app.ml.retrain_fusion \
  --split data/splits/in_the_wild_speaker_split.json \
  --train-cap 7000 --val-cap 2000 --patience 8

# 5. Build reference evidence index
python -m app.ml.build_reference_index --split data/splits/in_the_wild_speaker_split.json

# 6. Run evaluation on TEST partition
python -m app.ml.evaluate --split data/splits/in_the_wild_speaker_split.json
```

---

## Deployment

### Target Architecture

| Component | Target | Status |
|---|---|---|
| Frontend | Cloudflare Pages | Configured |
| Backend | Oracle Always Free Ampere A1 (4 OCPU / 24 GB RAM) | Docker Compose ready |
| Runtime | Docker Compose | docker-compose.yml provided |

### Docker

```bash
cd deploy
docker-compose up -d
```

### Memory Budget

| Component | Estimated Memory |
|---|---|
| Wav2Vec2 XLS-R-53 | ~1.2 GB |
| Fusion Head | ~5 MB |
| Spectra-AASIST3 | ~1.38 GB |
| **Total** | **~2.6 GB** (fits in 24 GB RAM) |

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/ml/test_smoke.py -v      # Architecture smoke tests
python -m pytest tests/ml/test_ensemble.py -v    # Ensemble truth table
python -m pytest tests/explainability/test_engine.py -v  # Explanation engine
```

---

## Technology Stack

### Backend
- **FastAPI** — API server
- **PyTorch** — ML inference
- **HuggingFace Transformers** — Wav2Vec2 backbone
- **Librosa** — audio processing
- **scikit-learn** — feature scaling

### Frontend
- **React 19** + **TypeScript**
- **Vite** — build tool
- **Tailwind CSS** + **shadcn/ui** — design system
- **Recharts** — data visualization
- **Framer Motion** — animations

### Models
- **Wav2Vec2 XLS-R-53** — speech embeddings (frozen backbone)
- **VAANI Fusion Head** — custom trained classifier (1027→256→128→2)
- **Spectra-AASIST3** — independent anti-spoofing signal (Apache-2.0)

---

## Model Card

| Metric | Clean | Noisy | Compressed |
|---|---|---|---|
| EER | **2.4573%** | **2.4573%** | **53.8818%** |
| Test speakers | \8 | \8 | \8 |
| Conditions | Clean | Noisy | Compressed (mp3/flac) |

*Evaluation on the In-the-Wild test split (8 speakers, 7,206 clips). Thresholds: agreement_threshold=0.60, entropy_threshold=0.55. EER = Equal Error Rate. Clean and noisy conditions use the same EER due to evaluation protocol.*

---

## Known Limitations

- Performance varies significantly by audio quality and recording conditions
- The Inconclusive verdict may appear for ambiguous audio — this is designed behavior, not a failure
- This system is not a forensic tool and should not be used as the sole basis for high-stakes decisions
- Background noise, microphone differences, and compression artifacts can affect results
- The compressed-audio condition (53.88% EER) is near-random — results on compressed or low-quality audio should not be relied on

---

## Project Structure

```
vaani-voice-authenticity/
├── app/
│   ├── api/           # API endpoints (analyze, model-card, health)
│   ├── core/          # Device selection (CPU/CUDA)
│   ├── explainability/# Deterministic explanation engine
│   └── ml/            # ML pipeline (inference, ensemble, fusion head)
├── data/splits/       # Speaker-disjoint split JSON
├── datasets/          # Dataset documentation
├── deploy/            # Docker configuration
├── frontend/          # React frontend
├── models/            # Model artifacts
├── tests/             # Test suite
└── requirements.txt
```

---

## License

MIT

---

## Citation

If you use VAANI in research, please cite the In-the-Wild dataset:

> Müller, N. et al. "In the Wild Audio Deepfake Detection Dataset." 2022.
