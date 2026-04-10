import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { IonSpinner } from '@ionic/react';
import styles from './styles.module.scss';
import { DataPNGViewer } from './DataPNGViewer';

interface Analysis {
  fft: number;
  json: string;
  png: string | null;
}

interface Recording {
  id: string;
  wav: string;
  timestamp: string;
  analyses: Analysis[];
}

interface ExampleFilesResponse {
  recordings: Recording[];
  basePath: string;
  message?: string;
}

export const SpectrogramExamplePage: React.FC = () => {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [selectedRecordingIndex, setSelectedRecordingIndex] = useState(0);
  const [selectedFftIndex, setSelectedFftIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [basePath, setBasePath] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/netcdf/list-example-files/');
        if (!response.ok) throw new Error('Failed to fetch file list');
        const data: ExampleFilesResponse = await response.json();
        if (data.recordings && data.recordings.length > 0) {
          setRecordings(data.recordings);
          setBasePath(data.basePath);
        } else {
          setMessage(data.message || 'No spectrogram files found in the example folder.');
        }
      } catch (e) {
        console.error('Error fetching files:', e);
        setMessage('Could not load example spectrograms.');
      } finally {
        setLoading(false);
      }
    };
    fetchFiles();
  }, []);

  // Current selected recording and analysis
  const selectedRecording = recordings[selectedRecordingIndex];
  const selectedAnalysis = selectedRecording?.analyses[selectedFftIndex];

  // Reset FFT index when recording changes
  useEffect(() => {
    setSelectedFftIndex(0);
  }, [selectedRecordingIndex]);

  // Navigation handlers
  const handlePrevious = useCallback(() => {
    if (selectedRecordingIndex > 0) {
      setSelectedRecordingIndex(selectedRecordingIndex - 1);
    }
  }, [selectedRecordingIndex]);

  const handleNext = useCallback(() => {
    if (selectedRecordingIndex < recordings.length - 1) {
      setSelectedRecordingIndex(selectedRecordingIndex + 1);
    }
  }, [selectedRecordingIndex, recordings.length]);

  // FFT options for dropdown
  const fftOptions = useMemo(() => {
    if (!selectedRecording) return [];
    return selectedRecording.analyses.map((a, idx) => ({
      value: idx,
      label: `nfft: ${a.fft}`,
      fft: a.fft,
    }));
  }, [selectedRecording]);

  if (loading) {
    return (
      <div className={styles.pageContainer}>
        <div className={styles.loadingContainer}>
          <IonSpinner />
          <p>Loading spectrograms...</p>
        </div>
      </div>
    );
  }

  if (message || recordings.length === 0) {
    return (
      <div className={styles.pageContainer}>
        <div className={styles.exampleContainer}>
          <div className={styles.header}>
            <h1>Spectrogram Example</h1>
            <p>{message || 'No spectrogram files found.'}</p>
            <p className={styles.note}>
              Place PNG/JSON spectrogram files in{' '}
              <code>volumes/datawork/dataset/example/</code> to view them here.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.pageContainer}>
      <div className={styles.viewerWrapper}>
        {recordings.length > 1 && (
          <div className={styles.recordingSelector}>
            <label>Recording:</label>
            <select
              value={selectedRecordingIndex}
              onChange={(e) => setSelectedRecordingIndex(parseInt(e.target.value))}
            >
              {recordings.map((rec, idx) => (
                <option key={rec.id} value={idx}>
                  {rec.timestamp || rec.id}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedRecording && selectedAnalysis && (
          <DataPNGViewer
            jsonPath={selectedAnalysis.json}
            basePath={basePath}
            wavFile={selectedRecording.wav}
            fftOptions={fftOptions}
            selectedFftIndex={selectedFftIndex}
            onFftChange={setSelectedFftIndex}
            onPrevious={handlePrevious}
            onNext={handleNext}
            hasPrevious={selectedRecordingIndex > 0}
            hasNext={selectedRecordingIndex < recordings.length - 1}
          />
        )}
      </div>
    </div>
  );
}

export default SpectrogramExamplePage;
