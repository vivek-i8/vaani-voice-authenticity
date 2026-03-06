import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * Upload Card Component
 * Design: Glassmorphism card (480px width, 32px padding)
 * Features: Drag and drop, file selection button
 * Supported formats: WAV, MP3, M4A, FLAC
 * Max size: 50MB
 * Animations: Teal glow on drag, checkmark on upload complete
 */
interface UploadCardProps {
  onFileSelect: (file: File) => void;
  isLoading?: boolean;
}

export default function UploadCard({ onFileSelect, isLoading = false }: UploadCardProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const supportedFormats = ['audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/flac'];
  const maxSize = 50 * 1024 * 1024; // 50MB

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const validateAndProcessFile = (file: File) => {
    if (!supportedFormats.includes(file.type)) {
      alert('Unsupported format. Please upload WAV, MP3, M4A, or FLAC.');
      return;
    }
    if (file.size > maxSize) {
      alert('File size exceeds 50MB limit.');
      return;
    }
    setUploadedFile(file);
    onFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      validateAndProcessFile(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      validateAndProcessFile(files[0]);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      id="upload-section"
      className="w-full max-w-xl mx-auto"
    >
      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        animate={{
          borderColor: isDragging ? '#2DD4BF' : 'rgba(255, 255, 255, 0.1)',
          boxShadow: isDragging ? '0 0 36px rgba(45, 212, 191, 0.25)' : 'none',
        }}
        transition={{ duration: 0.2 }}
        className="glass-card w-full p-10 md:p-12 text-center cursor-pointer hover:border-white/30 transition-colors duration-300"
      >
        {uploadedFile ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center gap-5"
          >
            <CheckCircle2 className="w-14 h-14 text-teal-400" />
            <div>
              <p className="text-white font-semibold text-base">File uploaded</p>
              <p className="text-gray-300 text-sm mt-2 truncate">{uploadedFile.name}</p>
            </div>
          </motion.div>
        ) : (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept=".wav,.mp3,.m4a,.flac"
              onChange={handleFileSelect}
              className="hidden"
            />
            <motion.div
              animate={{ y: isDragging ? -5 : 0 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col items-center gap-5"
            >
              <Upload className="w-12 h-12 text-teal-400" />
              <div>
                <p className="text-white font-semibold text-lg md:text-xl">
                  Drag and drop your audio file
                </p>
                <p className="text-gray-300 text-sm mt-2">
                  or click to browse
                </p>
              </div>
              <p className="text-gray-400 text-sm mt-1">
                WAV, MP3, M4A, FLAC • Max 50MB
              </p>
              <Button
                onClick={() => fileInputRef.current?.click()}
                size="lg"
                disabled={isLoading}
                className="mt-4 rounded-full px-8 bg-teal-500 text-slate-950 hover:bg-teal-400 active:scale-[0.99]"
              >
                Select File
              </Button>
            </motion.div>
          </>
        )}
      </motion.div>
    </motion.div>
  );
}
