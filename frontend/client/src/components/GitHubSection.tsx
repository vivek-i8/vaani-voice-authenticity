import React from 'react';
import { motion } from 'framer-motion';

/**
 * GitHub Section Component
 * Design: Very small, transparent footer with GitHub and Datasets links
 */
export default function GitHubSection() {
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
          href="data:text/plain;charset=utf-8,Datasets%20used%20during%20development%3A%0A%0A**Medley%20Deepfake%20Speech%20Dataset**%0Ahttps%3A%2F%2Fdata.mendeley.com%2Fdatasets%2F79g59sp69z%2F1%0A%0A**Audio%20Deepfake%20Detection%20Dataset%20%28Kaggle%29**%0Ahttps%3A%2F%2Fwww.kaggle.com%2Fdatasets%2Fadarshsingh0903%2Faudio-deepfake-detection-dataset"
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
