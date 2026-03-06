import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

/**
 * Processing State Component
 * Design: Terminal-style glass card with animated log lines
 * Logs appear every 400ms with typing animation
 * Progress bar fills as logs appear
 */
export default function ProcessingState() {
  const logs = [
    'Initializing VAANI neural core',
    'Loading acoustic models',
    'Extracting wav2vec embeddings',
    'Computing pitch variance',
    'Computing spectral drift',
    'Computing zero crossing rate',
    'Running classification model',
    'Evaluating entropy threshold',
    'Generating authenticity verdict',
  ];

  const [displayedLogs, setDisplayedLogs] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    logs.forEach((log, index) => {
      setTimeout(() => {
        setDisplayedLogs((prev) => [...prev, log]);
        setProgress(((index + 1) / logs.length) * 100);
      }, index * 400);
    });
  }, []);

  return (
    <div className="max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="glass-card p-8 md:p-10"
      >
        {/* Terminal Header */}
        <div className="flex items-center gap-2 mb-6 pb-4 border-b border-white/10">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-gray-400 text-sm ml-4 font-light">VAANI Analysis Terminal</span>
        </div>

        {/* Logs */}
        <div className="font-mono text-sm space-y-2 mb-8 min-h-32">
          {displayedLogs.map((log, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className="flex items-center gap-2"
            >
              <span className="text-teal-400">$</span>
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="text-gray-300"
              >
                {log}
              </motion.span>
            </motion.div>
          ))}
          {displayedLogs.length < logs.length && (
            <motion.div
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="flex items-center gap-2"
            >
              <span className="text-teal-400">$</span>
              <span className="text-gray-500 italic">Processing...</span>
            </motion.div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-gray-400 font-light">
            <span>Analysis Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <motion.div className="h-1 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: '0%' }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
              className="h-full bg-gradient-to-r from-teal-400 to-teal-500"
            />
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
