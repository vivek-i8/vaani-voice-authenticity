import React from 'react';
import { motion } from 'framer-motion';
import { useLocation } from 'wouter';
import { Button } from '@/components/ui/button';
import ConfidenceGauge from './ConfidenceGauge';
import PitchStabilityChart from './PitchStabilityChart';
import SignalCertainty from './SignalCertainty';
import DetailedAssessment from './DetailedAssessment';
import { useAudio } from '@/contexts/AudioContext';

/**
 * Results State Component
 * Design: Bento Grid layout with animated staggered appearance
 * Grid: Two columns
 * Left: Confidence Gauge, Signal Certainty
 * Right: Pitch Stability Chart, Detailed Assessment
 */
interface ResultsStateProps {
  result?: {
    label: 'Human' | 'AI' | 'Inconclusive';
    confidence: number;
    entropy: number;
    signals: {
      pitch_variance: number;
      spectral_drift: number;
      zcr_variance: number;
    };
    explanation: string;
  };
}

export default function ResultsState({ result }: ResultsStateProps) {
  const [, setLocation] = useLocation();
  const { clearAudio } = useAudio();

  if (!result) {
    return (
      <div className="max-w-6xl mx-auto text-center text-gray-400">
        Loading results...
      </div>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2,
      },
    },
  };

  const handleAnalyzeAnother = () => {
    // Clear global audio state
    clearAudio();
    
    // Navigate back to landing page
    setLocation('/');
  };

  const downloadReport = () => {
    if (!result) return;
    
    // Create report data
    const reportData = {
      label: result.label,
      confidence: result.confidence,
      entropy: result.entropy,
      signals: {
        pitch_variance: result.signals.pitch_variance,
        spectral_drift: result.signals.spectral_drift,
        zcr_variance: result.signals.zcr_variance
      }
    };
    
    // Convert to JSON string
    const dataStr = JSON.stringify(reportData, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    
    // Create download link
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "vaani_analysis_report.json";
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-6xl mx-auto"
    >
      {/* Results Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-10"
      >
        <h1 className="text-3xl md:text-4xl font-semibold text-white mb-4">
          Analysis Complete
        </h1>
        <p className="text-gray-400 text-sm md:text-base font-light">
          Here are the detailed findings from your voice authenticity analysis.
        </p>
      </motion.div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 md:gap-8">
        {/* Slot A: Verdict / Confidence (dominant) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="xl:col-span-7"
        >
          <ConfidenceGauge
            confidence={result.confidence}
            label={result.label}
          />
        </motion.div>

        {/* Slot B: Pitch Chart */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="xl:col-span-5"
        >
          <PitchStabilityChart signals={result.signals} />
        </motion.div>

        {/* Slot C: Signal Certainty */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="xl:col-span-4"
        >
          <SignalCertainty entropy={result.entropy} />
        </motion.div>

        {/* Slot D: Detailed Assessment */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.25 }}
          className="xl:col-span-8"
        >
          <DetailedAssessment
            explanation={result.explanation || {
              summary: result.label === 'AI' ? 'AI-generated voice patterns detected.' : 
                      result.label === 'Human' ? 'Natural human voice patterns detected.' : 
                      'Analysis inconclusive due to insufficient audio quality.',
              technical_analysis: result.label === 'AI' ? 'The system detected characteristics consistent with synthetic voice generation.' :
                       result.label === 'Human' ? 'The system detected natural speech patterns typical of human voices.' :
                       'Audio quality prevents definitive analysis.',
              recommendation: result.label === 'AI' ? 'Verify the caller\'s identity through another channel.' :
                              result.label === 'Human' ? 'No additional action needed.' :
                              'Please provide a clearer audio sample.'
            }}
            explanation_source={result.explanation_source || 'fallback'}
            label={result.label}
          />
        </motion.div>
      </div>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        className="flex flex-col md:flex-row gap-4 justify-center mt-12"
      >
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Button
            onClick={handleAnalyzeAnother}
            size="lg"
            className="rounded-full px-8 bg-teal-500 text-slate-950 hover:bg-teal-400"
          >
            Analyze Another File
          </Button>
        </motion.div>
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Button
            onClick={downloadReport}
            size="lg"
            variant="outline"
            className="rounded-full px-8 border-white/20 bg-white/5 text-white hover:bg-white/10"
          >
            Download Report
          </Button>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
