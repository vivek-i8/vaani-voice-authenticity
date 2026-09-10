# VAANI V2 Dataset Documentation

## Dataset: In-the-Wild Audio Deepfake Dataset

VAANI V2 uses the **In-the-Wild Audio Deepfake Dataset** (Müller et al., 2022) for training, evaluation, and reference evidence.

### Source

- **HuggingFace**: https://huggingface.co/datasets/mueller91/In-The-Wild
- **Paper**: Müller, N. M. et al. "Does Audio Deepfake Detection Generalize?" arXiv:2203.16263, 2022
- **License**: **CC-BY-SA-4.0** (Creative Commons Attribution-ShareAlike 4.0 International)
  - The audio files in this dataset carry the CC-BY-SA-4.0 license from the original source.
  - Do NOT describe this dataset or its audio as Apache-2.0. The underlying audio is CC-BY-SA-4.0.
- **Credit**: VocalSynthesis (attribution.txt in dataset)

### Dataset Summary

- **54 speakers** (celebrities and politicians)
- **31,779 clips** total
  - 19,963 bona-fide (real speech)
  - 11,816 spoof (AI-generated deepfakes)
- **~37.9 hours** total audio (20.7h real, 17.2h fake)
- **Format**: WAV, IEEE float (format tag 3), mono, 16 kHz, 32-bit
- **All clips verified present** after extraction

### Why This Dataset

- Real-world recording conditions (not studio-clean)
- Multiple speakers with varying characteristics
- Appropriate for speaker-disjoint evaluation
- Publicly available for research under CC-BY-SA-4.0

### Why Raw Data Is Not Included

The raw audio dataset is **not committed to this repository** because:
- Audio files are large (~7.7 GB compressed, ~uncompressed on disk)
- Repository should remain lightweight
- License terms require direct download
- Contributors should obtain the data themselves

---

## Dataset Preparation

### 1. Download

```bash
# Download the full dataset ZIP (~8.16 GB) from HuggingFace
cd datasets/in_the_wild
curl -L -o release_in_the_wild.zip \
  "https://huggingface.co/datasets/mueller91/In-The-Wild/resolve/main/release_in_the_wild.zip"

# Extract
unzip release_in_the_wild.zip

# Clean up ZIP (optional, saves ~8 GB)
rm release_in_the_wild.zip
```

### 2. Verify Extraction

After extraction, the expected structure is:

```
datasets/in_the_wild/release_in_the_wild/
├── meta.csv              # file,speaker,label mapping
├── attribution.txt       # dataset credit (VocalSynthesis)
├── 0.wav
├── 1.wav
├── ...
└── 31778.wav
```

**meta.csv** format:
```csv
file,speaker,label
0.wav,Alec Guinness,spoof
1.wav,Alec Guinness,spoof
4.wav,Christopher Hitchens,bona-fide
...
```

Labels in meta.csv: `bona-fide` and `spoof` (normalized to `bonafide`/`spoof` in split script).

### 3. Generate Speaker-Disjoint Split

```bash
cd /path/to/vaani-voice-authenticity
python -m app.ml.create_dataset_split \
  --dataset-dir datasets/in_the_wild/release_in_the_wild \
  --output data/splits/in_the_wild_speaker_split.json \
  --reference-speakers 6 \
  --seed 42 \
  --min-clips 10
```

This creates a four-way speaker-disjoint split:
- **TRAIN** — fusion head training (33 speakers, 18,013 clips)
- **VALIDATION** — threshold tuning only (7 speakers, 5,140 clips)
- **TEST** — final evaluation only (8 speakers, 7,206 clips)
- **REFERENCE-INDEX** — evidence retrieval (6 speakers, 1,420 clips)

**No speaker appears in more than one partition.** The script asserts this and fails loudly if violated.

### 4. Benchmark GPU, Then Retrain Fusion Head (staged)

Training is compute-staged for the development GPU. Do NOT extract all ~18K TRAIN clips or train on the full partition as a first step.

```bash
# 1. GPU benchmark/pilot (300-500 clips) — REQUIRED first.
#    Measures clips/sec, peak VRAM, cache size; recommends initial subset size.
python -m app.ml.benchmark_gpu \
  --split data/splits/in_the_wild_speaker_split.json

# 2. Train fusion head on a deterministic, speaker-aware, class-balanced
#    TRAIN subset (size chosen from the benchmark report). Caps are
#    configurable so scaling to 10K/15K/full TRAIN needs no redesign.
python -m app.ml.retrain_fusion \
  --split data/splits/in_the_wild_speaker_split.json \
  --train-cap 7000 --val-cap 2000 --patience 8

# Omit --train-cap/--val-cap to use the full partitions (only after
# validation results justify the additional computation).
```

Notes:
- Embeddings come from the resumable, config-hashed cache (`models/vaani_model/embeddings/`); interrupted runs resume where they stopped.
- Training uses early stopping with best-validation-checkpoint selection — not a blind fixed epoch budget.
- TEST and REFERENCE-INDEX are never used for training, tuning, or caching.

This generates:
- `models/vaani_model/fusion_head.pth` — trained model weights
- `models/vaani_model/scaler.pkl` — fitted StandardScaler (TRAIN subset only)
- `models/vaani_model/metadata.json` — training metadata incl. subset size + provenance

### 5. Build Reference Evidence Index

```bash
python -m app.ml.build_reference_index \
  --split data/splits/in_the_wild_speaker_split.json
```

This generates:
- `models/vaani_model/reference_index.npz` — L2-normalized embeddings for brute-force cosine retrieval

### 6. Run Evaluation

```bash
python -m app.ml.evaluate \
  --split data/splits/in_the_wild_speaker_split.json
```

This generates:
- `models/vaani_model/eval_report.json` — evaluation metrics under clean/noisy/compressed conditions

---

## Reproducibility

- **Random seed**: Fixed at 42 for split generation
- **Split file**: `data/splits/in_the_wild_speaker_split.json` is committed (the split JSON, not the raw audio)
- **Evaluation**: Run `evaluate.py` twice to verify identical results
- **Model artifacts**: Versioned in `models/vaani_model/` with metadata
- **All 31,779 clips verified present** before split generation

---

## Verified Partition Statistics (seed=42, reference_speakers=6, min_clips=10)

| Partition | Speakers | Clips | Bonafide | Spoof | Bonafide % |
|---|---|---|---|---|---|
| TRAIN | 33 | 18,013 | 10,753 | 7,260 | 59.7% |
| VALIDATION | 7 | 5,140 | 2,906 | 2,234 | 56.5% |
| TEST | 8 | 7,206 | 5,616 | 1,590 | 77.9% |
| REFERENCE-INDEX | 6 | 1,420 | 688 | 732 | 48.5% |
| **Total** | **54** | **31,779** | **19,963** | **11,816** | **62.8%** |

**Leakage assertions passed:**
- [PASS] No speaker appears in more than one partition
- [PASS] 54 speakers assigned across 4 partitions (no duplicates)
- [PASS] No clip appears in more than one partition
- [PASS] 31,779 unique clips across all partitions

---

## Audio Technical Properties

| Property | Value |
|---|---|
| Format | WAV (IEEE float, format tag 3) |
| Channels | Mono (1) |
| Sample rate | 16,000 Hz |
| Bit depth | 32-bit float |
| Encoding | PCM float |

---

## Known Dataset Limitations

- Recording conditions vary significantly across speakers
- Some clips may have background noise or compression artifacts
- Class balance varies per speaker (e.g., Obama: 91% bonafide, Notorious B.I.G.: 96% spoof)
- The dataset is not exhaustive — results should not be overgeneralized
- The paper claims 58 speakers but the actual data contains 54 (verified)
