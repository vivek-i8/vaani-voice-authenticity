import React from 'react';
import { motion } from 'framer-motion';

export default function TrustStrip() {
  const badges = [
    'No audio storage',
    'In-memory processing',
    'Confidence-scored verdicts',
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const badgeVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
      },
    },
  };

  return (
    <section className="py-10 md:py-12 px-4 text-center">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, type: 'spring', bounce: 0.3 }}
        viewport={{ once: true }}
        className="mb-6"
      >
        <p className="text-gray-400 text-sm md:text-base">
          Built for real-world voice verification workflows.
        </p>
      </motion.div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="flex flex-wrap justify-center gap-3 md:gap-4"
      >
        {badges.map((badge, index) => (
          <motion.div
            key={index}
            variants={badgeVariants}
            className="rounded-full bg-white/5 border border-white/10 px-5 py-2.5 text-sm text-gray-200 hover:border-teal-400/60 hover:text-teal-200 transition-all duration-300"
          >
            {badge}
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}
