export type Verdict = 'Human' | 'AI' | 'Inconclusive';

export type DemoResult = {
  verdict: Verdict;
  modelSignals: {
    wav2vec2FusionModel: { label: string; value: number; note: string };
    spectraAasist3: { label: string; value: number; note: string };
  };
  decisionLogic: { modelAgreement: string; uncertainty: string; rule: string };
  explanation: string;
  acousticEvidence: {
    pitchVariance: number;
    spectralCentroidDrift: number;
    zcrVariance: number;
  };
  referenceMatches: Array<{ reference: string; similarity: number }>;
  reliability: { analysisQuality: string; audioCondition: string; reliability: string; limitation: string };
  degraded: boolean;
};

export type AudioSelection = {
  file: File;
  url: string;
  name: string;
  size: number;
  type: string;
  duration?: number;
  sampleRate?: number;
  channels?: number;
  /** Interleaved [min, max] pairs per display bin, from AudioContext decoding. */
  samples?: number[];
};

export const demoResult: DemoResult = {
  verdict: 'Human',
  modelSignals: {
    wav2vec2FusionModel: { label: 'human', value: 0.91, note: 'Bonafide probability (human)' },
    spectraAasist3: { label: 'human', value: 0.88, note: 'Bonafide probability (human)' },
  },
  decisionLogic: { modelAgreement: 'Yes → Human', uncertainty: 'Low', rule: 'Both models support human' },
  explanation: 'Both models classify the audio as human with high confidence. The acoustic patterns (prosody, spectral characteristics, and noise profile) are consistent with natural human speech, with no significant synthetic artifacts detected.',
  acousticEvidence: { pitchVariance: 0.72, spectralCentroidDrift: 0.18, zcrVariance: 0.21 },
  referenceMatches: [
    { reference: 'Ref #12', similarity: 0.82 },
    { reference: 'Ref #07', similarity: 0.76 },
    { reference: 'Ref #25', similarity: 0.71 },
  ],
  reliability: {
    analysisQuality: 'Good',
    audioCondition: 'Clean',
    reliability: 'High',
    limitation: 'Results may be less reliable for heavily compressed or noisy audio.',
  },
  degraded: false,
};

export const analysisLines = [
  ['00:00:00', '>', 'Initializing analysis pipeline...'],
  ['00:00:00', '✓', 'Audio file loaded'],
  ['00:00:01', '✓', 'Preprocessing audio...'],
  ['00:00:01', '✓', 'Normalizing waveform'],
  ['00:00:02', '✓', 'Extracting acoustic features...'],
  ['00:00:02', '✓', 'Pitch and rhythm analysis'],
  ['00:00:02', '✓', 'Spectral features computed'],
  ['00:00:03', '>', 'Running Wav2Vec2 model inference...'],
  ['00:00:04', '>', 'Running Spectra-AASIST3 inference...'],
  ['00:00:04', '>', 'Applying decision rule...'],
  ['00:00:05', '>', 'Finalizing results...'],
] as const;

export const stages = [
  ['LOAD', 'Audio received'],
  ['PROCESS', 'Preparing audio'],
  ['ANALYZE', 'Running models'],
  ['DECIDE', 'Applying rules'],
  ['COMPLETE', 'Generating results'],
] as const;

export function formatBytes(bytes: number) {
  return bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export function formatTime(seconds: number) {
  if (!Number.isFinite(seconds)) return '00:00.0';
  return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toFixed(1).padStart(4, '0')}`;
}