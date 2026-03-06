# VAANI — Technical Architecture

## 1. System Overview

VAANI is an AI voice authenticity detection system consisting of:

Frontend  
Backend  
Machine Learning Inference Pipeline  
Explainability Layer

## 2. System Components

### Frontend
React + TypeScript + Vite  
Handles audio upload, visualization, and result display.

### Backend
FastAPI server responsible for audio processing and model inference.

### Machine Learning Model
Fusion neural network combining speech embeddings and acoustic features.

### Explainability Layer
AWS Bedrock Claude model used to generate user-friendly explanations.

## 3. Processing Pipeline

Audio Upload  
↓  
Audio Preprocessing  
↓  
Wav2Vec2 Embedding Extraction  
↓  
Acoustic Feature Extraction  
↓  
Feature Fusion Neural Network  
↓  
Probability Output  
↓  
Entropy Calculation  
↓  
Human / AI / Inconclusive Decision

## 4. Feature Extraction

VAANI extracts the following features:

### Speech Embeddings
Wav2Vec2 model generating 1024-dimensional representations.

### Acoustic Signals
- Pitch variance  
- Spectral drift  
- Zero-crossing rate variance

These signals capture irregularities often present in synthetic speech.

## 5. Machine Learning Model

The classifier is a fusion neural network that processes:

- 1024-dimensional speech embeddings  
- 3 acoustic signal features

These inputs are combined to produce a binary classification probability.

## 6. Decision Logic

Model outputs probabilities for:

- Human speech  
- AI generated speech

Entropy is used to measure prediction uncertainty.

If entropy exceeds a threshold the system returns:

"Inconclusive".

## 7. Deployment Architecture

Frontend hosted on Vercel  
Backend deployed on AWS EC2  
Explainability handled using AWS Bedrock Claude

Frontend communicates with backend via REST API.