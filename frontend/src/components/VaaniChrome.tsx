import { type ReactNode } from 'react';

export function VaaniLogoIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 130 110"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Left stroke of V (Primary Deep Charcoal Teal) */}
      <polygon points="1,12 18,12 74,106 57,106" fill="#0E383B" />
      {/* Right stroke of V (Secondary Sage Teal) */}
      <polygon points="57,106 74,106 101,60 84,60" fill="#689B95" />
      {/* Waveform Bar 1 (Deep Teal) */}
      <rect x="67.8" y="15.5" width="5.4" height="31" rx="2.7" fill="#0E383B" />
      {/* Waveform Bar 2 (Deep Teal, Tallest Peak) */}
      <rect x="81.3" y="0" width="5.4" height="60" rx="2.7" fill="#0E383B" />
      {/* Waveform Bar 3 (Sage Teal) */}
      <rect x="94.3" y="9" width="5.4" height="42" rx="2.7" fill="#689B95" />
      {/* Waveform Bar 4 (Deep Teal) */}
      <rect x="107.3" y="15.5" width="5.4" height="31" rx="2.7" fill="#0E383B" />
      {/* Waveform Bar 5 (Sage Teal) */}
      <rect x="120.3" y="23.5" width="5.4" height="13" rx="2.7" fill="#689B95" />
    </svg>
  );
}

export function BrandHeader({ action }: { action?: ReactNode }) {
  return (
    <header className="site-header">
      <div className="brand-lockup">
        <VaaniLogoIcon className="brand-logo-icon" />
        <span className="brand-divider" aria-hidden="true" />
        <div className="brand" data-testid="text-brand">VAANI</div>
        <div className="brand-context">VOICE AUTHENTICITY<br />ANALYSIS</div>
      </div>
      <div className="header-meta">
        <div className="version">v2.0</div>
        <div className="privacy">Private<br />Local processing<br />Your audio stays yours</div>
        <span className="status-dot" aria-label="System ready" />
        {action}
      </div>
    </header>
  );
}

export function FileIdentity({ name, size, type, duration }: { name: string; size: string; type: string; duration?: number }) {
  return (
    <div className="file-identity" data-testid="file-identity">
      <span className="file-glyph" aria-hidden="true" />
      <div className="file-meta">
        <strong data-testid="text-file-name">{name}</strong>
        <span data-testid="text-file-meta">{size} · {duration ? `${duration.toFixed(1)} seconds` : '3–5 seconds'} · {type || 'audio'}</span>
      </div>
    </div>
  );
}