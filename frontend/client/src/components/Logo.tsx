import React from 'react';

/**
 * Logo Component
 * Design: Shield + waveform mark aligned to dark premium UI.
 */
export default function Logo() {
  return (
    <div className="flex items-center gap-3 flex-shrink-0">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-600/90 shadow-md shadow-violet-600/20 ring-1 ring-white/10">
        <svg
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Shield */}
          <path
            d="M12 3.5L6.5 5.6V11.4C6.5 14.6 8.7 17.5 12 18.5C15.3 17.5 17.5 14.6 17.5 11.4V5.6L12 3.5Z"
            stroke="rgba(255,255,255,0.92)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Waveform inside shield */}
          <path
            d="M8.5 12.25C9 11.7 9.5 11.3 10 11.3C10.8 11.3 11.2 12.7 12 12.7C12.8 12.7 13.2 11.3 14 11.3C14.5 11.3 15 11.6 15.5 12.05"
            stroke="#2DD4BF"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <div className="hidden sm:flex flex-col leading-tight">
        <span className="text-sm font-semibold tracking-tight text-white/90">
          VAANI
        </span>
        <span className="text-[11px] font-medium text-gray-400">
          Voice Authenticity Platform
        </span>
      </div>
    </div>
  );
}
