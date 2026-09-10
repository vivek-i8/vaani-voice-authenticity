import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Info, AlertTriangle, BarChart3 } from 'lucide-react';
import { fetchModelCard, type ModelCardResponse } from '@/lib/api';

/**
 * ReliabilityPanel — V2 Tab
 * Shows: model card info, evaluation metrics by condition (clean/noisy/compressed),
 * known limitations, methodology disclosure.
 * If eval report is unavailable, shows explicit "unavailable" state.
 */
export default function ReliabilityPanel() {
  const [modelCard, setModelCard] = useState<ModelCardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const card = await fetchModelCard();
        if (!cancelled) {
          setModelCard(card);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load model card',
          );
          setLoading(false);
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="glass-card p-8 animate-pulse">
          <div className="h-4 bg-white/10 rounded w-1/3 mb-4" />
          <div className="h-3 bg-white/5 rounded w-2/3" />
        </div>
      </div>
    );
  }

  if (error || !modelCard) {
    return (
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-8"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-gray-300 text-sm font-medium mb-2">
                Evaluation Report Unavailable
              </h3>
              <p className="text-gray-500 text-xs font-light">
                The model card and evaluation report could not be loaded. This
                does not affect per-clip verdicts — only the Reliability tab is
                affected.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Static known limitations even without model card */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-8"
        >
          <h4 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-4">
            Known Limitations
          </h4>
          <ul className="space-y-2">
            <li className="flex items-start gap-2 text-sm text-gray-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
              Performance metrics are not yet available for this deployment
            </li>
            <li className="flex items-start gap-2 text-sm text-gray-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
              Evaluation was not run on the In-the-Wild dataset conditions
            </li>
          </ul>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Model Card */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-8"
      >
        <div className="flex items-center gap-2 mb-6">
          <BarChart3 className="w-4 h-4 text-gray-400" />
          <h3 className="text-gray-400 text-sm font-medium">Model Card</h3>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-gray-500 text-xs mb-1">Model Version</p>
            <p className="text-gray-200 text-sm font-medium">
              {modelCard.model_version}
            </p>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1">Dataset</p>
            <p className="text-gray-200 text-sm font-medium">
              {modelCard.dataset}
            </p>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1">Split Method</p>
            <p className="text-gray-200 text-sm font-medium">
              {modelCard.split_method}
            </p>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1">Spectra Commit</p>
            <p className="text-gray-200 text-sm font-medium font-mono">
              {modelCard.spectra_commit.slice(0, 8)}
            </p>
          </div>
        </div>

        {/* Threshold Constants */}
        <div className="pt-4 border-t border-white/10">
          <h4 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-3">
            Threshold Constants
          </h4>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-gray-500 text-xs mb-1">Agreement</p>
              <p className="text-teal-400 text-sm font-medium">
                {modelCard.threshold_constants.agreement_threshold}
              </p>
            </div>
            <div>
              <p className="text-gray-500 text-xs mb-1">Entropy</p>
              <p className="text-teal-400 text-sm font-medium">
                {modelCard.threshold_constants.entropy_threshold}
              </p>
            </div>
            <div>
              <p className="text-gray-500 text-xs mb-1">Min Reference</p>
              <p className="text-teal-400 text-sm font-medium">
                {modelCard.threshold_constants.min_reference_similarity}
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Evaluation Metrics by Condition */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-8"
      >
        <h4 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-4">
          Empirical Reliability by Condition
        </h4>

        {modelCard.evaluation ? (
          <div className="space-y-5">
            {(['clean', 'noisy', 'compressed'] as const).map((condition) => {
              const eval_ = modelCard.evaluation![condition];
              return (
                <div key={condition}>
                  <h5 className="text-gray-300 text-sm font-medium mb-3 capitalize">
                    {condition} Condition
                  </h5>
                  <div className="grid grid-cols-4 gap-3">
                    <div className="text-center p-3 rounded-lg bg-white/[0.02] border border-white/5">
                      <p className="text-gray-500 text-xs mb-1">EER</p>
                      <p className="text-teal-400 text-sm font-medium">
                        {(eval_.eer * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-white/[0.02] border border-white/5">
                      <p className="text-gray-500 text-xs mb-1">Accuracy</p>
                      {eval_.accuracy != null ? (
                        <p className="text-teal-400 text-sm font-medium">
                          {(eval_.accuracy * 100).toFixed(1)}%
                        </p>
                      ) : (
                        <p className="text-gray-500 text-sm font-medium">N/A</p>
                      )}
                    </div>
                    <div className="text-center p-3 rounded-lg bg-white/[0.02] border border-white/5">
                      <p className="text-gray-500 text-xs mb-1">FPR</p>
                      {eval_.fpr != null ? (
                        <p className="text-rose-400 text-sm font-medium">
                          {(eval_.fpr * 100).toFixed(1)}%
                        </p>
                      ) : (
                        <p className="text-gray-500 text-sm font-medium">N/A</p>
                      )}
                    </div>
                    <div className="text-center p-3 rounded-lg bg-white/[0.02] border border-white/5">
                      <p className="text-gray-500 text-xs mb-1">FNR</p>
                      {eval_.fnr != null ? (
                        <p className="text-rose-400 text-sm font-medium">
                          {(eval_.fnr * 100).toFixed(1)}%
                        </p>
                      ) : (
                        <p className="text-gray-500 text-sm font-medium">N/A</p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-sm font-light">
            Evaluation report not yet generated. Run{' '}
            <code className="text-teal-400 text-xs">evaluate.py</code> after
            retraining to produce condition-specific metrics.
          </p>
        )}
      </motion.div>

      {/* Methodology Disclosure */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="glass-card p-8"
      >
        <div className="flex items-start gap-3">
          <Info className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-3">
              Methodology
            </h4>
            <p className="text-gray-300 text-sm font-light leading-relaxed">
              VAANI uses a two-signal ensemble: a custom fusion head (Wav2Vec2
              embeddings + acoustic features) and an independent anti-spoofing
              signal (Spectra-AASIST3). The final verdict is determined by a
              deterministic truth table, not a learned meta-model. Reference
              evidence is retrieved by nearest-neighbor cosine similarity on
              Wav2Vec2 embeddings. Results are reported under clean, noisy, and
              compressed audio conditions separately.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Known Limitations */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-card p-8"
      >
        <h4 className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-4">
          Known Limitations
        </h4>
        <ul className="space-y-2">
          {(modelCard.known_limitations || []).map((limitation, i) => (
            <li
              key={i}
              className="flex items-start gap-2 text-sm text-gray-400 font-light"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
              {limitation}
            </li>
          ))}
          {(!modelCard.known_limitations ||
            modelCard.known_limitations.length === 0) && (
            <>
              <li className="flex items-start gap-2 text-sm text-gray-400 font-light">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                Performance varies significantly by audio quality and recording
                conditions
              </li>
              <li className="flex items-start gap-2 text-sm text-gray-400 font-light">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                The Inconclusive verdict may appear for ambiguous audio — this is
                a designed behavior, not a failure
              </li>
              <li className="flex items-start gap-2 text-sm text-gray-400 font-light">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                This system is not a forensic tool and should not be used as the
                sole basis for high-stakes decisions
              </li>
            </>
          )}
        </ul>
      </motion.div>
    </div>
  );
}
