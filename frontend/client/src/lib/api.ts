const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * V2 Analysis Response
 * Matches the backend /api/analyze endpoint schema.
 * No LLM explanation -- all explanations are deterministic.
 */
export interface EnsembleSignal {
  score: number;
  prediction: string;
  available?: boolean;
}

export interface ReferenceExample {
  label: string;
  similarity: number;
  source: string;
  speaker_id?: string;
  filename?: string;
}

export interface Explanation {
  summary: string;
  evidence_cited: string[];
  technical_analysis: string;
  recommendation: string;
}

export interface AnalysisResponse {
  verdict: 'Human' | 'AI' | 'Inconclusive';
  confidence: number;
  confidence_note: string;
  entropy: number;
  ensemble: {
    agreement: string;
    vaani_signal: EnsembleSignal;
    spectra_signal: EnsembleSignal;
    available: boolean;
  };
  signals: {
    pitch_variance: number;
    spectral_drift: number;
    zcr_variance: number;
  };
  reference_examples: ReferenceExample[];
  reference_note: string;
  explanation: Explanation;
  status: string;
  degraded: boolean;
}

/**
 * Health Response — /api/health
 */
export interface HealthResponse {
  status: string;
  device: string;
  models: {
    vaani_fusion: boolean;
    spectra_aasist3: boolean;
    reference_index: boolean;
  };
  ensemble_available: boolean;
}

/**
 * Model Card Response — /api/model-card
 */
export interface ModelCardResponse {
  model_version: string;
  spectra_commit: string;
  dataset: string;
  split_method: string;
  threshold_constants: {
    agreement_threshold: number;
    entropy_threshold: number;
    min_reference_similarity: number;
  };
  evaluation: {
    clean: { eer: number; accuracy: number | null; fpr: number | null; fnr: number | null };
    noisy: { eer: number; accuracy: number | null; fpr: number | null; fnr: number | null };
    compressed: { eer: number; accuracy: number | null; fpr: number | null; fnr: number | null };
  } | null;
  known_limitations: string[];
}

/**
 * Error Response from the API
 */
export interface ApiErrorResponse {
  detail: string;
  status_code: number;
  degraded?: boolean;
}

export async function analyzeAudio(audioFile: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('file', audioFile);

  const targetUrl = API_BASE_URL ? `${API_BASE_URL}/api/analyze` : '/api/analyze';
  const response = await fetch(targetUrl, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Analysis failed (${response.status}): ${errorBody}`);
  }

  return response.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const targetUrl = API_BASE_URL ? `${API_BASE_URL}/api/health` : '/api/health';
  const response = await fetch(targetUrl, { method: 'GET' });

  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }

  return response.json();
}

export async function fetchModelCard(): Promise<ModelCardResponse> {
  const targetUrl = API_BASE_URL ? `${API_BASE_URL}/api/model-card` : '/api/model-card';
  const response = await fetch(targetUrl, { method: 'GET' });

  if (!response.ok) {
    throw new Error(`Model card fetch failed (${response.status})`);
  }

  return response.json();
}
