import React from 'react';
import { motion } from 'framer-motion';
import { Mic2, Brain, CheckCircle2 } from 'lucide-react';

/**
 * How It Works Section
 * Design: Three glass cards arranged horizontally
 * Cards have hover glow teal effect
 * Responsive: Stack on mobile
 */
export default function HowItWorks() {
  const steps = [
    {
      icon: Mic2,
      title: 'Capture Voice',
      description: 'Upload or record a voice sample.',
    },
    {
      icon: Brain,
      title: 'Neural Analysis',
      description:
        'VAANI extracts acoustic signals including pitch variance, spectral drift, and zero crossing rate.',
    },
    {
      icon: CheckCircle2,
      title: 'Authenticity Verdict',
      description: 'Receive authenticity classification and confidence scoring.',
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2,
      },
    },
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6 },
    },
  };

  return (
    <section
      id="how-it-works"
      className="py-24 px-4 md:px-8"
    >
      <div className="max-w-6xl mx-auto">
        <motion.h2
          initial={{ opacity: 0, y: -20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="text-3xl md:text-4xl font-semibold text-center mb-16 text-white"
        >
          How It Works
        </motion.h2>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8"
        >
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={index}
                variants={cardVariants}
                className="glass-card p-8 md:p-9 glow-teal group"
              >
                <motion.div
                  whileHover={{ scale: 1.1 }}
                  transition={{ duration: 0.3 }}
                  className="mb-6"
                >
                  <Icon className="w-11 h-11 text-teal-400 group-hover:text-teal-200 transition-colors" />
                </motion.div>
                <h3 className="text-lg font-semibold text-white mb-3">
                  {step.title}
                </h3>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {step.description}
                </p>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
