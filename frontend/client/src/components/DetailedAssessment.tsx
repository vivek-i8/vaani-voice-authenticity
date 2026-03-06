import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

/**
 * Detailed Assessment Component
 * Design: Display explanation text and recommended action
 * Shows assessment details with appropriate icon based on result
 */
interface DetailedAssessmentProps {
  explanation: string;
  label: 'Human' | 'AI' | 'Inconclusive';
}

export default function DetailedAssessment({
  explanation,
  label,
}: DetailedAssessmentProps) {
  const isHuman = label === 'Human';
  const isInconclusive = label === 'Inconclusive';
  const Icon = isHuman ? CheckCircle2 : isInconclusive ? AlertCircle : AlertCircle;
  const iconColor = isHuman ? 'text-teal-400' : isInconclusive ? 'text-amber-400' : 'text-rose-400';

  const recommendedAction = isHuman
    ? 'This voice sample appears to be authentic human speech. No further action required.'
    : isInconclusive 
    ? 'Audio quality is insufficient for definitive analysis. Please provide a clearer audio sample.'
    : 'This voice sample shows characteristics of AI-generated or synthetic speech. Verify the source before using for critical applications.';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, delay: 0.3 }}
      className="glass-card p-8 md:p-9 h-full"
    >
      <div className="flex items-start gap-4 mb-6">
        <Icon className={`w-6 h-6 ${iconColor} flex-shrink-0 mt-1`} />
        <div>
          <h3 className="text-white font-semibold text-lg mb-2">Assessment Details</h3>
          <p className="text-gray-300 text-sm leading-relaxed font-light">{explanation}</p>
        </div>
      </div>

      <div className="pt-6 border-t border-white/10">
        <h4 className="text-gray-400 text-xs font-semibold uppercase mb-3 font-light tracking-wide">
          Recommended Action
        </h4>
        <p className="text-gray-300 text-sm leading-relaxed font-light">{recommendedAction}</p>
      </div>
    </motion.div>
  );
}
