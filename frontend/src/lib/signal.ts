// Deterministic procedural signal library shared by the VAANI waveform and
// terrain renderers. Every function is a pure, time-coherent function of
// (position, time): neighboring positions correlate by construction, so the
// renderers never jitter and never allocate per frame.
//
// Visual language (locked reference):
//  - hero/analysis: center-mirrored voice-like waveform, localized bursts,
//    long quiet zones, spiky-but-dense burst texture
//  - terrain: perspective heightfield sampled into occluded dot rows

export type EnvelopeBin = { min: number; max: number };

/** Development-only tuning parameters, mutated by the wave-debug panel. */
export const debugParams = {
  noise: 1,
  envelope: 1,
  motion: 1,
  layers: 44,
  terrainAmplitude: 1,
  pointDensity: 1,
};

/** Frozen timestamp (seconds) used to render a good static frame under reduced motion. */
export const STATIC_FRAME_SECONDS = 12;

// ---------------------------------------------------------------------------
// Deterministic noise primitives
// ---------------------------------------------------------------------------

function hash1(n: number): number {
  const s = Math.sin(n * 127.1) * 43758.5453123;
  return s - Math.floor(s);
}

function hash2(x: number, y: number): number {
  const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453123;
  return s - Math.floor(s);
}

function smootherstep(f: number): number {
  const x = Math.min(1, Math.max(0, f));
  return x * x * x * (x * (x * 6 - 15) + 10);
}

/** Smooth 1D value noise in [0, 1]. */
function valueNoise(x: number): number {
  const i = Math.floor(x);
  const f = x - i;
  const a = hash1(i);
  const b = hash1(i + 1);
  return a + (b - a) * smootherstep(f);
}

/** Coherent 1D fractal noise, roughly [-1, 1]. */
function fbm(x: number, octaves = 3): number {
  let amp = 0.5;
  let freq = 1;
  let sum = 0;
  let norm = 0;
  for (let o = 0; o < octaves; o += 1) {
    sum += (valueNoise(x * freq) * 2 - 1) * amp;
    norm += amp;
    amp *= 0.5;
    freq *= 2.13;
  }
  return sum / norm;
}

/** Smooth 2D value noise in [0, 1]; coherent along both axes. */
function valueNoise2(x: number, y: number): number {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = smootherstep(x - ix);
  const fy = smootherstep(y - iy);
  const a = hash2(ix, iy);
  const b = hash2(ix + 1, iy);
  const c = hash2(ix, iy + 1);
  const d = hash2(ix + 1, iy + 1);
  return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy;
}

/** Coherent 2D fractal noise, roughly [-1, 1]. */
function fbm2(x: number, y: number, octaves = 3): number {
  let amp = 0.5;
  let fx = 1;
  let fy = 1;
  let sum = 0;
  let norm = 0;
  for (let o = 0; o < octaves; o += 1) {
    sum += (valueNoise2(x * fx, y * fy) * 2 - 1) * amp;
    norm += amp;
    amp *= 0.5;
    fx *= 2.17;
    fy *= 2.09;
  }
  return sum / norm;
}

// ---------------------------------------------------------------------------
// Speech burst envelopes (asymmetric, unevenly spaced, independently wobbling)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Speech burst envelopes: asymmetric syllable packets that breathe and drift
// ---------------------------------------------------------------------------

type Burst = { c: number; a: number; wl: number; wr: number; ph: number; drift: number };

// Locked-reference hero placement (Panel 01):
// - Quiet lead-in [0.0 to 0.12]
// - Dominant hero burst peaking at ~0.21 (amp 0.96, asymmetric rise & fall)
// - Articulation dip [0.32 to 0.40]
// - Central syllable cluster across upload target [0.44 to 0.60] (peaks 0.64 & 0.78)
// - Articulation valley [0.62 to 0.68]
// - Secondary strong voice burst [0.70 to 0.86] (peak 0.82)
// - Gentle trailing cadence to quiet baseline ticks [0.88 to 1.0]
const AMBIENT_BURSTS: Burst[] = [
  { c: 0.09, a: 0.10, wl: 0.020, wr: 0.025, ph: 0.0, drift: 0.004 },
  { c: 0.21, a: 0.96, wl: 0.042, wr: 0.062, ph: 1.7, drift: 0.010 },
  { c: 0.36, a: 0.15, wl: 0.022, wr: 0.032, ph: 3.2, drift: 0.006 },
  { c: 0.47, a: 0.62, wl: 0.034, wr: 0.040, ph: 4.4, drift: 0.009 },
  { c: 0.54, a: 0.78, wl: 0.036, wr: 0.048, ph: 0.8, drift: 0.011 },
  { c: 0.65, a: 0.14, wl: 0.020, wr: 0.028, ph: 2.1, drift: 0.005 },
  { c: 0.78, a: 0.82, wl: 0.038, wr: 0.052, ph: 5.1, drift: 0.010 },
  { c: 0.90, a: 0.30, wl: 0.028, wr: 0.038, ph: 3.8, drift: 0.007 },
];

// Analysis mode: longer, denser, more continuous active voice signal.
const PROCESSING_BURSTS: Burst[] = [
  { c: 0.07, a: 0.40, wl: 0.020, wr: 0.026, ph: 0.3, drift: 0.006 },
  { c: 0.18, a: 0.88, wl: 0.025, wr: 0.038, ph: 2.1, drift: 0.010 },
  { c: 0.29, a: 0.52, wl: 0.022, wr: 0.032, ph: 4.4, drift: 0.008 },
  { c: 0.40, a: 1.00, wl: 0.028, wr: 0.042, ph: 1.2, drift: 0.012 },
  { c: 0.53, a: 0.64, wl: 0.024, wr: 0.034, ph: 3.6, drift: 0.009 },
  { c: 0.64, a: 0.90, wl: 0.026, wr: 0.038, ph: 5.2, drift: 0.011 },
  { c: 0.75, a: 0.48, wl: 0.020, wr: 0.028, ph: 0.9, drift: 0.007 },
  { c: 0.85, a: 0.74, wl: 0.024, wr: 0.036, ph: 2.8, drift: 0.010 },
  { c: 0.94, a: 0.42, wl: 0.020, wr: 0.028, ph: 4.7, drift: 0.006 },
];

const QUIET_FLOOR = 0.022;

function envelopeAt(bursts: Burst[], p: number, t: number): number {
  let e = 0.0;
  for (let i = 0; i < bursts.length; i += 1) {
    const b = bursts[i];
    // Dynamic breathing and position drift over 10s
    const driftCenter = b.c + b.drift * Math.sin(t * 0.42 + b.ph);
    const d = p - driftCenter;
    const wl = b.wl * (1.0 + 0.15 * Math.sin(t * 0.50 + b.ph * 1.3));
    const wr = b.wr * (1.0 + 0.15 * Math.cos(t * 0.45 + b.ph * 0.7));
    const w = d < 0 ? wl : wr;
    // Asymmetric speech packet envelope
    const ampBreath = 0.80 + 0.20 * Math.sin(t * 0.52 + b.ph);
    e += b.a * ampBreath * Math.exp(-(d * d) / (2 * w * w));
  }
  return e;
}

// ---------------------------------------------------------------------------
// Waveform signals:
// Authentic stylized voice signal: asymmetric speech packets + sharp pitch pulses
// + glottal micro-variations + articulation quiet intervals.
// ---------------------------------------------------------------------------

function texturedSignal(bursts: Burst[], p: number, t: number, gain: number): number {
  const tt = t * 0.85 * debugParams.motion;
  const env = envelopeAt(bursts, p, tt) * debugParams.envelope;

  // Sharp pitch-period comb pulses characteristic of voiced speech (jagged bar tops)
  const pitchFreq = 240.0;
  const pitchComb = 0.42 + 0.58 * Math.pow(Math.abs(Math.sin(p * pitchFreq + Math.sin(p * 32.0) * 1.8 - tt * 0.40)), 1.6);

  // Formant resonance envelope (vocal tract filtering)
  const formant1 = 0.78 + 0.22 * Math.cos(p * 92.0 + tt * 0.25);
  const formant2 = 0.82 + 0.18 * Math.sin(p * 48.0 - tt * 0.18);

  // High-frequency speech microstructure (individual stroke height irregularity)
  const glottalJitter = 0.82 + 0.18 * Math.sin(p * 510.0 + tt * 0.6);

  // Traveling packet modulation
  const travelingWave = 0.86 + 0.14 * Math.sin(2 * Math.PI * (p * 5.5 - tt * 0.12) + 0.5);

  // Fine ambient quiet floor ticks outside speech packets
  const quietTick = 0.022 * (0.65 + 0.35 * Math.abs(Math.sin(p * 310.0 - tt * 0.3)));

  // Combine: voice burst texture is active when env > 0.04
  const voiceTexture = pitchComb * formant1 * formant2 * glottalJitter * travelingWave;
  const speechSignal = env * voiceTexture * gain;

  return Math.max(quietTick, speechSignal);
}

/** Hero ambient signal: voice-like bursts, long quiet zones, living shape evolution. */
export function ambientSignal(p: number, t: number): number {
  return texturedSignal(AMBIENT_BURSTS, p, t, 1.0);
}

/** Analysis-screen signal: denser, hotter active speech stream. */
export function processingSignal(p: number, t: number): number {
  return texturedSignal(PROCESSING_BURSTS, p, t, 1.08);
}

// ---------------------------------------------------------------------------
// Terrain heightfield: broad asymmetric masses + coherent detail, sampled per
// (x, depth band, time) by the renderer. Returns roughly [-0.15, 1.1].
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Terrain multi-surface topology: multiple localized overlapping masses,
// non-periodic phase drift, varying envelope widths and depths.
// Matches PANEL 04: independent broad formations across the canvas with
// no single dominant crest.
// ---------------------------------------------------------------------------

export interface LocalizedSurface {
  id: string;
  type: 'dome' | 'ridge';
  center: number;
  width: number;
  depth: number;
  amplitude: number;
  skew: number;
  speed: number;
  phase: number;
  colorTone: 'primary' | 'muted' | 'pale';
  baseAlpha: number;
  baseDotRadius: number;
}

// 9 localized overlapping formations exactly matching Panel 04:
// 1-3. Background rolling hills (pale gray-teal, peeking between midground formations)
// 4. Far-left mound (crisp foreground rise)
// 5. Iconic Left-Center Dome (the prominent rounded centerpiece of Panel 04)
// 6. Center-Left Sloping Ridge (undulating wave decaying down to right)
// 7. Center-Right Sweeping Contour (foreground sweeping wave)
// 8. Far-Right Dome (distinct rounded dome)
// 9. Rightmost Edge Form (trailing acoustic crest)
export const LOCALIZED_SURFACES: LocalizedSurface[] = [
  // 1. Distant Back Hill (behind left-center)
  {
    id: 'back-left',
    type: 'dome',
    center: 0.20,
    width: 0.30,
    depth: 0.18,
    amplitude: 0.56,
    skew: 0.08,
    speed: 0.012,
    phase: 0.7,
    colorTone: 'pale',
    baseAlpha: 0.48,
    baseDotRadius: 0.65,
  },
  // 2. Distant Center-Right Hill (peeking behind center ridges)
  {
    id: 'back-center-right',
    type: 'ridge',
    center: 0.58,
    width: 0.32,
    depth: 0.22,
    amplitude: 0.60,
    skew: 0.10,
    speed: 0.015,
    phase: 2.4,
    colorTone: 'pale',
    baseAlpha: 0.50,
    baseDotRadius: 0.68,
  },
  // 3. Distant Right Hill
  {
    id: 'back-right',
    type: 'dome',
    center: 0.76,
    width: 0.28,
    depth: 0.24,
    amplitude: 0.52,
    skew: -0.05,
    speed: 0.014,
    phase: 4.1,
    colorTone: 'pale',
    baseAlpha: 0.45,
    baseDotRadius: 0.66,
  },
  // 4. Far-Left Mound (Foreground)
  {
    id: 'fore-left-mound',
    type: 'dome',
    center: 0.08,
    width: 0.24,
    depth: 0.78,
    amplitude: 0.56,
    skew: -0.15,
    speed: 0.018,
    phase: 1.2,
    colorTone: 'primary',
    baseAlpha: 0.88,
    baseDotRadius: 0.95,
  },
  // 5. Iconic Left-Center Dome (The centerpiece of Panel 04)
  {
    id: 'iconic-dome',
    type: 'dome',
    center: 0.358,
    width: 0.34,
    depth: 0.48,
    amplitude: 0.88,
    skew: -0.04,
    speed: 0.015,
    phase: 1.8,
    colorTone: 'primary',
    baseAlpha: 0.90,
    baseDotRadius: 0.95,
  },
  // 6. Center-Left Sloping Ridge
  {
    id: 'center-left-ridge',
    type: 'ridge',
    center: 0.536,
    width: 0.30,
    depth: 0.40,
    amplitude: 0.70,
    skew: 0.16,
    speed: 0.017,
    phase: 3.5,
    colorTone: 'muted',
    baseAlpha: 0.78,
    baseDotRadius: 0.88,
  },
  // 7. Center-Right Sweeping Contour
  {
    id: 'center-right-contour',
    type: 'ridge',
    center: 0.670,
    width: 0.28,
    depth: 0.68,
    amplitude: 0.58,
    skew: -0.14,
    speed: 0.016,
    phase: 5.0,
    colorTone: 'primary',
    baseAlpha: 0.84,
    baseDotRadius: 0.98,
  },
  // 8. Far-Right Dome
  {
    id: 'far-right-dome',
    type: 'dome',
    center: 0.848,
    width: 0.28,
    depth: 0.46,
    amplitude: 0.70,
    skew: 0.08,
    speed: 0.019,
    phase: 2.9,
    colorTone: 'muted',
    baseAlpha: 0.80,
    baseDotRadius: 0.90,
  },
  // 9. Rightmost Edge Form
  {
    id: 'rightmost-form',
    type: 'dome',
    center: 0.980,
    width: 0.22,
    depth: 0.64,
    amplitude: 0.54,
    skew: -0.10,
    speed: 0.021,
    phase: 0.9,
    colorTone: 'primary',
    baseAlpha: 0.82,
    baseDotRadius: 0.95,
  },
];

/** Legacy alias for backwards compatibility */
export const SURFACES = LOCALIZED_SURFACES;

/** Legacy heightfield evaluation for backwards compatibility */
export function sampleTerrainSurface(u: number, depthT: number, t: number): { height: number; ripple: number; alphaWeight: number } {
  let netElevation = 0;
  let maxWeight = 0;
  for (let i = 0; i < LOCALIZED_SURFACES.length; i += 1) {
    const s = LOCALIZED_SURFACES[i];
    const dDiff = (depthT - s.depth) / 0.32;
    if (Math.abs(dDiff) > 2.2) continue;
    const dWeight = Math.exp(-0.5 * dDiff * dDiff);
    const dx = u - s.center;
    const w = dx < 0 ? s.width * (1 - s.skew) : s.width * (1 + s.skew);
    const normX = dx / (w * 0.5);
    if (Math.abs(normX) > 2.2) continue;
    const uWeight = Math.exp(-0.5 * normX * normX);
    const contrib = s.amplitude * uWeight * dWeight;
    netElevation += contrib;
    if (contrib > maxWeight) maxWeight = contrib;
  }
  return { height: netElevation, ripple: 0, alphaWeight: maxWeight };
}

export function terrainField(u: number, layerDepth: number, t: number): number {
  return sampleTerrainSurface(u, layerDepth, t).height;
}

// ---------------------------------------------------------------------------
// Real-audio envelope helpers (decoded mode).
// ---------------------------------------------------------------------------

/** Deterministic audio-like envelope used for the local demo result preview. */
export function demoEnvelope(bins: number): EnvelopeBin[] {
  const out: EnvelopeBin[] = new Array(bins);
  for (let i = 0; i < bins; i += 1) {
    const p = (i + 0.5) / bins;
    const s = envelopeAt(PROCESSING_BURSTS, p, 7.3) * 0.92;
    const up = s * (0.78 + 0.22 * (fbm(p * 47 + 11.3, 2) * 0.5 + 0.5));
    const dn = s * (0.74 + 0.26 * (fbm(p * 43 + 31.7, 2) * 0.5 + 0.5));
    out[i] = { min: -dn, max: up };
  }
  return out;
}
