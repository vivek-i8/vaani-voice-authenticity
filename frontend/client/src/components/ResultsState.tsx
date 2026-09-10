import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'wouter';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import VerdictPanel from './VerdictPanel';
import EvidencePanel from './EvidencePanel';
import ReliabilityPanel from './ReliabilityPanel';
import { useAudio } from '@/contexts/AudioContext';
import type { AnalysisResponse } from '@/lib/api';

/**
 * Results State — V2
 * Three-tab results view: Verdict / Evidence / Reliability
 * Per Section 13 of the source of truth:
 * - Verdict tab (default): label + confidence + caveat
 * - Evidence tab: per-model scores + agreement + reference examples
 * - Reliability tab: model card, evaluation by condition, limitations
 *
 * Uses existing shadcn Tabs component.
 */
interface ResultsStateProps {
  result: AnalysisResponse;
}

export default function ResultsState({ result }: ResultsStateProps) {
  const [, setLocation] = useLocation();
  const { clearAudio } = useAudio();
  const [activeTab, setActiveTab] = useState('verdict');

  if (!result) {
    return (
      <div className="max-w-6xl mx-auto text-center text-gray-400">
        Loading results...
      </div>
    );
  }

  const handleAnalyzeAnother = () => {
    clearAudio();
    setLocation('/');
  };

  const downloadReport = () => {
    const dataStr = JSON.stringify(result, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vaani_v2_report.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-4xl mx-auto"
    >
      {/* Results Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-8"
      >
        <h1 className="text-3xl md:text-4xl font-semibold text-white mb-3">
          Analysis Complete
        </h1>
        <p className="text-gray-400 text-sm font-light">
          Multi-signal voice authenticity analysis
        </p>
      </motion.div>

      {/* Three-Tab Layout */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-8 bg-white/5 border border-white/10">
          <TabsTrigger
            value="verdict"
            className="data-[state=active]:bg-teal-500/20 data-[state=active]:text-teal-300 data-[state=active]:border-b-2 data-[state=active]:border-teal-400 text-gray-400 text-sm font-medium"
          >
            Verdict
          </TabsTrigger>
          <TabsTrigger
            value="evidence"
            className="data-[state=active]:bg-teal-500/20 data-[state=active]:text-teal-300 data-[state=active]:border-b-2 data-[state=active]:border-teal-400 text-gray-400 text-sm font-medium"
          >
            Evidence
          </TabsTrigger>
          <TabsTrigger
            value="reliability"
            className="data-[state=active]:bg-teal-500/20 data-[state=active]:text-teal-300 data-[state=active]:border-b-2 data-[state=active]:border-teal-400 text-gray-400 text-sm font-medium"
          >
            Reliability
          </TabsTrigger>
        </TabsList>

        <AnimatePresence mode="wait">
          <TabsContent value="verdict" className="mt-0">
            <motion.div
              key="verdict"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <VerdictPanel result={result} />
            </motion.div>
          </TabsContent>

          <TabsContent value="evidence" className="mt-0">
            <motion.div
              key="evidence"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <EvidencePanel result={result} />
            </motion.div>
          </TabsContent>

          <TabsContent value="reliability" className="mt-0">
            <motion.div
              key="reliability"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <ReliabilityPanel />
            </motion.div>
          </TabsContent>
        </AnimatePresence>
      </Tabs>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
        className="flex flex-col md:flex-row gap-4 justify-center mt-10"
      >
        <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
          <Button
            onClick={handleAnalyzeAnother}
            size="lg"
            className="rounded-full px-8 bg-teal-500 text-slate-950 hover:bg-teal-400"
          >
            Analyze Another File
          </Button>
        </motion.div>
        <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
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
