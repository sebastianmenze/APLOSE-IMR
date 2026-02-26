import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { IonSpinner } from '@ionic/react';
import styles from './styles.module.scss';
import { SoundLibraryViewer } from './SoundLibraryViewer';

interface Analysis {
  fft: number;
  json: string;
  png: string | null;
}

interface SoundFile {
  prefix: string;
  filename: string;
  baseName: string;
  analyses: Analysis[];
}

interface SoundLibraryResponse {
  files: SoundFile[];
  basePath: string;
  message?: string;
}

/**
 * Sound Library Page
 *
 * Displays audio files from the sound library folder.
 * Shows files grouped by prefix with spectrogram visualization.
 */
export const SoundLibraryPage: React.FC = () => {
  const [files, setFiles] = useState<SoundFile[]>([]);
  const [selectedFileIndex, setSelectedFileIndex] = useState<number | null>(null);
  const [selectedFftIndex, setSelectedFftIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [basePath, setBasePath] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Fetch file list on mount
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch('/api/netcdf/list-sound-library/');
        if (!response.ok) {
          throw new Error('Failed to fetch sound library');
        }
        const data: SoundLibraryResponse = await response.json();

        if (!data.files || data.files.length === 0) {
          setError(data.message || 'No files found in sound library');
        } else {
          setFiles(data.files);
          setBasePath(data.basePath);
        }
        setLoading(false);
      } catch (e) {
        console.error('Error fetching sound library:', e);
        setError('Failed to load sound library');
        setLoading(false);
      }
    };

    fetchFiles();
  }, []);

  // Current selected file and analysis
  const selectedFile = selectedFileIndex !== null ? files[selectedFileIndex] : null;
  const selectedAnalysis = selectedFile?.analyses[selectedFftIndex];

  // Reset FFT index when file changes
  useEffect(() => {
    setSelectedFftIndex(0);
  }, [selectedFileIndex]);

  // FFT options for dropdown
  const fftOptions = useMemo(() => {
    if (!selectedFile) return [];
    return selectedFile.analyses.map((a, idx) => ({
      value: idx,
      label: `nfft: ${a.fft}`,
      fft: a.fft,
    }));
  }, [selectedFile]);

  // Handle file selection
  const handleFileSelect = useCallback((index: number) => {
    setSelectedFileIndex(index);
  }, []);

  if (loading) {
    return (
      <div className={styles.pageContainer}>
        <div className={styles.loadingContainer}>
          <IonSpinner />
          <p>Loading sound library...</p>
        </div>
      </div>
    );
  }

  if (error && files.length === 0) {
    return (
      <div className={styles.pageContainer}>
        <div className={styles.errorContainer}>
          <h2>Sound Library</h2>
          <p>{error}</p>
          <p className={styles.helpText}>
            Place your spectrogram PNG/JSON files in:
            <code>volumes/datawork/dataset/sound_library/</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.pageContainer}>
      <div className={styles.contentWrapper}>
        {/* File List Panel */}
        <div className={styles.fileListPanel}>
          <h2>Sound Library</h2>
          <div className={styles.fileList}>
            {files.map((file, index) => (
              <button
                key={file.filename || file.baseName}
                className={`${styles.fileItem} ${selectedFileIndex === index ? styles.active : ''}`}
                onClick={() => handleFileSelect(index)}
              >
                {file.prefix}
              </button>
            ))}
          </div>
        </div>

        {/* Viewer Panel */}
        <div className={styles.viewerPanel}>
          {selectedFile && selectedAnalysis ? (
            <SoundLibraryViewer
              jsonPath={selectedAnalysis.json}
              basePath={basePath}
              wavFile={selectedFile.filename}
              fftOptions={fftOptions}
              selectedFftIndex={selectedFftIndex}
              onFftChange={setSelectedFftIndex}
              fileSelector={
                <select
                  value={selectedFileIndex ?? ''}
                  onChange={(e) => setSelectedFileIndex(parseInt(e.target.value))}
                  className={styles.fileDropdown}
                >
                  {files.map((file, idx) => (
                    <option key={file.filename || file.baseName} value={idx}>
                      {file.prefix}
                    </option>
                  ))}
                </select>
              }
            />
          ) : (
            <div className={styles.selectPrompt}>
              <p>Select a sound from the list to view its spectrogram</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SoundLibraryPage;
