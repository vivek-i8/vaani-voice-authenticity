import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

/**
 * Signal Certainty Component
 * Design: Display entropy metric and two progress bars
 * Bars: Linguistic Coherence, Artifact Presence
 * Values normalized to 0-100%
 */
interface SignalCertaintyProps {
  entropy?: number;
}

export default function SignalCertainty({ entropy = 0.32 }: SignalCertaintyProps) {
  const [linguisticCoherence, setLinguisticCoherence] = useState(0);
  const [artifactPresence, setArtifactPresence] = useState(0);

  // Normalize entropy to percentage (0-1 to 0-100)
  const signalCertaintyPercent = Math.round((1 - entropy) * 100);

  useEffect(() => {
    // Animate linguistic coherence (higher is better)
    const interval1 = setInterval(() => {
      setLinguisticCoherence((prev) => {
        const target = signalCertaintyPercent;
        if (prev >= target) {
          clearInterval(interval1);
          return target;
        }
        return prev + target / 50;
      });
    }, 30);

    // Animate artifact presence (lower is better, so we show inverse)
    const interval2 = setInterval(() => {
      setArtifactPresence((prev) => {
        const target = Math.round(entropy * 100);
        if (prev >= target) {
          clearInterval(interval2);
          return target;
        }
        return prev + target / 50;
      });
    }, 30);

    return () => {
      clearInterval(interval1);
      clearInterval(interval2);
    };
  }, [entropy, signalCertaintyPercent]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="glass-card p-8 md:p-9 h-full"
    >
      <h3 className="text-gray-400 text-sm font-medium mb-6">Signal Certainty</h3>

      <div className="space-y-6">
        {/* Signal Certainty Percentage */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center mb-6"
        >
          <p className="text-3xl font-semibold text-teal-400 mb-2">
            {Math.round(signalCertaintyPercent)}%
          </p>
          <p className="text-gray-400 text-xs font-light">Overall Signal Quality</p>
        </motion.div>

        {/* Linguistic Coherence */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-300 text-xs font-light">Linguistic Coherence</span>
            <span className="text-teal-400 font-medium text-xs">
              {Math.round(linguisticCoherence)}%
            </span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: '0%' }}
              animate={{ width: `${linguisticCoherence}%` }}
              transition={{ duration: 0.6 }}
              className="h-full bg-gradient-to-r from-teal-400 to-teal-500"
            />
          </div>
        </div>

        {/* Artifact Presence */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-300 text-xs font-light">Artifact Presence</span>
            <span className="text-rose-400 font-medium text-xs">
              {Math.round(artifactPresence)}%
            </span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: '0%' }}
              animate={{ width: `${artifactPresence}%` }}
              transition={{ duration: 0.6 }}
              className="h-full bg-gradient-to-r from-rose-400 to-rose-500"
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
