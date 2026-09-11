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
      // Instead of redirecting, show a proper message
      setState('error');
      return;
    }

    // Real API call to /api/analyze via the shared API client
    const performAnalysis = async () => {
      try {
        const result = await analyzeAudio(audioFile);
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
            <p className="text-red-500 mb-4">No audio file found for analysis.</p>
            <p className="text-gray-400 mb-6">Please upload an audio file from the home page to start analysis.</p>
            <button 
              onClick={() => setLocation('/')}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Go to Home Page
            </button>
          </div>
        ) : (
          <ResultsState result={analysisResult} />
        )}
      </section>
    </div>
  );
}
