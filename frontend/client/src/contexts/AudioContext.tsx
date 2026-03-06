import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

interface AudioContextType {
  audioFile: File | null;
  audioPreviewUrl: string | null;
  setAudioFile: (file: File | null) => void;
  setAudioPreviewUrl: (url: string | null) => void;
  clearAudio: () => void;
}

const AudioContext = createContext<AudioContextType | undefined>(undefined);

export function AudioProvider({ children }: { children: ReactNode }) {
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [audioPreviewUrl, setAudioPreviewUrl] = useState<string | null>(null);

  // Cleanup object URL when component unmounts or URL changes
  useEffect(() => {
    return () => {
      if (audioPreviewUrl) {
        URL.revokeObjectURL(audioPreviewUrl);
      }
    };
  }, [audioPreviewUrl]);

  const clearAudio = () => {
    if (audioPreviewUrl) {
      URL.revokeObjectURL(audioPreviewUrl);
    }
    setAudioFile(null);
    setAudioPreviewUrl(null);
  };

  return (
    <AudioContext.Provider value={{
      audioFile,
      audioPreviewUrl,
      setAudioFile,
      setAudioPreviewUrl,
      clearAudio
    }}>
      {children}
    </AudioContext.Provider>
  );
}

export function useAudio() {
  const context = useContext(AudioContext);
  if (context === undefined) {
    throw new Error('useAudio must be used within an AudioProvider');
  }
  return context;
}
