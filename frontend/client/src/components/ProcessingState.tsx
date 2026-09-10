import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

/**
 * Processing State — V2
 * Three-stage processing display per Section 13:
 * 1. Running acoustic-fusion signal
 * 2. Running anti-spoofing ensemble
 * 3. Retrieving comparable evidence
 */
export default function ProcessingState() {
  const stages = [
    { label: 'Running acoustic-fusion signal', detail: 'Wav2Vec2 embeddings + acoustic features' },
    { label: 'Running anti-spoofing ensemble', detail: 'Spectra-AASIST3 second opinion' },
    { label: 'Retrieving comparable evidence', detail: 'Nearest-neighbor reference lookup' },
  ];

  const [currentStage, setCurrentStage] = useState(0);
  const [completedStages, setCompletedStages] = useState<number[]>([]);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const totalDuration = 6000; // 6 seconds total
    const stageDuration = totalDuration / stages.length;

    stages.forEach((_, index) => {
      setTimeout(() => {
        setCurrentStage(index);
        setProgress(((index + 1) / stages.length) * 100);
      }, index * stageDuration);

      setTimeout(() => {
        setCompletedStages((prev) => [...prev, index]);
      }, index * stageDuration + stageDuration * 0.8);
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
          <span className="text-gray-400 text-sm ml-4 font-light">
            VAANI Analysis Pipeline
          </span>
        </div>

        {/* Stages */}
        <div className="space-y-4 mb-8 min-h-40">
          {stages.map((stage, index) => {
            const isCompleted = completedStages.includes(index);
            const isCurrent = currentStage === index && !isCompleted;
            const isPending = index > currentStage;

            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: index * 0.15 }}
                className={`flex items-start gap-3 p-3 rounded-lg transition-colors duration-300 ${
                  isCurrent
                    ? 'bg-teal-500/10 border border-teal-500/20'
                    : isCompleted
                      ? 'bg-white/[0.02]'
                      : 'opacity-50'
                }`}
              >
                {/* Status indicator */}
                <div className="mt-1 flex-shrink-0">
                  {isCompleted ? (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="w-2 h-2 rounded-full bg-teal-400"
                    />
                  ) : isCurrent ? (
                    <motion.div
                      animate={{ opacity: [1, 0.4, 1] }}
                      transition={{ duration: 1.2, repeat: Infinity }}
                      className="w-2 h-2 rounded-full bg-teal-400"
                    />
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-white/20" />
                  )}
                </div>

                <div className="flex-1">
                  <p
                    className={`text-sm font-medium ${
                      isCompleted
                        ? 'text-gray-300'
                        : isCurrent
                          ? 'text-teal-300'
                          : 'text-gray-500'
                    }`}
                  >
                    {stage.label}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5 font-light">
                    {stage.detail}
                  </p>
                </div>

                {isCompleted && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-xs text-teal-400"
                  >
                    ✓
                  </motion.span>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-gray-400 font-light">
            <span>Pipeline Progress</span>
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
