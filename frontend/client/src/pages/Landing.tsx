import React from 'react';
import { useLocation } from 'wouter';
import { motion } from 'framer-motion';
import Header from '@/components/Header';
import TrustStrip from '@/components/TrustStrip';
import UploadCard from '@/components/UploadCard';
import GitHubSection from '@/components/GitHubSection';
import { useAudio } from '@/contexts/AudioContext';

/**
 * Landing Page
 * Design: Dark premium interface with hero section, trust strip, upload card, how it works, and GitHub section
 * Features: Smooth animations, responsive design, drag-and-drop upload
 */
export default function Landing() {
  const [, setLocation] = useLocation();
  const { setAudioFile, setAudioPreviewUrl, clearAudio } = useAudio();

  const handleFileSelect = (file: File) => {
    // Clear any existing audio first
    clearAudio();
    
    // Store file in global state
    setAudioFile(file);
    
    // Create preview URL
    const previewUrl = URL.createObjectURL(file);
    setAudioPreviewUrl(previewUrl);
    
    // Navigate to preview page
    setLocation('/preview');
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header showAnalyzeButton={false} />

      {/* Hero Section */}
      <section className="pt-32 pb-12 px-4 text-center">
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-5xl mx-auto"
        >
          <h1 className="text-4xl md:text-6xl font-semibold leading-tight mb-7">
            <span className="text-white">Detecting the </span>
            <span className="font-serif-italic text-teal-300 text-[1.15em] font-medium">
              Truth
            </span>
            <span className="text-white"> in Every Voice</span>
          </h1>
          <div className="text-gray-300 text-lg md:text-xl leading-relaxed max-w-3xl mx-auto">
            <p>Upload an audio clip.</p>
            <p className="mt-2">Get an instant verdict: Human or AI-generated.</p>
            <p className="mt-2">See a confidence score you can trust.</p>
          </div>
        </motion.div>
      </section>

      {/* Trust Strip */}
      <TrustStrip />

      {/* Upload Section */}
      <section className="py-16 px-4">
        <UploadCard onFileSelect={handleFileSelect} />
      </section>

      {/* GitHub Section */}
      <GitHubSection />

      {/* Footer */}
      <footer className="py-8 px-4 text-center border-t border-white/10">
        <p className="text-gray-500 text-sm">
          © 2024 VAANI Voice Authenticity Platform. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
