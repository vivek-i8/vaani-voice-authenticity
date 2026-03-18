import React from 'react';
import { motion } from 'framer-motion';

/**
 * GitHub Section Component
 * Design: Very small, transparent footer with GitHub and Datasets links
 */
export default function GitHubSection() {
  const datasetsContent = `Datasets used during development:

**Medley Deepfake Speech Dataset**
https://data.mendeley.com/datasets/79g59sp69z/1

**Audio Deepfake Detection Dataset (Kaggle)**
https://www.kaggle.com/datasets/adarshsingh0903/audio-deepfake-detection-dataset`;

  return (
    <section className="py-12 px-4">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        viewport={{ once: true }}
        className="max-w-2xl mx-auto flex items-center justify-center gap-8 text-center"
      >
        {/* GitHub Link */}
        <a
          href="https://github.com/vivek-i8/vaani-voice-authenticity"
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-400 hover:text-teal-300 transition-colors duration-300 text-sm opacity-80 hover:opacity-100"
        >
          GitHub
        </a>

        {/* Dataset Link */}
        <a
          href="data:text/plain;charset=utf-8,${encodeURIComponent(datasetsContent)}"
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-400 hover:text-teal-300 transition-colors duration-300 text-sm opacity-80 hover:opacity-100"
        >
          Datasets
        </a>
      </motion.div>
    </section>
  );
}
