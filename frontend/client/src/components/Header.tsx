import React, { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'wouter';
import Logo from './Logo';

/**
 * Header Component
 * Design: Fixed header with 80px height
 * Left: Logo icon only
 * Right: Status badges + Analyze Voice button
 * The button scrolls to upload section on landing page
 */
interface HeaderProps {
  onAnalyzeClick?: () => void;
  showAnalyzeButton?: boolean;
}

export default function Header({ onAnalyzeClick, showAnalyzeButton = true }: HeaderProps) {
  const [location] = useLocation();
  const [health, setHealth] = useState<{ status: string; device: string } | null>(null);
  const [healthError, setHealthError] = useState(false);

  const healthUrl = useMemo(() => {
    // We already call /api from the frontend; health lives at /api/v1/health.
    // Default local backend: http://127.0.0.1:8000
    const apiBase = (import.meta as any).env.VITE_API_BASE_URL;
    return `${apiBase}/api/v1/health`;
  }, []);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      try {
        setHealthError(false);
        const res = await fetch(healthUrl, { method: 'GET' });
        if (!res.ok) throw new Error(`health ${res.status}`);
        const json = (await res.json()) as { status: string; device: string };
        if (!cancelled) setHealth(json);
      } catch {
        if (!cancelled) {
          setHealthError(true);
          setHealth(null);
        }
      }
    };

    run();
    const id = window.setInterval(run, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [healthUrl]);

  const handleAnalyzeClick = () => {
    if (location === '/') {
      // Scroll to upload section
      const uploadSection = document.getElementById('upload-section');
      if (uploadSection) {
        uploadSection.scrollIntoView({ behavior: 'smooth' });
      }
    }
    onAnalyzeClick?.();
  };

  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId);
    if (section) {
      section.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 h-20 bg-background/80 backdrop-blur-md border-b border-white/10 z-50">
      <div className="h-full flex items-center justify-between px-4 md:px-8 max-w-7xl mx-auto">
        {/* Left: Logo */}
        <Logo />

        {/* Right: Status badges */}
        <div className="flex items-center gap-2">
          <div
            className={[
              'inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium border',
              healthError
                ? 'bg-rose-500/10 border-rose-400/30 text-rose-200'
                : health?.status === 'ok'
                ? 'bg-teal-500/10 border-teal-400/30 text-teal-200'
                : 'bg-amber-500/10 border-amber-400/30 text-amber-200',
            ].join(' ')}
            title={healthError ? 'Backend unreachable' : `Backend status: ${health?.status ?? 'unknown'}`}
          >
            <span
              className={[
                'h-2 w-2 rounded-full',
                healthError
                  ? 'bg-rose-400'
                  : health?.status === 'ok'
                  ? 'bg-teal-400'
                  : 'bg-amber-400',
              ].join(' ')}
            />
            <span>{healthError ? 'Backend offline' : health?.status === 'ok' ? 'Backend healthy' : 'Backend starting'}</span>
          </div>

          <div className="hidden sm:inline-flex items-center rounded-full px-3 py-1 text-xs font-medium bg-white/5 border border-white/10 text-gray-200">
            {health?.device ? `Device: ${health.device.toUpperCase()}` : 'Device: —'}
          </div>
        </div>
      </div>
    </header>
  );
}
