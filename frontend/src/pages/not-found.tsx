import { useEffect } from 'react';
import { useLocation } from 'wouter';
import { BrandHeader } from '@/components/VaaniChrome';
import { VaaniFooterSignal } from '@/components/VaaniFooterSignal';

export default function NotFound() {
  const [, setLocation] = useLocation();

  // Ensure genuine missing routes signal noindex to crawlers that execute JavaScript
  useEffect(() => {
    let meta = document.querySelector('meta[name="robots"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute('name', 'robots');
      document.head.appendChild(meta);
    }
    const previous = meta.getAttribute('content') ?? 'index, follow';
    meta.setAttribute('content', 'noindex, nofollow');
    return () => {
      meta?.setAttribute('content', previous);
    };
  }, []);

  return (
    <main className="vaani-app not-found-layout enter" data-testid="page-not-found">
      <BrandHeader />
      <div className="not-found-stage">
        <section className="not-found-panel corner-frame" aria-labelledby="not-found-title">
          <span className="not-found-code">404 · ERROR</span>
          <h1 id="not-found-title" className="not-found-title">SIGNAL NOT FOUND</h1>
          <p className="not-found-description">
            The requested address does not correspond to an active instrument route or the analysis session has expired.
          </p>
          <div className="not-found-actions">
            <button
              type="button"
              className="not-found-button"
              onClick={() => setLocation('/')}
              data-testid="button-not-found-home"
            >
              ←&nbsp; Return to audio input
            </button>
          </div>
        </section>
      </div>

      <footer className="acoustic-footer" aria-label="Acoustic analysis visual">
        <div className="footer-signal-stage">
          <VaaniFooterSignal />
        </div>
        <div className="footer-signature">
          <span>HUMAN SPEECH MATTERS</span>
          <span className="signature-dash" aria-hidden="true">—</span>
        </div>
      </footer>
    </main>
  );
}
