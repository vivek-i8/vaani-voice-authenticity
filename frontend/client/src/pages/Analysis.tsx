import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'wouter';
import Header from '@/components/Header';
import ProcessingState from '@/components/ProcessingState';
import ResultsState from '@/components/ResultsState';
import AnalysisErrorState from '@/components/AnalysisErrorState';
import { analyzeAudio, type AnalysisResponse } from '@/lib/api';
import { useAudio } from '@/contexts/AudioContext';

/**
 * Analysis Page — V2
 * Three states: processing, complete, error
 * Uses AnalysisErrorState for structured error display
 */
export default function Analysis() {
  const [, setLocation] = useLocation();
  const [state, setState] = useState<'processing' | 'complete' | 'error'>(
    'processing',
  );
  const [analysisResult, setAnalysisResult] = useState<
    AnalysisResponse | undefined
  >(undefined);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [errorStatusCode, setErrorStatusCode] = useState<number | undefined>(
    undefined,
  );
  const { audioFile } = useAudio();

  const performAnalysis = useCallback(async () => {
    if (!audioFile) {
      setState('error');
      setErrorMessage('No audio file selected. Please upload a file first.');
      return;
    }

    setState('processing');
    setErrorMessage('');
    setErrorStatusCode(undefined);

    try {
      const result = await analyzeAudio(audioFile);
      setAnalysisResult(result);
      setState('complete');
    } catch (error) {
      console.error('Analysis failed:', error);
      const msg = error instanceof Error ? error.message : 'Analysis failed';
      setErrorMessage(msg);

      // Try to extract status code from error message
      const statusMatch = msg.match(/\((\d+)\)/);
      if (statusMatch) {
        setErrorStatusCode(parseInt(statusMatch[1], 10));
      }

      setState('error');
    }
  }, [audioFile]);

  useEffect(() => {
    performAnalysis();
  }, [performAnalysis]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header showAnalyzeButton={false} />

      {state === 'processing' && <ProcessingState />}

      {state === 'error' && (
        <section className="pt-32 pb-16 px-4">
          <AnalysisErrorState
            message={errorMessage}
            statusCode={errorStatusCode}
            onRetry={performAnalysis}
          />
        </section>
      )}

      {state === 'complete' && analysisResult && (
        <section className="pt-32 pb-16 px-4">
          <ResultsState result={analysisResult} />
        </section>
      )}
    </div>
  );
}
