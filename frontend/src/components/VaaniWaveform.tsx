import { useEffect, useMemo, useRef, type MouseEvent } from 'react';
import {
  ambientSignal,
  demoEnvelope,
  processingSignal,
  STATIC_FRAME_SECONDS,
  type EnvelopeBin,
} from '@/lib/signal';

export type WaveformMode = 'ambient' | 'processing' | 'decoded';

type WaveformProps = {
  mode?: WaveformMode;
  samples?: number[];
  count?: number;
  className?: string;
  progress?: number;
  onSeek?: (fraction: number) => void;
  label?: string;
  isDragging?: boolean;
  audioElement?: HTMLAudioElement | null;
  isPlaying?: boolean;
  morphTarget?: EnvelopeBin[] | null;
  morphProgress?: number; // 0 = procedural, 1 = morphTarget
};

// Web Audio API helper for live audio playback visualization
const audioContextMap = new WeakMap<HTMLAudioElement, { ctx: AudioContext; analyser: AnalyserNode }>();

function getOrCreateAnalyser(audio: HTMLAudioElement): { ctx: AudioContext; analyser: AnalyserNode } | null {
  if (typeof window === 'undefined') return null;
  const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtx) return null;

  let entry = audioContextMap.get(audio);
  if (!entry) {
    try {
      const ctx = new AudioCtx();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.75;
      const source = ctx.createMediaElementSource(audio);
      source.connect(analyser);
      analyser.connect(ctx.destination);
      entry = { ctx, analyser };
      audioContextMap.set(audio, entry);
    } catch {
      return null;
    }
  }
  if (entry.ctx.state === 'suspended') {
    void entry.ctx.resume();
  }
  return entry;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function VaaniWaveform({
  mode = 'ambient',
  samples,
  count = 140,
  className = '',
  progress,
  onSeek,
  label = 'Audio waveform',
  isDragging = false,
  audioElement = null,
  isPlaying = false,
  morphTarget = null,
  morphProgress = 0,
}: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const hoverRef = useRef(false);
  const timeDomainBufferRef = useRef<Float32Array<ArrayBuffer> | null>(null);

  // Decoded envelope is static per (samples, count)
  const decoded = useMemo(() => {
    if (mode !== 'decoded') return null;
    const bins = Math.max(32, count);
    if (samples?.length) {
      const env: EnvelopeBin[] = new Array(bins);
      const group = samples.length / 2 / bins;
      for (let i = 0; i < bins; i += 1) {
        const start = Math.floor(i * group);
        const end = Math.min(samples.length / 2, Math.max(start + 1, Math.floor((i + 1) * group)));
        let min = 0;
        let max = 0;
        for (let j = start; j < end; j += 1) {
          const lo = samples[j * 2];
          const hi = samples[j * 2 + 1];
          if (lo < min) min = lo;
          if (hi > max) max = hi;
        }
        env[i] = { min, max };
      }
      return env;
    }
    return demoEnvelope(bins);
  }, [mode, samples, count]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    let width = 1;
    let height = 1;
    let raf = 0;

    const resize = () => {
      const bounds = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = Math.max(1, bounds.width);
      height = Math.max(1, bounds.height);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const drawAxis = () => {
      const centerY = height / 2;
      ctx.strokeStyle = mode === 'ambient' ? 'hsl(165 19% 87% / 0.40)' : 'hsl(165 19% 87% / 0.65)';
      ctx.lineWidth = 0.75;
      ctx.beginPath();
      ctx.moveTo(0, centerY);
      ctx.lineTo(width, centerY);
      ctx.stroke();
    };

    const drawDecoded = () => {
      if (!decoded) return;
      const bins = decoded.length;
      drawAxis();
      const spacing = width / bins;
      ctx.lineWidth = Math.max(1.0, Math.min(1.4, spacing * 0.36));
      ctx.lineCap = 'round';
      const centerY = height / 2;
      const halfSpan = height * 0.46;
      const playX = progress !== undefined ? progress * width : null;

      // Optional real-time Web Audio live frequency/time wobble when playing
      let audioWobble: Float32Array | null = null;
      if (isPlaying && audioElement) {
        const audioEntry = getOrCreateAnalyser(audioElement);
        if (audioEntry) {
          if (!timeDomainBufferRef.current || timeDomainBufferRef.current.length !== audioEntry.analyser.fftSize) {
            timeDomainBufferRef.current = new Float32Array(audioEntry.analyser.fftSize);
          }
          audioEntry.analyser.getFloatTimeDomainData(timeDomainBufferRef.current);
          audioWobble = timeDomainBufferRef.current;
        }
      }

      for (let i = 0; i < bins; i += 1) {
        const { min, max } = decoded[i];
        const x = (i + 0.5) * spacing;
        let wobble = 1.0;
        if (audioWobble && isPlaying) {
          const sampleIdx = Math.floor((i / bins) * audioWobble.length);
          const sampleVal = Math.abs(audioWobble[sampleIdx] || 0);
          wobble = 1.0 + sampleVal * 0.35;
        }

        const y1 = centerY - max * halfSpan * wobble;
        const y2 = centerY - min * halfSpan * wobble;
        const isPast = progress !== undefined && (i + 0.5) / bins <= progress;
        const amp = Math.max(Math.abs(min), Math.abs(max));

        // Muted teal #5E8F8B with crisp playback hierarchy
        if (isPast) {
          ctx.strokeStyle = 'hsl(175 21% 46% / 0.98)';
        } else if (amp > 0.35) {
          ctx.strokeStyle = 'hsl(175 21% 46% / 0.75)';
        } else {
          ctx.strokeStyle = 'hsl(175 21% 46% / 0.42)';
        }

        ctx.beginPath();
        if (Math.abs(y2 - y1) < 1.4) {
          ctx.moveTo(x, centerY - 0.8);
          ctx.lineTo(x, centerY + 0.8);
        } else {
          ctx.moveTo(x, y1);
          ctx.lineTo(x, y2);
        }
        ctx.stroke();
      }

      // Playhead scrub needle
      if (playX !== null) {
        ctx.strokeStyle = 'hsl(187 43% 16% / 0.75)'; // Charcoal #17363A
        ctx.lineWidth = 1.25;
        ctx.beginPath();
        ctx.moveTo(playX, 8);
        ctx.lineTo(playX, height - 8);
        ctx.stroke();
      }
    };

    const drawProcedural = (seconds: number) => {
      // Stroke density: ~220-270 strokes across standard desktop width (spacing ~3px)
      const strokeCount = Math.max(120, Math.min(270, Math.round(width / 3.05)));
      const spacing = width / strokeCount;
      const centerY = height / 2;
      const isAmbient = mode === 'ambient';
      const halfSpan = isAmbient ? height * 0.32 : height * 0.46;

      drawAxis();

      ctx.lineWidth = isAmbient ? 1.0 : 1.15;
      ctx.lineCap = 'round';

      const sigFn = mode === 'processing' ? processingSignal : ambientSignal;
      const dragBoost = isDragging ? 1.15 : 1.0;

      for (let i = 0; i < strokeCount; i += 1) {
        const p = (i + 0.5) / strokeCount;
        let a = sigFn(p, seconds) * dragBoost;

        // Smooth morphing to uploaded waveform if active
        if (morphProgress > 0 && morphTarget && morphTarget.length > 0) {
          const targetIdx = Math.min(morphTarget.length - 1, Math.floor(p * morphTarget.length));
          const targetBin = morphTarget[targetIdx];
          const targetAmp = Math.max(Math.abs(targetBin.min), Math.abs(targetBin.max));
          a = a * (1 - morphProgress) + targetAmp * morphProgress;
        }

        const x = (i + 0.5) * spacing;
        const half = halfSpan * a;

        // Visual presence: in ambient mode, keep waveform subordinate to upload target
        if (isAmbient) {
          if (a >= 0.40) {
            ctx.strokeStyle = `hsl(175 21% 46% / ${Math.min(0.50, 0.32 + a * 0.20).toFixed(3)})`;
          } else if (a >= 0.15) {
            ctx.strokeStyle = `hsl(175 21% 46% / ${(0.22 + a * 0.20).toFixed(3)})`;
          } else {
            ctx.strokeStyle = 'hsl(175 21% 46% / 0.15)';
          }
        } else {
          // Processing mode
          if (a >= 0.45) {
            ctx.strokeStyle = `hsl(175 21% 46% / ${Math.min(0.96, 0.72 + a * 0.24).toFixed(3)})`;
          } else if (a >= 0.16) {
            ctx.strokeStyle = `hsl(175 21% 46% / ${(0.50 + a * 0.35).toFixed(3)})`;
          } else if (a >= 0.05) {
            ctx.strokeStyle = `hsl(175 21% 46% / ${(0.34 + a * 0.30).toFixed(3)})`;
          } else {
            ctx.strokeStyle = 'hsl(175 21% 46% / 0.28)';
          }
        }

        ctx.beginPath();
        if (half < 1.0) {
          ctx.moveTo(x, centerY - 1.0);
          ctx.lineTo(x, centerY + 1.0);
        } else {
          ctx.moveTo(x, centerY - half);
          ctx.lineTo(x, centerY + half);
        }
        ctx.stroke();
      }
    };

    const drawFrame = (seconds: number) => {
      ctx.clearRect(0, 0, width, height);
      if (mode === 'decoded') {
        drawDecoded();
      } else {
        drawProcedural(seconds);
      }
    };

    resize();
    drawFrame(reducedMotion.matches ? STATIC_FRAME_SECONDS : 0);

    const onResize = () => {
      resize();
      drawFrame(reducedMotion.matches ? STATIC_FRAME_SECONDS : performance.now() / 1000);
    };
    const resizeObserver = new ResizeObserver(onResize);
    resizeObserver.observe(canvas);

    if (reducedMotion.matches) {
      return () => resizeObserver.disconnect();
    }

    const tick = (time: number) => {
      drawFrame(time / 1000);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      resizeObserver.disconnect();
    };
  }, [mode, decoded, progress, isDragging, isPlaying, audioElement, morphTarget, morphProgress]);

  const seek = (event: MouseEvent<HTMLCanvasElement>) => {
    if (!onSeek || !canvasRef.current) return;
    const bounds = canvasRef.current.getBoundingClientRect();
    onSeek(Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width)));
  };

  return (
    <canvas
      ref={canvasRef}
      role="img"
      aria-label={label}
      data-testid="waveform-canvas"
      className={`waveform-canvas ${className}`}
      onClick={seek}
      onMouseEnter={() => { hoverRef.current = true; }}
      onMouseLeave={() => { hoverRef.current = false; }}
    />
  );
}
