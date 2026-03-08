const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://vaani-13-233-132-63.duckdns.org';

export interface AnalysisResponse {
  label: 'Human' | 'AI' | 'Inconclusive';
  confidence: number;
  entropy: number;
  signals: {
    pitch_variance: number;
    spectral_drift: number;
    zcr_variance: number;
  };
  explanation: {
    summary: string;
    analysis: string;
    recommendation: string;
  };
}

export async function analyzeAudio(audioFile: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('file', audioFile);

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Analysis failed: ${response.status} ${response.statusText}`);
  }

  const result = await response.json();
  
  // Add explanation based on label for UI compatibility
  let explanation = '';
  if (result.label === 'Human') {
    explanation = 'Detected natural pitch variations and spectral patterns consistent with authentic human speech.';
  } else if (result.label === 'AI') {
    explanation = 'Synthetic voice patterns detected with artificial characteristics.';
  } else if (result.label === 'Inconclusive') {
    explanation = 'Audio quality is insufficient for definitive analysis. Please provide a clearer audio sample.';
  }

  return {
    ...result,
    explanation
  };
}
