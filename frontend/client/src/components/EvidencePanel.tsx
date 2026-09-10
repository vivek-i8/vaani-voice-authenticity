import React from 'react';
import { motion } from 'framer-motion';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  BookOpen,
} from 'lucide-react';
import type { AnalysisResponse } from '@/lib/api';

/**
 * EvidencePanel — V2 Tab
 * Shows: per-model scores, ensemble agreement, reference examples with similarity.
 * Reference examples always labeled "comparable reference evidence, not proof."
 */
interface EvidencePanelProps {
  result: AnalysisResponse;
}

function ScoreCard({
  label,
  score,
  prediction,
  available,
}: {
  label: string;
  score: number;
  prediction: string;
  available: boolean;
}) {
  const percent = Math.round(score * 100);
  const barColor =
    score >= 0.6
      ? 'bg-teal-400'
      : score <= 0.4
        ? 'bg-rose-400'
        : 'bg-amber-400';

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-gray-300">{label}</span>
        <span className="text-xs text-gray-500">
          {available ? `${percent}%` : 'Unavailable'}
        </span>
      </div>
      <div className="h-2.5 rounded-full bg-white/5 overflow-hidden mb-3">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: available ? `${percent}%` : '0%' }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className={`h-full rounded-full ${available ? barColor : 'bg-gray-600'}`}
        />
      </div>
      <p className="text-xs text-gray-500">
        {available ? `Prediction: ${prediction}` : 'Model not loaded'}
      </p>
    </motion.div>
  );
}

export default function EvidencePanel({ result }: EvidencePanelProps) {
  const { ensemble, signals, reference_examples, reference_note, degraded } =
    result;

  const AgreementIcon =
    ensemble.agreement === 'agree'
      ? CheckCircle2
      : ensemble.agreement === 'disagree'
        ? XCircle
        : AlertTriangle;

  const agreementColor =
    ensemble.agreement === 'agree'
      ? 'text-teal-400'
      : ensemble.agreement === 'disagree'
        ? 'text-amber-400'
        : 'text-gray-400';

  const agreementLabel =
    ensemble.agreement === 'agree'
      ? 'Signals agree'
      : ensemble.agreement === 'disagree'
        ? 'Signals disagree'
        : ensemble.agreement === 'single-model-only'
          ? 'Single model only'
          : ensemble.agreement;

  const vaaniPrediction =
    ensemble.vaani_signal.score >= 0.6
      ? 'Human'
      : ensemble.vaani_signal.score <= 0.4
        ? 'AI'
        : 'Ambiguous';

  const spectraPrediction = ensemble.spectra_signal.available
    ? ensemble.spectra_signal.score >= 0.6
      ? 'Human'
      : ensemble.spectra_signal.score <= 0.4
        ? 'AI'
        : 'Ambiguous'
    : 'Unavailable';

  return (
    <div className="space-y-6">
      {/* Degraded Mode Banner */}
      {degraded && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20"
        >
          <p className="text-xs text-amber-400">
            Single-model analysis — ensemble signal unavailable. Only the VAANI
            signal was used for this verdict.
          </p>
        </motion.div>
      )}

      {/* Model Scores */}
      <div>
        <h3 className="text-gray-400 text-sm font-medium mb-4">
          Per-Signal Model Scores
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ScoreCard
            label="VAANI Fusion Signal"
            score={ensemble.vaani_signal.score}
            prediction={vaaniPrediction}
            available={true}
          />
          <ScoreCard
            label="Spectra-AASIST3"
            score={ensemble.spectra_signal.score}
            prediction={spectraPrediction}
            available={ensemble.spectra_signal.available ?? false}
          />
        </div>
      </div>

      {/* Ensemble Agreement */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="glass-card p-6"
      >
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-gray-400 text-xs font-medium uppercase tracking-wider">
            Ensemble Agreement
          </h4>
          <div className={`flex items-center gap-1.5 ${agreementColor}`}>
            <AgreementIcon className="w-4 h-4" />
            <span className="text-xs font-medium">{agreementLabel}</span>
          </div>
        </div>
        {ensemble.agreement === 'disagree' && (
          <p className="text-gray-500 text-xs font-light">
            The two independent signals produced conflicting predictions. When
            signals disagree, the ensemble treats this as an uncertainty
            condition rather than forcing a binary answer.
          </p>
        )}
        {ensemble.agreement === 'single-model-only' && (
          <p className="text-gray-500 text-xs font-light">
            Only the VAANI signal was available. The ensemble was not applied.
            The verdict reflects a single-signal analysis.
          </p>
        )}
      </motion.div>

      {/* Acoustic Features */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-card p-6"
      >
        <h4 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-4">
          Acoustic Features
        </h4>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-gray-400 text-xs mb-1 font-light">
              Pitch Variance
            </p>
            <p className="text-teal-400 font-medium text-sm">
              {(signals.pitch_variance * 100).toFixed(0)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-xs mb-1 font-light">
              Spectral Drift
            </p>
            <p className="text-teal-400 font-medium text-sm">
              {(signals.spectral_drift * 100).toFixed(0)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-xs mb-1 font-light">
              ZCR Variance
            </p>
            <p className="text-teal-400 font-medium text-sm">
              {(signals.zcr_variance * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      </motion.div>

      {/* Reference Examples */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="glass-card p-6"
      >
        <div className="flex items-center gap-2 mb-2">
          <BookOpen className="w-4 h-4 text-gray-400" />
          <h4 className="text-gray-400 text-xs font-medium uppercase tracking-wider">
            Reference Evidence
          </h4>
        </div>
        <p className="text-gray-500 text-xs mb-5 italic">
          Comparable references, not proof. Nearest-neighbor matches from the
          training dataset.
        </p>

        {!reference_examples || reference_examples.length === 0 ? (
          <p className="text-gray-500 text-sm">
            {reference_note ||
              'No reference index available yet. Reference evidence comparison requires a built index from the training dataset.'}
          </p>
        ) : (
          <div className="space-y-3">
            {reference_examples.map((ex, i) => {
              const similarityPercent = Math.round(ex.similarity * 100);
              const labelColor =
                ex.label === 'bonafide' || ex.label === 'Human'
                  ? 'text-teal-400'
                  : ex.label === 'spoof' || ex.label === 'AI'
                    ? 'text-rose-400'
                    : 'text-gray-400';
              const barColor =
                ex.label === 'bonafide' || ex.label === 'Human'
                  ? 'bg-teal-400'
                  : ex.label === 'spoof' || ex.label === 'AI'
                    ? 'bg-rose-400'
                    : 'bg-gray-400';

              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.1 }}
                  className="flex items-center gap-4 p-3 rounded-lg bg-white/[0.02] border border-white/5"
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white/5 flex items-center justify-center">
                    <span className="text-xs text-gray-400">#{i + 1}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-medium ${labelColor}`}>
                        {ex.label}
                      </span>
                      <span className="text-xs text-gray-500">
                        similarity: {similarityPercent}%
                      </span>
                      {ex.source && (
                        <span className="text-xs text-gray-600">
                          ({ex.source})
                        </span>
                      )}
                    </div>
                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${similarityPercent}%` }}
                        transition={{ duration: 0.6, ease: 'easeOut' }}
                        className={`h-full rounded-full ${barColor}`}
                      />
                    </div>
                    {ex.filename && (
                      <p className="text-xs text-gray-600 mt-1 truncate">
                        {ex.filename}
                      </p>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}

        {reference_note && reference_examples && reference_examples.length > 0 && (
          <p className="text-xs text-gray-500 mt-4 italic">{reference_note}</p>
        )}
      </motion.div>
    </div>
  );
}
