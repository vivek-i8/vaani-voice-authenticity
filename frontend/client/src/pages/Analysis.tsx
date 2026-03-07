import React, { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import { motion } from 'framer-motion';
import Header from '@/components/Header';
import ProcessingState from '@/components/ProcessingState';
import ResultsState from '@/components/ResultsState';
import { analyzeAudio, type AnalysisResponse } from '@/lib/api';
import { useAudio } from '@/contexts/AudioContext';

/**
 * Analysis Page
 * Design: Two states - Processing and Results
 * Processing: Terminal-style logs with typing animation and progress bar
 * Results: Bento grid with confidence gauge, pitch chart, signal certainty, and assessment
 */
export default function Analysis() {
  const [, setLocation] = useLocation();
  const [state, setState] = useState<'processing' | 'complete' | 'error'>('processing');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | undefined>(undefined);
  const { audioFile } = useAudio();

  useEffect(() => {
    // Check if audio file is available
    if (!audioFile) {
      setLocation('/');
      return;
    }

    // Real API call to /api/analyze
    const performAnalysis = async () => {
      try {
        // Direct API call with hardcoded HTTPS URL
        const formData = new FormData();
        formData.append('file', audioFile);

        const response = await fetch('https://vaani-13-233-132-63.duckdns.org/api/analyze', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Analysis failed: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        setAnalysisResult(result);
        setState('complete');
      } catch (error) {
        console.error('Analysis failed:', error);
        setState('error');
      }
    };

    performAnalysis();
  }, [audioFile, setLocation]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header showAnalyzeButton={false} />

      <section className="pt-32 pb-16 px-4">
        {state === 'processing' ? (
          <ProcessingState />
        ) : state === 'error' ? (
          <div className="text-center py-8">
            <p className="text-red-500">Analysis failed. Please try again.</p>
            <button 
              onClick={() => setState('processing')}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Try Again
            </button>
          </div>
        ) : (
          <ResultsState result={analysisResult} />
        )}
      </section>
    </div>
  );
}
