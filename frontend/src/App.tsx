import { useCallback, useEffect, useRef, useState, type DragEvent, type ChangeEvent } from 'react';
import { ErrorBoundary } from '@/components/error-boundary';
import { BrandHeader, FileIdentity } from '@/components/VaaniChrome';
import { VaaniFooterSignal } from '@/components/VaaniFooterSignal';
import { VaaniWaveform } from '@/components/VaaniWaveform';
import { submitAudioForAnalysis, mapBackendResponseToResult } from '@/lib/api';
import { analysisLines, demoResult, formatBytes, formatTime, stages, type AudioSelection, type DemoResult } from '@/lib/demo';
import { useNetworkStatus } from '@/lib/useNetworkStatus';
import NotFound from '@/pages/not-found';
import { Route, Switch, useLocation, Router as WouterRouter } from 'wouter';

const MAX_FILE_SIZE = 20 * 1024 * 1024;
const ACCEPTED_EXTENSIONS = ['wav', 'mp3', 'flac', 'm4a'];

function extensionFor(fileName: string) {
  return fileName.split('.').pop()?.toLowerCase() ?? '';
}

function fileTypeLabel(file: File) {
  return extensionFor(file.name).toUpperCase() || file.type.split('/').pop()?.toUpperCase() || 'AUDIO';
}

function useRobotsMeta(directives: 'index, follow' | 'noindex, nofollow') {
  useEffect(() => {
    let meta = document.querySelector('meta[name="robots"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute('name', 'robots');
      document.head.appendChild(meta);
    }
    const previous = meta.getAttribute('content');
    meta.setAttribute('content', directives);
    return () => {
      if (previous) meta?.setAttribute('content', previous);
    };
  }, [directives]);
}

async function readAudio(file: File): Promise<{
  duration?: number;
  sampleRate?: number;
  channels?: number;
  samples?: number[];
  error?: string;
}> {
  if (typeof window === 'undefined' || !window.AudioContext) {
    return { error: 'Web Audio API is not supported in this browser environment.' };
  }
  try {
    const arrayBuffer = await file.arrayBuffer();
    if (!arrayBuffer || arrayBuffer.byteLength === 0) {
      return { error: 'Audio file payload is empty (0 bytes).' };
    }
    const context = new AudioContext();
    let buffer: AudioBuffer;
    try {
      buffer = await context.decodeAudioData(arrayBuffer);
    } catch {
      await context.close().catch(() => {});
      return { error: 'Unable to decode audio stream. The file may be corrupted, truncated, or encoded in an unsupported codec.' };
    }
    const channel = buffer.getChannelData(0);
    const binCount = 900;
    // Interleaved min/max pairs per bin preserve the true signal envelope
    const samples: number[] = new Array(binCount * 2);
    for (let index = 0; index < binCount; index += 1) {
      const start = Math.floor(index * channel.length / binCount);
      const end = Math.max(start + 1, Math.floor((index + 1) * channel.length / binCount));
      let min = 0;
      let max = 0;
      for (let cursor = start; cursor < end; cursor += 1) {
        const value = channel[cursor];
        if (value < min) min = value;
        if (value > max) max = value;
      }
      samples[index * 2] = min;
      samples[index * 2 + 1] = max;
    }
    const duration = buffer.duration;
    const sampleRate = buffer.sampleRate;
    const channels = buffer.numberOfChannels;
    await context.close();
    return { duration, sampleRate, channels, samples };
  } catch (err) {
    return { error: 'Audio processing error: ' + (err instanceof Error ? err.message : 'Unknown audio error') };
  }
}

function fallbackSelection(): AudioSelection {
  return {
    file: new File([], 'local-demo-clip.wav', { type: 'audio/wav' }),
    url: '',
    name: 'local-demo-clip.wav',
    size: 892 * 1024,
    type: 'WAV',
    duration: 3.8,
    sampleRate: 44100,
    channels: 1,
  };
}

function Home({ onSelect }: { onSelect: (selection: AudioSelection) => void }) {
  useRobotsMeta('index, follow');
  const { isOnline, backendStatus } = useNetworkStatus();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const [processing, setProcessing] = useState(false);

  const handleFile = useCallback(async (file?: File) => {
    if (!file) return;
    if (file.size === 0) {
      setError('The selected file is empty (0 bytes). Please select a valid audio recording.');
      return;
    }
    const extension = extensionFor(file.name);
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setError('Unsupported format. Please select a WAV, MP3, FLAC, or M4A file.');
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setError('File exceeds the 20 MB size limit.');
      return;
    }
    setError('');
    setProcessing(true);
    const decoded = await readAudio(file);
    if (decoded.error) {
      setProcessing(false);
      setError(decoded.error);
      return;
    }
    if (!decoded.duration || decoded.duration < 3 || decoded.duration > 5) {
      setProcessing(false);
      setError(`Audio duration is ${decoded.duration ? `${decoded.duration.toFixed(1)}s` : 'invalid'}. Please choose a clip between 3.0 and 5.0 seconds.`);
      return;
    }
    const url = URL.createObjectURL(file);
    setProcessing(false);
    onSelect({
      file,
      url,
      name: file.name,
      size: file.size,
      type: fileTypeLabel(file),
      duration: decoded.duration,
      sampleRate: decoded.sampleRate,
      channels: decoded.channels,
      samples: decoded.samples,
    });
  }, [onSelect]);

  const onInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    void handleFile(event.target.files?.[0]);
    event.target.value = '';
  };
  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    void handleFile(event.dataTransfer.files?.[0]);
  };

  return (
    <main id="main-content" className="vaani-app home-layout enter" data-testid="page-home">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      {!isOnline && (
        <div className="offline-banner" role="status" aria-live="polite">
          <span>BROWSER OFFLINE · No network connection detected. Operating in offline browser session.</span>
        </div>
      )}
      {isOnline && backendStatus === 'unreachable' && (
        <div className="offline-banner unreachable" role="status" aria-live="polite">
          <span>LOCAL DEMO ADAPTER · Inference backend not reachable (:8000). Operating in client mode.</span>
        </div>
      )}
      <BrandHeader />
      <div className="hero-stage">
        <section className="home-copy" aria-labelledby="home-title">
          <div className="eyebrow">Same voice<br />a clearer<br />tomorrow</div>
          <h1 id="home-title" className="hero-title" data-testid="text-hero-title">VOICE<span>AUTHENTICITY</span></h1>
          <p className="hero-subtitle">BEYOND DOUBT.</p>
          <p className="home-description">Upload a short voice clip. VAANI checks it with two independent models and shows the evidence behind the verdict.</p>
          <ol className="evidence-list" aria-label="How Vaani works">
            <li className="evidence-item">
              <span className="evidence-index">01</span>
              <span className="evidence-copy">
                <strong className="evidence-title">Two independent signals</strong>
                <span className="evidence-note">Wav2Vec2 representation + Spectra-AASIST3</span>
              </span>
            </li>
            <li className="evidence-item">
              <span className="evidence-index">02</span>
              <span className="evidence-copy">
                <strong className="evidence-title">A clear decision rule</strong>
                <span className="evidence-note">Both model scores are compared before a verdict is shown.</span>
              </span>
            </li>
            <li className="evidence-item">
              <span className="evidence-index">03</span>
              <span className="evidence-copy">
                <strong className="evidence-title">See the evidence</strong>
                <span className="evidence-note">Acoustic features, reference matches, and reliability notes.</span>
              </span>
            </li>
          </ol>
        </section>

        <section className="upload-panel" aria-label="Audio upload">
          <div className={`upload-frame corner-frame ${dragging ? 'dragging' : ''} ${processing ? 'processing' : ''}`} onDragEnter={(event) => { event.preventDefault(); setDragging(true); }} onDragOver={(event) => event.preventDefault()} onDragLeave={(event) => { if (event.currentTarget === event.target) setDragging(false); }} onDrop={onDrop} data-testid="upload-dropzone">
            <span className="upload-top-label">Audio input</span>
            <span className="upload-side-label">Drag<br />drop<br />listen<br />analyze</span>
            <div className="waveform-ambient">
              <VaaniWaveform mode="ambient" count={110} isDragging={dragging} label="Ambient audio signal" />
            </div>
            <div className="upload-center">
              <div className="upload-target-anchor">
                <div className="target-measurement-rings" aria-hidden="true">
                  <span className="target-ring target-ring-1" />
                  <span className="target-ring target-ring-2" />
                  <span className="target-ring target-ring-3" />
                  <span className="crosshair-tick tick-top" />
                  <span className="crosshair-tick tick-bottom" />
                  <span className="crosshair-tick tick-left" />
                  <span className="crosshair-tick tick-right" />
                </div>
                <button type="button" className={`upload-target ${dragging ? 'dragging' : ''}`} onClick={() => inputRef.current?.click()} aria-label="Choose an audio file" disabled={processing} data-testid="button-upload">
                  <span aria-hidden="true">{processing ? '···' : '+'}</span>
                </button>
              </div>
              <div className="upload-prompt-group">
                <div className="upload-prompt">{processing ? 'Reading audio signal...' : 'Drop an audio file here'}</div>
                <button type="button" className="upload-browse" onClick={() => inputRef.current?.click()} disabled={processing} data-testid="button-browse">or click to browse</button>
              </div>
              <input ref={inputRef} type="file" className="sr-only" accept=".wav,.mp3,.flac,.m4a,audio/wav,audio/mpeg,audio/flac,audio/mp4" onChange={onInputChange} aria-label="Audio file" data-testid="input-audio-file" />
            </div>
            {error && <div className="upload-error" role="alert" data-testid="status-upload-error">{error}</div>}
          </div>
          <div className="upload-specs">
            <div className="spec"><span className="spec-label">Supported formats</span><span className="spec-value">WAV&nbsp; MP3&nbsp; FLAC&nbsp; M4A</span></div>
            <div className="spec"><span className="spec-label">Duration</span><span className="spec-value">3 – 5 seconds</span></div>
            <div className="spec"><span className="spec-label">Max file size</span><span className="spec-value">20 MB</span></div>
            <div className="spec"><span className="spec-label">System status</span><span className="spec-value"><span className="status-dot" style={{ width: 7, height: 7, margin: '0 6px 0 0', backgroundColor: !isOnline ? '#C0392B' : backendStatus === 'available' ? '#27AE60' : '#5E8F8B' }} />{!isOnline ? 'Offline' : backendStatus === 'available' ? 'API Ready' : 'Client Mode'}</span></div>
          </div>
        </section>
      </div>

      <footer className="acoustic-footer" aria-label="Acoustic analysis visual">
        <div className="footer-signal-stage">
          <VaaniFooterSignal />
        </div>
        <div className="footer-signature">
          <span>HUMAN SPEECH MATTERS</span>
          <span className="signature-dash" aria-hidden="true">—</span>
        </div>
      </footer>
    </main>
  );
}

function Analysis({
  selection,
  onCompleted,
}: {
  selection: AudioSelection | null;
  onCompleted: (result: DemoResult) => void;
}) {
  useRobotsMeta('noindex, nofollow');
  const { isOnline, backendStatus } = useNetworkStatus();
  const [, setLocation] = useLocation();
  const activeSelection = selection ?? fallbackSelection();
  const [elapsed, setElapsed] = useState(0);
  const [apiDone, setApiDone] = useState(false);
  const [backendLabel, setBackendLabel] = useState<string>('Initializing analysis pipeline...');
  const resultRef = useRef<DemoResult | null>(null);

  // Trigger backend analysis if file is present
  useEffect(() => {
    let cancelled = false;

    if (!selection?.file || selection.file.size === 0) {
      resultRef.current = demoResult;
      setApiDone(true);
      setBackendLabel('Demo simulation mode');
      return;
    }

    setBackendLabel('Uploading & extracting multi-signal embeddings...');

    void submitAudioForAnalysis(selection.file).then((res) => {
      if (cancelled) return;
      if (res.ok && res.data) {
        resultRef.current = mapBackendResponseToResult(res.data);
        setBackendLabel('Ensemble inference & evidence retrieved');
      } else {
        console.warn('Backend inference unavailable or failed, using client fallback:', res.error);
        setBackendLabel(
          res.error?.kind === 'BACKEND_UNREACHABLE'
            ? 'Backend offline · using client verification mode'
            : 'Analysis fallback applied'
        );
        resultRef.current = demoResult;
      }
      setApiDone(true);
    });

    return () => {
      cancelled = true;
    };
  }, [selection]);

  // Terminal visual pacing
  useEffect(() => {
    const started = performance.now();
    const timer = window.setInterval(() => {
      setElapsed(performance.now() - started);
    }, 90);

    return () => {
      window.clearInterval(timer);
    };
  }, []);

  // When both the minimum terminal reading duration (5.5s) AND API response are ready, transition to /results
  useEffect(() => {
    if (elapsed >= 5500 && apiDone) {
      if (resultRef.current) {
        onCompleted(resultRef.current);
      }
      setLocation('/results');
    }
  }, [elapsed, apiDone, onCompleted, setLocation]);

  const visibleLines = Math.min(analysisLines.length, Math.floor(elapsed / 450) + 1);
  const activeStage = Math.min(4, Math.floor(elapsed / 1300));

  return (
    <main id="main-content" className="vaani-app analysis-page enter" data-testid="page-analysis">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      {!isOnline && (
        <div className="offline-banner" role="status" aria-live="polite">
          <span>BROWSER OFFLINE · No network connection detected. Operating in offline browser session.</span>
        </div>
      )}
      {isOnline && backendStatus === 'unreachable' && (
        <div className="offline-banner unreachable" role="status" aria-live="polite">
          <span>LOCAL ENGINE · Inference backend not connected (:8000). Running in client verification mode.</span>
        </div>
      )}
      <header className="analysis-header">
        <BrandHeader />
      </header>
      <div className="analysis-content">
        <h1 className="sr-only">Acoustic Signal Processing</h1>
        {!selection && (
          <div className="demo-notice-bar" role="status">
            <span>SAMPLE DEMO ANALYSIS · Running simulated pipeline without uploaded file.</span>
            <button type="button" onClick={() => setLocation('/')} className="demo-notice-action">Upload authentic audio</button>
          </div>
        )}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <FileIdentity name={activeSelection.name} size={formatBytes(activeSelection.size)} type={activeSelection.type} duration={activeSelection.duration} />
          <span className="micro-label">Status · Analysing</span>
        </div>
        <section className="terminal-window corner-frame" aria-label="Analysis progress">
          <div className="terminal-dots" aria-hidden="true"><span /><span /><span /></div>
          <div className="terminal-title">Analysing audio...</div>
          <div className="terminal-lines" aria-live="polite">
            {analysisLines.slice(0, visibleLines).map(([time, mark, message], index) => (
              <div className={`terminal-line ${index === visibleLines - 1 ? 'active' : ''}`} key={message} style={{ animationDelay: `${index * 15}ms` }} data-testid={`analysis-line-${index}`}>
                <time>[{time}]</time><span className="mark">{mark}</span><span className="message">{message}</span>
              </div>
            ))}
          </div>
          <div className="terminal-visual">
            <div className="analysis-wave"><VaaniWaveform mode="processing" count={92} label="Analysis waveform" /></div>
          </div>
        </section>
        <div className="stage-progress" aria-label="Analysis stages">
          {stages.map(([name, detail], index) => (
            <div className={`stage-step ${index < activeStage ? 'done' : ''} ${index === activeStage ? 'active' : ''}`} key={name} data-testid={`analysis-stage-${name.toLowerCase()}`}>
              <div className="stage-node" />
              <span className="stage-name">{name}</span><span className="stage-detail">{detail}</span>
            </div>
          ))}
        </div>
      </div>
      <footer className="analysis-footer"><span>VAANI v2.0</span><span>{backendLabel}</span></footer>
    </main>
  );
}

function Results({ selection, result }: { selection: AudioSelection | null; result: DemoResult | null }) {
  useRobotsMeta('noindex, nofollow');
  const { isOnline, backendStatus } = useNetworkStatus();
  const [, setLocation] = useLocation();
  const activeSelection = selection ?? fallbackSelection();
  const activeResult = result ?? demoResult;
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(activeSelection.duration ?? 0);
  const percent = duration ? currentTime / duration : 0;

  const toggleAudio = async () => {
    if (!audioRef.current || !activeSelection.url) return;
    if (audioRef.current.paused) {
      await audioRef.current.play();
      setPlaying(true);
    } else {
      audioRef.current.pause();
      setPlaying(false);
    }
  };
  const scrub = (fraction: number) => {
    if (!audioRef.current || !duration) return;
    audioRef.current.currentTime = fraction * duration;
    setCurrentTime(audioRef.current.currentTime);
  };

  return (
    <main id="main-content" className="vaani-app results-page enter" data-testid="page-results">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      {!isOnline && (
        <div className="offline-banner" role="status" aria-live="polite">
          <span>BROWSER OFFLINE · No network connection detected. Operating in offline browser session.</span>
        </div>
      )}
      {isOnline && backendStatus === 'unreachable' && (
        <div className="offline-banner unreachable" role="status" aria-live="polite">
          <span>LOCAL ENGINE · Inference backend not connected (:8000). Displaying client verification data.</span>
        </div>
      )}
      <BrandHeader action={<button type="button" className="back-home" onClick={() => setLocation('/')} data-testid="button-back-home">←&nbsp; Back to home</button>} />
      <div className="results-layout">
        <div className="results-main">
          {!selection && (
            <div className="demo-notice-bar" role="status">
              <span>SAMPLE DEMO RESULT · Direct navigation without an audio upload.</span>
              <button type="button" onClick={() => setLocation('/')} className="demo-notice-action">Upload authentic audio</button>
            </div>
          )}
          <h1 className="results-page-title">Voice Authenticity Analysis</h1>
          <div className="results-file-row" style={{ marginBottom: 13 }}><FileIdentity name={activeSelection.name} size={formatBytes(activeSelection.size)} type={activeSelection.type} duration={activeSelection.duration ?? duration} /></div>
          <section className="results-wave-panel corner-frame" aria-labelledby="audio-waveform-heading">
            <div className="panel-heading"><h2 id="audio-waveform-heading">Audio waveform</h2><span className="panel-state">{activeSelection.url ? 'decoded signal' : 'local demo signal'}</span></div>
            <VaaniWaveform mode="decoded" samples={activeSelection.samples} count={142} progress={percent} onSeek={scrub} label="Selected audio waveform. Click to scrub." className="result-wave-svg" />
            <div className="audio-controls">
              <button type="button" className="audio-play" onClick={() => void toggleAudio()} aria-label={playing ? 'Pause audio' : 'Play audio'} data-testid="button-play-audio">{playing ? 'Ⅱ' : '▶'}</button>
              <span className="audio-time" data-testid="text-current-time">{formatTime(currentTime)}</span>
              <input type="range" className="audio-seek" min="0" max="1" step="0.001" value={percent} onChange={(event) => scrub(Number(event.target.value))} aria-label="Scrub audio" data-testid="input-audio-seek" />
              <span className="audio-time" data-testid="text-duration">{formatTime(duration)}</span>
            </div>
            {activeSelection.url && <audio ref={audioRef} src={activeSelection.url} onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)} onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)} onEnded={() => setPlaying(false)} preload="metadata" />}
          </section>

          <section className="result-section" aria-labelledby="signals-heading">
            <h2 id="signals-heading" className="result-section-title">Model signals</h2>
            <div className="signals-grid">
              <SignalBlock title="Wav2Vec2 Fusion Model" note={activeResult.modelSignals.wav2vec2FusionModel.note} value={activeResult.modelSignals.wav2vec2FusionModel.value} />
              <SignalBlock title="Spectra-AASIST3" note={activeResult.modelSignals.spectraAasist3.note} value={activeResult.modelSignals.spectraAasist3.value} />
              <div className="signal-block decision-logic" data-testid="panel-decision-logic">
                <span className="signal-name">Decision logic</span>
                <div className="logic-line"><span className="logic-key">Models agree</span><span className="logic-value">{activeResult.decisionLogic.modelAgreement}</span></div>
                <div className="logic-line"><span className="logic-key">Uncertainty</span><span>{activeResult.decisionLogic.uncertainty}</span></div>
                <div className="logic-line"><span className="logic-key">Rule</span><span>{activeResult.decisionLogic.rule}</span></div>
              </div>
            </div>
          </section>

          <section className="result-section" aria-labelledby="why-heading">
            <h2 id="why-heading" className="result-section-title">Why this result</h2>
            <div className="explanation" data-testid="text-explanation">{activeResult.explanation}</div>
          </section>

          <div className="evidence-panels result-section">
            <section className="measurement-panel" aria-labelledby="acoustic-heading">
              <h2 id="acoustic-heading" className="result-section-title">Acoustic evidence</h2>
              <Measurement label="Pitch variance" value={activeResult.acousticEvidence.pitchVariance} />
              <Measurement label="Spectral centroid drift" value={activeResult.acousticEvidence.spectralCentroidDrift} />
              <Measurement label="ZCR variance" value={activeResult.acousticEvidence.zcrVariance} />
            </section>
            <section className="reference-panel" aria-labelledby="reference-heading">
              <h2 id="reference-heading" className="result-section-title">Reference matches&nbsp; (top 3)</h2>
              {activeResult.referenceMatches.slice(0, 3).map((match) => <div className="reference-row" key={match.reference} data-testid={`reference-match-${match.reference.replaceAll(' ', '-').toLowerCase()}`}><span>{match.reference}</span><span className="measurement-value">{match.similarity.toFixed(2)}</span><span className="metric-track"><span className="metric-fill" style={{ width: `${Math.min(100, Math.max(0, match.similarity * 100))}%` }} /></span></div>)}
              <p className="provenance">Cosine similarity · held-out reference index</p>
            </section>
          </div>
        </div>

        <aside className="results-side">
          <section className="verdict-panel corner-frame" aria-labelledby="verdict-heading">
            <div className="panel-heading"><h2 id="verdict-heading">Verdict</h2><span className="panel-state">Model agreement <span className="status-dot" style={{ width: 7, height: 7, margin: '0 0 0 6px' }} /></span></div>
            <div className="verdict-status"><span className={`verdict-word ${activeResult.verdict.toLowerCase()}`} data-testid="text-verdict">{activeResult.verdict.toUpperCase()}</span></div>
            <p className="verdict-copy">
              {activeResult.verdict === 'Human'
                ? 'Both models classify the acoustic features as natural human speech.'
                : activeResult.verdict === 'AI'
                ? 'Synthetic acoustic artifacts detected across model features.'
                : 'Models returned conflicting scores; origin remains unconfirmed.'}
            </p>
          </section>
          <section className="side-panel" aria-labelledby="details-heading">
            <h2 id="details-heading" className="side-heading">Audio details</h2>
            <dl>
              <Detail label="Duration" value={duration ? `${duration.toFixed(1)} seconds` : 'Not reported'} />
              <Detail label="Sample rate" value={activeSelection.sampleRate ? `${activeSelection.sampleRate.toLocaleString()} Hz` : 'Not reported'} />
              <Detail label="Channels" value={activeSelection.channels ? (activeSelection.channels === 1 ? 'Mono' : `${activeSelection.channels} channels`) : 'Not reported'} />
              <Detail label="File type" value={activeSelection.type} />
              <Detail label="File size" value={formatBytes(activeSelection.size)} />
            </dl>
          </section>
          <section className="side-panel" aria-labelledby="reliability-heading">
            <h2 id="reliability-heading" className="side-heading">Reliability &amp; limitations</h2>
            <dl>
              <Detail label="Analysis quality" value={activeResult.reliability.analysisQuality} />
              <Detail label="Audio condition" value={activeResult.reliability.audioCondition} />
              <Detail label="Reliability" value={activeResult.reliability.reliability} />
            </dl>
            <div className="limitation">{activeResult.reliability.limitation}</div>
          </section>
          <div className="micro-label" style={{ marginTop: 15 }}>{activeResult.degraded ? 'Single-signal mode' : 'Dual-signal ensemble active'}</div>
        </aside>
      </div>
      <footer className="results-footer"><span>VAANI v2.0</span><span className="thin-rule" /><span>VOICE AUTHENTICITY ANALYSIS</span></footer>
    </main>
  );
}

function SignalBlock({ title, note, value }: { title: string; note: string; value: number }) {
  const percent = Math.min(100, Math.max(0, value * 100));
  return (
    <div className="signal-block" data-testid={`signal-${title.toLowerCase().replaceAll(' ', '-')}`}>
      <span className="signal-name">{title}</span>
      <span className="signal-note">{note}</span>
      <span className="signal-value">{value.toFixed(2)}</span>
      <span className="metric-track"><span className="metric-fill" style={{ width: `${percent}%` }} /></span>
    </div>
  );
}

function Measurement({ label, value }: { label: string; value: number }) {
  const displayVal = value > 999 ? (value / 1000).toFixed(1) + 'k' : value > 10 ? value.toFixed(0) : value.toFixed(2);
  const barPercent = Math.min(100, Math.max(4, value <= 1 ? value * 100 : Math.min(100, (Math.log10(value + 1) / 6) * 100)));
  return (
    <div className="measurement-row" data-testid={`measurement-${label.toLowerCase().replaceAll(' ', '-')}`}>
      <span>{label}</span>
      <span className="measurement-value">{displayVal}</span>
      <span className="metric-track"><span className="metric-fill" style={{ width: `${barPercent}%` }} /></span>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="detail-row"><dt>{label}</dt><dd>{value}</dd></div>;
}

function Router({
  selection,
  result,
  setResult,
  onSelect,
}: {
  selection: AudioSelection | null;
  result: DemoResult | null;
  setResult: (result: DemoResult) => void;
  onSelect: (selection: AudioSelection) => void;
}) {
  return (
    <ErrorBoundary resetKey={window.location.pathname}>
      <Switch>
        <Route path="/"><Home onSelect={onSelect} /></Route>
        <Route path="/analysis"><Analysis selection={selection} onCompleted={setResult} /></Route>
        <Route path="/results"><Results selection={selection} result={result} /></Route>
        <Route component={NotFound} />
      </Switch>
    </ErrorBoundary>
  );
}

function Application() {
  const [selection, setSelection] = useState<AudioSelection | null>(null);
  const [analysisResult, setAnalysisResult] = useState<DemoResult | null>(null);
  const [, setLocation] = useLocation();

  const selectAndAnalyze = useCallback((nextSelection: AudioSelection) => {
    setSelection((previous) => {
      if (previous?.url) URL.revokeObjectURL(previous.url);
      return nextSelection;
    });
    setAnalysisResult(null);
    setLocation('/analysis');
  }, [setLocation]);

  return (
    <Router
      selection={selection}
      result={analysisResult}
      setResult={setAnalysisResult}
      onSelect={selectAndAnalyze}
    />
  );
}

function App() {
  return <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}><Application /></WouterRouter>;
}

export default App;