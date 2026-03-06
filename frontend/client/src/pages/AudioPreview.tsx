import React, { useState } from 'react';
import { useLocation } from 'wouter';
import { motion } from 'framer-motion';
import Header from '@/components/Header';
import { useAudio } from '@/contexts/AudioContext';

/**
 * Audio Preview Page
 * Design: Display uploaded audio file with waveform visualization and browser audio controls
 * Features: Native audio player with controls, analyze button
 * Waveform accent: Teal color
 */
export default function AudioPreview() {
  const [, setLocation] = useLocation();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const { audioFile, audioPreviewUrl } = useAudio();

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault(); // Prevent form submission/page reload
    setIsAnalyzing(true);
    try {
      // Navigate to analysis page - audio file is already in global state
      setLocation('/analysis');
    } catch (error) {
      console.error('Error during analysis:', error);
      setIsAnalyzing(false);
    }
  };

  if (!audioFile || !audioPreviewUrl) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header showAnalyzeButton={false} />

      <section className="pt-32 pb-16 px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-2xl mx-auto"
        >
          {/* File Info */}
          <div className="mb-8 text-center">
            <h1 className="text-2xl md:text-3xl font-semibold text-white mb-2">
              Audio Preview
            </h1>
            <p className="text-gray-400 text-xs truncate font-light">{audioFile.name}</p>
          </div>

          {/* Glass Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="glass-card p-8"
          >
            {/* Waveform Visualization (Placeholder) */}
            <div className="mb-8 h-24 bg-white/5 rounded-lg flex items-center justify-center border border-white/10">
              <svg
                className="w-full h-full"
                viewBox="0 0 400 100"
                preserveAspectRatio="none"
              >
                {Array.from({ length: 100 }).map((_, i) => {
                  const height = Math.random() * 80 + 10;
                  return (
                    <rect
                      key={i}
                      x={i * 4}
                      y={50 - height / 2}
                      width="3"
                      height={height}
                      fill="#2DD4BF"
                      opacity="0.6"
                    />
                  );
                })}
              </svg>
            </div>

            {/* Audio Player */}
            <div className="mb-8">
              <audio
                src={audioPreviewUrl}
                controls
                className="w-full h-16 bg-white/10 rounded-lg"
              />
            </div>

            {/* Analyze Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              type="button"
              className="w-full py-3 rounded-full bg-teal-500 hover:bg-teal-600 disabled:opacity-50 text-white font-medium text-sm transition-colors"
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze Voice'}
            </motion.button>
          </motion.div>
        </motion.div>
      </section>
    </div>
  );
}
