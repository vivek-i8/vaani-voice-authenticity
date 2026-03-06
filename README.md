# VAANI — AI Voice Authenticity Detection System

VAANI detects AI-generated voices using neural acoustic analysis and speech signal modeling.  
The system analyzes short audio clips and determines whether the voice is human or synthetic.

---

## Problem Statement

AI voice cloning tools can now replicate human voices with high realism.  
These technologies are increasingly used in scam calls, misinformation, and identity fraud.

Detecting whether a voice recording is human or AI-generated has therefore become an important security challenge.

VAANI was built to address this problem by analyzing acoustic characteristics of speech and identifying patterns typical of synthetic voices.

---

## Solution Overview

VAANI analyzes uploaded voice recordings and classifies them as:

• Human Voice  
• AI Generated Voice  
• Inconclusive  

The system extracts acoustic signals from speech and combines them with deep speech embeddings to determine authenticity.

The final output includes:

• Prediction label  
• Confidence score  
• Signal certainty metrics  
• Acoustic feature analysis

---

## System Architecture

User (Browser)  
↓  
Frontend (React + Vite)  
↓  
FastAPI Backend  
↓  
Audio Processing Pipeline  
↓  
Feature Extraction  
• Wav2Vec2 embeddings  
• Acoustic signal features  
↓  
Fusion Neural Network  
↓  
Confidence & Entropy Calculation  
↓  
Explainability Layer (AWS Bedrock - Claude)  
↓  
Final Result Returned to User

The frontend communicates with the backend API, which processes audio and runs the machine learning model.

---

## How the System Works

Audio Upload  
↓  
Audio Preprocessing  
↓  
Wav2Vec2 Embedding Extraction  
↓  
Acoustic Feature Extraction  
↓  
Fusion Neural Network Classification  
↓  
Confidence and Entropy Calculation  
↓  
Human / AI / Inconclusive Result

Entropy is used to determine uncertainty in predictions.

---

## Tech Stack

### Backend
- FastAPI
- PyTorch
- HuggingFace Transformers
- Librosa

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS

### Infrastructure
- AWS EC2
- AWS Bedrock (Claude) for explainability

---

## Quick Start

Clone the repository:

```
git clone https://github.com/<username>/vaani.git
cd vaani
```

Backend setup:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Start the backend server:

```
uvicorn app.main:app --reload
```

The backend API will run at:

http://127.0.0.1:8000

Swagger API documentation:

http://127.0.0.1:8000/docs

Frontend setup (new terminal):

```
cd frontend
npm install
npm run dev
```

Frontend will run at:

http://localhost:3000

---

## Dataset Sources

Datasets used:

Medley Deepfake Speech Dataset  
https://data.mendeley.com/datasets/79g59sp69z/1

Audio Deepfake Detection Dataset (Kaggle)  
https://www.kaggle.com/datasets/adarshsingh0903/audio-deepfake-detection-dataset

These datasets were used to create a balanced dataset of human and AI-generated speech samples. Datasets are not included in this repository due to size and licensing considerations.

---

## Model Architecture

VAANI uses a fusion architecture combining:

• Wav2Vec2 speech embeddings (1024-dimensional)

• Acoustic speech features
  - Pitch variance
  - Spectral drift
  - Zero-crossing rate variance

These signals are combined and processed by a neural network classifier that produces authenticity predictions.

Entropy is used to detect uncertain predictions and label them as "Inconclusive".

---

## Project Structure

```
vaani
├ app
├ frontend
├ models
├ datasets
├ docs
├ requirements.txt
└ train_fusion_model.py
```

The backend handles inference while the frontend provides the user interface.

---

## Future Improvements

• Real-time call detection  
• Larger training datasets  
• Improved detection of advanced voice cloning models  
• Mobile application interface

---

## Limitations and Future Work

VAANI is currently trained on curated public datasets for AI voice detection.  
While the system performs reliably on benchmark evaluation samples, real-world voice recordings may introduce additional acoustic variations such as:

- background noise
- microphone response differences
- audio compression artifacts (e.g., MP3 encoding)
- room reverberation

These variations can shift acoustic feature distributions and occasionally affect classification performance.

The current prototype focuses on validating the core architecture combining speech embeddings and acoustic signal analysis.

Future versions of VAANI will improve robustness through:

- expanding the training dataset with real-world microphone recordings
- including compressed audio formats such as MP3
- applying audio augmentation techniques (noise, reverberation, device simulation)
- improving feature normalization and calibration
- extending evaluation across more diverse voice environments

These improvements will allow VAANI to generalize more effectively to real-world audio conditions.
