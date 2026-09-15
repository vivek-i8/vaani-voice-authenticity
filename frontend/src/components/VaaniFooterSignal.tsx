import { useEffect, useRef } from 'react';

const COLOR_MODEL_01 = 'rgb(23, 54, 58)';       // #17363A Dark Charcoal Teal
const COLOR_MODEL_02 = 'rgb(104, 155, 149)';     // #689B95 Muted Teal

// Evaluate Model 01 base silhouette (centerline Y and local amplitude)
// Features from reference:
// - starts at x ~ 0 with cy = 0.38 (aligned with Model 01 dash)
// - first major swell peaking at x ~ 0.28 (cy ~ 0.26, amp ~ 0.12)
// - dip to cross Model 02 at x ~ 0.40 (cy ~ 0.48, amp ~ 0.045)
// - dominant grand peak at x ~ 0.60 (cy ~ 0.20, amp ~ 0.175)
// - trailing wave at x ~ 0.74 (cy ~ 0.44, amp ~ 0.065)
// - convergence into center baseline (cy = 0.50, amp -> 0) at x > 0.84
function evalModel01(x: number, t: number) {
  // Base centerline Y in [0, 1] (0 = top, 1 = bottom)
  let cy = 0.50;
  // Left baseline alignment with Model 01 label
  const leftBlend = Math.max(0, 1.0 - x / 0.20);
  cy = cy * (1.0 - leftBlend) + 0.38 * leftBlend;

  // Elevation envelope of the centerline
  cy -= 0.18 * Math.exp(-Math.pow((x - 0.28) / 0.09, 2)); // swell 1 centerline lift
  cy += 0.04 * Math.exp(-Math.pow((x - 0.40) / 0.06, 2)); // crossing dip
  cy -= 0.24 * Math.exp(-Math.pow((x - 0.60) / 0.11, 2)); // dominant grand peak lift
  cy -= 0.06 * Math.exp(-Math.pow((x - 0.74) / 0.08, 2)); // trailing lift

  // Base amplitude envelope (thickness of the vertical micro-mark field)
  let amp = 0.008; // baseline thinness
  amp += 0.135 * Math.exp(-Math.pow((x - 0.28) / 0.08, 2));
  amp += 0.045 * Math.exp(-Math.pow((x - 0.48) / 0.07, 2));
  amp += 0.185 * Math.exp(-Math.pow((x - 0.60) / 0.10, 2)); // grand peak amplitude
  amp += 0.075 * Math.exp(-Math.pow((x - 0.74) / 0.07, 2));

  // Convergence to center baseline as x approaches 0.85 - 0.96
  if (x > 0.80) {
    const fade = Math.max(0, 1.0 - (x - 0.80) / 0.12);
    amp *= fade;
    cy = cy * fade + 0.50 * (1.0 - fade);
  }

  // Left inception thinness
  if (x < 0.14) {
    const ramp = Math.max(0.005, (x / 0.14));
    amp = Math.min(amp, 0.008 + 0.03 * ramp);
  }

  // Chained traveling wave deformation:
  // Propagates left-to-right so neighboring sections rise and fall asynchronously
  const wave1 = Math.sin(2 * Math.PI * (x * 2.2 - t * 0.12));
  const wave2 = Math.cos(2 * Math.PI * (x * 3.8 - t * 0.16) + 0.5);
  const travelingMod = 1.0 + (wave1 * 0.16 + wave2 * 0.08);

  // Centerline vertical breathing (chained wave)
  const cyWave = Math.sin(2 * Math.PI * (x * 1.8 - t * 0.10) + 0.3) * 0.018;

  return {
    cy: cy + cyWave,
    amp: Math.max(0.002, amp * travelingMod),
  };
}

// Evaluate Model 02 base silhouette (centerline Y and local amplitude)
// Features from reference:
// - starts at x ~ 0 with cy = 0.64 (aligned with Model 02 dash)
// - early swell at x ~ 0.22 (cy ~ 0.60, amp ~ 0.065)
// - dips under Model 01 at x ~ 0.30 (cy ~ 0.68, amp ~ 0.035)
// - central swell at x ~ 0.44 crossing Model 01's valley (cy ~ 0.46, amp ~ 0.11)
// - dips under Model 01's grand peak at x ~ 0.60 (cy ~ 0.72, amp ~ 0.05)
// - broad secondary swell at x ~ 0.72 (cy ~ 0.58, amp ~ 0.08)
// - convergence into center baseline (cy = 0.50) at x > 0.84
function evalModel02(x: number, t: number) {
  let cy = 0.50;
  // Left baseline alignment with Model 02 label
  const leftBlend = Math.max(0, 1.0 - x / 0.20);
  cy = cy * (1.0 - leftBlend) + 0.64 * leftBlend;

  cy -= 0.06 * Math.exp(-Math.pow((x - 0.22) / 0.08, 2)); // early swell
  cy += 0.08 * Math.exp(-Math.pow((x - 0.30) / 0.06, 2)); // dip under peak 1
  cy -= 0.16 * Math.exp(-Math.pow((x - 0.44) / 0.09, 2)); // central crossing swell
  cy += 0.14 * Math.exp(-Math.pow((x - 0.60) / 0.08, 2)); // valley under grand peak
  cy -= 0.08 * Math.exp(-Math.pow((x - 0.72) / 0.09, 2)); // right swell

  let amp = 0.007;
  amp += 0.075 * Math.exp(-Math.pow((x - 0.22) / 0.07, 2));
  amp += 0.035 * Math.exp(-Math.pow((x - 0.30) / 0.05, 2));
  amp += 0.115 * Math.exp(-Math.pow((x - 0.44) / 0.08, 2));
  amp += 0.045 * Math.exp(-Math.pow((x - 0.58) / 0.06, 2));
  amp += 0.085 * Math.exp(-Math.pow((x - 0.72) / 0.08, 2));

  // Convergence to center baseline as x approaches 0.85 - 0.96
  if (x > 0.80) {
    const fade = Math.max(0, 1.0 - (x - 0.80) / 0.12);
    amp *= fade;
    cy = cy * fade + 0.50 * (1.0 - fade);
  }

  // Left inception thinness
  if (x < 0.14) {
    const ramp = Math.max(0.005, (x / 0.14));
    amp = Math.min(amp, 0.007 + 0.025 * ramp);
  }

  // Chained traveling wave deformation with independent speed, wavelength, and phase
  const wave1 = Math.sin(2 * Math.PI * (x * 2.6 - t * 0.15) + 1.9);
  const wave2 = Math.cos(2 * Math.PI * (x * 4.4 - t * 0.20) + 1.1);
  const travelingMod = 1.0 + (wave1 * 0.18 + wave2 * 0.09);

  // Centerline vertical breathing (independent phase)
  const cyWave = Math.sin(2 * Math.PI * (x * 2.0 - t * 0.13) + 1.6) * 0.02;

  return {
    cy: cy + cyWave,
    amp: Math.max(0.002, amp * travelingMod),
  };
}

export function VaaniFooterSignal() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    let width = 0;
    let height = 0;
    let dpr = 1;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      width = Math.max(1, rect.width);
      height = Math.max(1, rect.height);
      dpr = Math.min(window.devicePixelRatio || 1, 2.5);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(canvas);

    let rafId = 0;
    const startTime = performance.now();

    // Render single frame
    const render = (timeSec: number) => {
      ctx.clearRect(0, 0, width, height);

      // Micro-mark density: slice spacing ~3.4px matching reference raster
      const step = 3.4;
      const numSlices = Math.floor(width / step);

      // 1. Render Model 02 (Secondary Muted Teal Field)
      ctx.lineWidth = 1.1;
      ctx.lineCap = 'butt';
      ctx.setLineDash([2.2, 1.4]); // Stippled micro-dash structure

      for (let i = 0; i < numSlices; i += 1) {
        const xNorm = i / numSlices;
        if (xNorm < 0.01 || xNorm > 0.96) continue;

        const x = i * step;
        const { cy, amp } = evalModel02(xNorm, timeSec);

        const centerY = cy * height;
        const halfH = amp * height;

        // Density modulation: micro-striations within vertical mark
        const striation = 0.85 + 0.15 * Math.sin(i * 1.7);
        const effectiveH = Math.max(0.6, halfH * striation);

        // Alpha hierarchy: stronger at crests, airy at tails
        const alpha = Math.min(0.78, Math.max(0.20, amp * 4.0));
        ctx.strokeStyle = `rgba(104, 155, 149, ${alpha.toFixed(3)})`; // #689B95

        // Draw vertical micro-mark
        ctx.beginPath();
        ctx.moveTo(x, centerY - effectiveH);
        ctx.lineTo(x, centerY + effectiveH);
        ctx.stroke();

        // Delicate stipple dots beyond the tips for acoustic point-cloud feel
        if (effectiveH > 6) {
          ctx.fillStyle = `rgba(104, 155, 149, ${(alpha * 0.42).toFixed(3)})`;
          ctx.fillRect(x - 0.5, centerY - effectiveH - 2.0, 1, 1);
          ctx.fillRect(x - 0.5, centerY + effectiveH + 1.0, 1, 1);
        }
      }

      // 2. Render Model 01 (Primary Dark Charcoal Teal Field)
      ctx.lineWidth = 1.25;
      ctx.setLineDash([2.4, 1.3]);

      for (let i = 0; i < numSlices; i += 1) {
        const xNorm = i / numSlices;
        if (xNorm < 0.01 || xNorm > 0.96) continue;

        const x = i * step;
        const { cy, amp } = evalModel01(xNorm, timeSec);

        const centerY = cy * height;
        const halfH = amp * height;

        const striation = 0.86 + 0.14 * Math.cos(i * 1.5);
        const effectiveH = Math.max(0.6, halfH * striation);

        // Dark charcoal #17363A with crisp contrast
        const alpha = Math.min(0.92, Math.max(0.28, amp * 4.4));
        ctx.strokeStyle = `rgba(23, 54, 58, ${alpha.toFixed(3)})`; // #17363A

        ctx.beginPath();
        ctx.moveTo(x, centerY - effectiveH);
        ctx.lineTo(x, centerY + effectiveH);
        ctx.stroke();

        // Halftone stipple dots beyond the tips
        if (effectiveH > 6) {
          ctx.fillStyle = `rgba(23, 54, 58, ${(alpha * 0.50).toFixed(3)})`;
          ctx.fillRect(x - 0.5, centerY - effectiveH - 2.2, 1.1, 1.1);
          ctx.fillRect(x - 0.5, centerY + effectiveH + 1.2, 1.1, 1.1);
        }
      }

      // Reset dash for solid convergence line
      ctx.setLineDash([]);

      // 3. Convergence Line connecting to Agreement Marker (x > 0.92 to canvas edge)
      const convStart = width * 0.92;
      const convEnd = width;
      const convY = height * 0.50;

      ctx.beginPath();
      ctx.strokeStyle = 'rgba(104, 155, 149, 0.40)';
      ctx.lineWidth = 0.75;
      ctx.moveTo(convStart, convY);
      ctx.lineTo(convEnd, convY);
      ctx.stroke();
    };

    if (reducedMotion.matches) {
      render(0);
      return () => {
        observer.disconnect();
      };
    }

    const loop = (now: number) => {
      if (!document.hidden) {
        const elapsedSec = (now - startTime) / 1000;
        render(elapsedSec);
      }
      rafId = requestAnimationFrame(loop);
    };

    rafId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(rafId);
      observer.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{ width: '100%', height: '100%', display: 'block' }}
    />
  );
}
