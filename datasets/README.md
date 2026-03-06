# VAANI Dataset Documentation

The datasets used to train and evaluate VAANI voice authenticity detection system are **not included in this repository**.

Audio datasets significantly increase repository size and may contain licensing restrictions.  
For this reason, only documentation and dataset sources are provided here.

This file explains **which datasets were used and how to training dataset was constructed.**

---

## Dataset Overview

VAANI was trained on a **balanced dataset of human and AI-generated speech recordings**.

Dataset composition used during development:

Human Speech: 200 samples  
AI Generated Speech: 200 samples  

Total: 400 audio samples.

The goal was to maintain **class balance** to prevent bias during model training.

The audio clips were used **as provided in the original datasets**.

---

## Dataset Sources

Two publicly available datasets were used.

### Medley Deepfake Speech Dataset

Source:

https://data.mendeley.com/datasets/79g59sp69z/1

This dataset contains synthetic speech samples generated using modern voice synthesis systems.

These recordings were used as **AI-generated voice examples**.

---

### Audio Deepfake Detection Dataset (Kaggle)

Source:

https://www.kaggle.com/datasets/adarshsingh0903/audio-deepfake-detection-dataset

This dataset contains both **real human speech recordings and AI-generated voices**.

Samples from this dataset were used for both human and synthetic voice classes.

---

## Dataset Selection Strategy

The dataset was constructed using:

- balanced sampling of human and AI voices
- samples from multiple AI voice generators
- natural human speech recordings with realistic variability

This approach helps to model learn **general characteristics of synthetic speech** rather than artifacts from a single system.

---

## Dataset Structure During Development

During model development, dataset was organized locally as:

```
datasets/
    human/
    ai/
```

Each folder contained `.wav` files used for training and evaluation.

---

## Notes

The dataset is excluded from this repository to:

- keep repository lightweight
- respect dataset licensing
- avoid uploading large binary files to GitHub

Users can recreate the dataset by downloading the sources listed above.
