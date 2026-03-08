import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

/**
 * Detailed Assessment Component
 * Design: Display structured explanation with summary, analysis, and recommendation
 * Shows assessment details with appropriate icon based on result
 */
interface DetailedAssessmentProps {
  explanation: {
    summary: string;
    analysis: string;
    recommendation: string;
  };
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

  // Handle both structured and string explanations for backward compatibility
  const explanationObj = typeof explanation === 'string' 
    ? { summary: explanation, analysis: explanation, recommendation: "Stay alert and verify caller identity." }
    : explanation;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, delay: 0.3 }}
      className="glass-card p-8 md:p-9 h-full"
    >
      <div className="flex items-start gap-4 mb-6">
        <Icon className={`w-6 h-6 ${iconColor} flex-shrink-0 mt-1`} />
        <div className="flex-1">
          <h3 className="text-white font-semibold text-lg mb-4">Claude Explanation</h3>
          
          {/* Summary Section */}
          <div className="mb-4">
            <h4 className="text-gray-400 text-sm font-medium mb-2">Summary</h4>
            <p className="text-gray-300 text-sm leading-relaxed font-light">
              {explanationObj.summary || "Analysis summary not available."}
            </p>
          </div>

          {/* Technical Analysis Section */}
          <div className="mb-4">
            <h4 className="text-gray-400 text-sm font-medium mb-2">Technical Analysis</h4>
            <p className="text-gray-300 text-sm leading-relaxed font-light">
              {explanationObj.analysis || "Technical analysis not available."}
            </p>
          </div>

          {/* Recommended Action Section */}
          <div className="pt-4 border-t border-white/10">
            <h4 className="text-gray-400 text-sm font-medium mb-2">Recommended Action</h4>
            <p className="text-gray-300 text-sm leading-relaxed font-light">
              {explanationObj.recommendation || "Stay alert and verify caller identity."}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
