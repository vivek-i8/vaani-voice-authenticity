import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, RefreshCcw } from 'lucide-react';
import { useLocation } from 'wouter';
import { useAudio } from '@/contexts/AudioContext';

/**
 * AnalysisErrorState — V2
 * Structured error display for network failures, backend errors, and invalid input.
 * Uses the existing design system (glass-card, teal accent).
 * No alert() — errors shown inline.
 */
interface AnalysisErrorStateProps {
  message: string;
  statusCode?: number;
  onRetry?: () => void;
}

export default function AnalysisErrorState({
  message,
  statusCode,
  onRetry,
}: AnalysisErrorStateProps) {
  const [, setLocation] = useLocation();
  const { clearAudio } = useAudio();

  const handleGoBack = () => {
    clearAudio();
    setLocation('/');
  };

  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    } else {
      window.location.reload();
    }
  };

  // Parse user-friendly error message
  const getErrorTitle = () => {
    if (statusCode === 413) return 'File Too Large';
    if (statusCode === 422) return 'Invalid Audio File';
    if (statusCode === 503) return 'Service Temporarily Unavailable';
    if (statusCode && statusCode >= 500) return 'Server Error';
    if (message.includes('Failed to fetch') || message.includes('NetworkError'))
      return 'Network Error';
    return 'Analysis Error';
  };

  const getErrorDescription = () => {
    if (statusCode === 413) {
      return 'The uploaded file exceeds the maximum size limit. Please upload a file smaller than 50MB.';
    }
    if (statusCode === 422) {
      return 'The uploaded file could not be processed. Please ensure the file is a valid audio format (WAV, MP3, M4A, or FLAC) with a duration between 3 and 5 seconds.';
    }
    if (statusCode === 503) {
      return 'The analysis service is temporarily unavailable. The backend may be starting up or under maintenance. Please try again in a moment.';
    }
    if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
      return 'Could not connect to the analysis server. Please check your network connection and ensure the backend is running.';
    }
    return message || 'An unexpected error occurred during analysis.';
  };

  return (
    <div className="max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="glass-card p-8 md:p-10 text-center"
      >
        <motion.div
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="mb-6"
        >
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto" />
        </motion.div>

        <h2 className="text-xl font-semibold text-white mb-3">
          {getErrorTitle()}
        </h2>

        <p className="text-gray-400 text-sm mb-8 leading-relaxed max-w-md mx-auto font-light">
          {getErrorDescription()}
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleRetry}
            className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-full bg-teal-500 text-slate-950 hover:bg-teal-400 transition text-sm font-medium"
          >
            <RefreshCcw className="w-4 h-4" />
            Try Again
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleGoBack}
            className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-full border border-white/20 bg-white/5 text-white hover:bg-white/10 transition text-sm font-medium"
          >
            Upload Different File
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}
