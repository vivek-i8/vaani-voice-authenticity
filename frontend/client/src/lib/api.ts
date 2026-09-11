const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export interface ExplanationObject {
  summary?: string;
  technical_analysis?: string;
  recommendation?: string;
  model?: string;
}

export interface AnalysisResponse {
  label: 'Human' | 'AI' | 'Inconclusive';
  confidence: number;
  entropy: number;
  signals: {
    pitch_variance: number;
    spectral_drift: number;
    zcr_variance: number;
  };
  explanation?: ExplanationObject;
  explanation_source?: 'claude' | 'mock' | 'fallback';
}

export async function analyzeAudio(audioFile: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('file', audioFile);

  const response = await fetch(`${API_BASE_URL}/api/analyze/`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Analysis failed: ${response.status} ${response.statusText}`);
  }

  const result = await response.json();
  return result;
}
