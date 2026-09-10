import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { Info, CheckCircle2, AlertCircle } from 'lucide-react';
import type { AnalysisResponse } from '@/lib/api';

/**
 * VerdictPanel — V2 Tab
 * Shows: verdict label, animated confidence gauge, confidence caveat, entropy note.
 * Inconclusive states name both trigger conditions per Section 8.
 */
interface VerdictPanelProps {
  result: AnalysisResponse;
}

export default function VerdictPanel({ result }: VerdictPanelProps) {
  const { verdict, confidence, confidence_note, entropy, ensemble, degraded, explanation } = result;
  const [animatedConfidence, setAnimatedConfidence] = useState(0);

  useEffect(() => {
    const target = confidence * 100;
    const interval = setInterval(() => {
      setAnimatedConfidence((prev) => {
        if (prev >= target) {
          clearInterval(interval);
          return target;
        }
        return prev + target / 50;
      });
    }, 30);
    return () => clearInterval(interval);
  }, [confidence]);

  const color =
    verdict === 'Human'
      ? '#2DD4BF'
      : verdict === 'Inconclusive'
        ? '#F59E0B'
        : '#FB7185';

  const labelColor =
    verdict === 'Human'
      ? 'text-teal-300'
      : verdict === 'Inconclusive'
        ? 'text-amber-300'
        : 'text-rose-300';

  const Icon =
    verdict === 'Human'
      ? CheckCircle2
      : verdict === 'Inconclusive'
        ? Info
        : AlertCircle;

  const data = [
    { name: 'confidence', value: animatedConfidence },
    { name: 'remaining', value: 100 - animatedConfidence },
  ];

  // Determine Inconclusive trigger conditions
  const isInconclusive = verdict === 'Inconclusive';
  const triggers: string[] = [];
  if (isInconclusive) {
    if (ensemble.agreement === 'disagree') {
      triggers.push('Signal disagreement');
    }
    if (entropy >= 0.7) {
      triggers.push('High entropy');
    }
    // Check if either signal is in ambiguous band
    if (
      ensemble.vaani_signal.score > 0.4 &&
      ensemble.vaani_signal.score < 0.6
    ) {
      triggers.push('VAANI signal in ambiguous band');
    }
    if (
      ensemble.spectra_signal.available &&
      ensemble.spectra_signal.score > 0.4 &&
      ensemble.spectra_signal.score < 0.6
    ) {
      triggers.push('Spectra signal in ambiguous band');
    }
  }

  return (
    <div className="space-y-6">
      {/* Main Verdict Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card p-8 md:p-10 text-center"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-gray-400 text-sm font-medium">Primary Verdict</h3>
          {degraded && (
            <span className="inline-flex items-center rounded-full border border-amber-400/30 bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-300">
              Degraded Mode
            </span>
          )}
        </div>

        {/* Confidence Gauge */}
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
                <Cell key="confidence" fill={color} />
                <Cell key="remaining" fill="rgba(255, 255, 255, 0.1)" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Confidence Number */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <p className="text-5xl font-semibold text-white mb-2">
            {Math.round(animatedConfidence)}%
          </p>
          <p className="text-gray-400 text-sm mb-1 font-light">
            Model-reported confidence
          </p>
          <p className={`font-semibold text-lg ${labelColor}`}>{verdict}</p>
        </motion.div>
      </motion.div>

      {/* Confidence Caveat */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-card p-6"
      >
        <div className="flex items-start gap-3">
          <Info className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-gray-300 text-sm leading-relaxed">
              {confidence_note ||
                'This confidence score is model-reported confidence, not a validated probability of correctness. It reflects how strongly the model\'s internal signals align, not how likely the label is to be correct.'}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Inconclusive Trigger Conditions */}
      {isInconclusive && triggers.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card p-6 border-amber-500/20"
        >
          <h4 className="text-amber-400 text-xs font-medium uppercase tracking-wider mb-3">
            Why Inconclusive
          </h4>
          <ul className="space-y-2">
            {triggers.map((trigger, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                {trigger}
              </li>
            ))}
          </ul>
        </motion.div>
      )}

      {/* Deterministic Explanation (from backend explanation engine — no LLM) */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.55 }}
        className="glass-card p-6"
      >
        <h4 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-3">
          Explanation
        </h4>
        {explanation?.summary && (
          <p className="text-gray-200 text-sm font-medium leading-relaxed mb-3">
            {explanation.summary}
          </p>
        )}
        {explanation?.technical_analysis && (
          <p className="text-gray-400 text-xs font-light leading-relaxed mb-3">
            {explanation.technical_analysis}
          </p>
        )}
        {explanation?.recommendation && (
          <p className="text-gray-400 text-xs font-light leading-relaxed">
            {explanation.recommendation}
          </p>
        )}
      </motion.div>

      {/* Entropy Note */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="glass-card p-6"
      >
        <h4 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-2">
          Entropy
        </h4>
        <p className="text-2xl font-semibold text-teal-400 mb-1">
          {(entropy * 100).toFixed(0)}%
        </p>
        <p className="text-gray-500 text-xs font-light">
          Higher entropy indicates greater uncertainty in the model's internal
          representation.
        </p>
      </motion.div>
    </div>
  );
}
