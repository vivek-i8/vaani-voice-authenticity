# Dataset: In-the-Wild Audio Deepfake Dataset

VAANI trains, evaluates, and retrieves reference evidence from the In-the-Wild Audio Deepfake Dataset (Müller et al., 2022).

## Source and license

- HuggingFace: https://huggingface.co/datasets/mueller91/In-The-Wild
- Paper: Müller, N. M. et al. "Does Audio Deepfake Detection Generalize?" arXiv:2203.16263, 2022
- License: CC-BY-SA-4.0 (Creative Commons Attribution-ShareAlike 4.0 International)
- Credit: VocalSynthesis (attribution.txt in the dataset)

The audio carries CC-BY-SA-4.0 from the original source. This dataset and its audio are not covered by this repository's Apache-2.0 license. Do not redistribute the audio without meeting CC-BY-SA-4.0 terms.

## Contents

- 54 speakers (public figures)
- 31,779 clips: 19,963 bona fide, 11,816 spoof
- About 37.9 hours of audio
- Format: WAV, IEEE float (format tag 3), mono, 16 kHz, 32-bit

The paper describes 58 speakers; the distributed data contains 54 (verified).

## Why the raw data is not committed

The full dataset is about 8 GB. License terms require direct download, and the repository stays small without it. Obtain the data yourself before running training, evaluation, or index building.

## Download

```bash
cd datasets/in_the_wild
curl -L -o release_in_the_wild.zip \
  "https://huggingface.co/datasets/mueller91/In-The-Wild/resolve/main/release_in_the_wild.zip"
unzip release_in_the_wild.zip
rm release_in_the_wild.zip   # optional, frees about 8 GB
```

Expected structure after extraction:

```
datasets/in_the_wild/release_in_the_wild/
├── meta.csv              # file,speaker,label
├── attribution.txt
├── 0.wav
├── 1.wav
└── 31778.wav
```

`meta.csv` labels are `bona-fide` and `spoof`, normalized to `bonafide`/`spoof` by the split script.

## Split generation

```bash
python -m app.ml.create_dataset_split \
  --dataset-dir datasets/in_the_wild/release_in_the_wild \
  --output data/splits/in_the_wild_speaker_split.json \
  --reference-speakers 6 \
  --seed 42 \
  --min-clips 10
```

The script asserts speaker and clip disjointness and fails if either is violated. The generated split is committed at `data/splits/in_the_wild_speaker_split.json`.

## Verified partition statistics (seed=42, reference_speakers=6, min_clips=10)

| Partition | Speakers | Clips | Bonafide | Spoof |
|---|---|---|---|---|
| TRAIN | 33 | 18,013 | 10,753 | 7,260 |
| VALIDATION | 7 | 5,140 | 2,906 | 2,234 |
| TEST | 8 | 7,206 | 5,616 | 1,590 |
| REFERENCE-INDEX | 6 | 1,420 | 688 | 732 |
| Total | 54 | 31,779 | 19,963 | 11,816 |

Partition roles: TRAIN trains the fusion head, VALIDATION is used for threshold tuning and early stopping only, TEST is used for final evaluation only, REFERENCE-INDEX exists for evidence retrieval and is excluded from training and evaluation.

Leakage assertions passed: no speaker appears in more than one partition, no clip appears in more than one partition, 31,779 unique clips across all partitions.

## Reproducibility

- Random seed fixed at 42 for split generation
- All 31,779 clips verified present before split generation
- Evaluation writes `models/vaani_model/eval_report.json`; running it twice produces identical results
- Embedding extraction uses a resumable cache keyed by a config hash (`models/vaani_model/embeddings/`, gitignored)
