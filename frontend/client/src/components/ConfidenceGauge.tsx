import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

/**
 * Confidence Gauge Component
 * Design: Radial gauge chart with animated fill
 * Color: Teal for Human, Rose for AI
 * Displays confidence percentage and classification label
 */
interface ConfidenceGaugeProps {
  confidence: number;
  label: 'Human' | 'AI' | 'Inconclusive';
}

export default function ConfidenceGauge({ confidence, label }: ConfidenceGaugeProps) {
  const [animatedConfidence, setAnimatedConfidence] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setAnimatedConfidence((prev) => {
        if (prev >= confidence * 100) {
          clearInterval(interval);
          return confidence * 100;
        }
        return prev + (confidence * 100) / 50;
      });
    }, 30);

    return () => clearInterval(interval);
  }, [confidence]);

  const color = label === 'Human' ? '#2DD4BF' : label === 'Inconclusive' ? '#F59E0B' : '#FB7185';
  const data = [
    { name: 'confidence', value: animatedConfidence },
    { name: 'remaining', value: 100 - animatedConfidence },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6 }}
      className="glass-card p-8 md:p-10 text-center h-full"
    >
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-gray-400 text-sm font-medium">Primary Verdict</h3>
        <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-xs font-medium text-gray-200">
          Voice Integrity
        </span>
      </div>

      <div className="mx-auto mb-6 h-64 w-full max-w-sm">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={84}
              outerRadius={120}
              startAngle={180}
              endAngle={0}
              dataKey="value"
            >
              <Cell fill={color} />
              <Cell fill="rgba(255, 255, 255, 0.1)" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <p className="text-5xl font-semibold text-white mb-2">
          {Math.round(animatedConfidence)}%
        </p>
        <p className="text-gray-400 text-sm mb-3 font-light">Model Confidence</p>
        <p className="text-teal-300 font-semibold text-lg">{label}</p>
      </motion.div>
    </motion.div>
  );
}
