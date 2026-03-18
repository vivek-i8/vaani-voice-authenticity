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
          href="/datasets.txt"
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
