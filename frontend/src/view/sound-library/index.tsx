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
 * Displays audio files from the sound library folder as thumbnails.
 * Click on a thumbnail to view the full spectrogram.
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

  // Handle file selection from thumbnail
  const handleFileSelect = useCallback((index: number) => {
    setSelectedFileIndex(index);
  }, []);

  // Handle back to thumbnails
  const handleBack = useCallback(() => {
    setSelectedFileIndex(null);
  }, []);

  // Get thumbnail URL for a file (use first analysis PNG)
  const getThumbnailUrl = useCallback((file: SoundFile) => {
    const firstAnalysis = file.analyses[0];
    if (firstAnalysis?.json) {
      // Derive PNG from JSON filename
      const pngFilename = firstAnalysis.json.replace(/\.json$/, '.png');
      return `${basePath}${encodeURIComponent(pngFilename)}`;
    }
    return null;
  }, [basePath]);

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

  // Show full viewer when a file is selected
  if (selectedFile && selectedAnalysis) {
    return (
      <div className={styles.pageContainer}>
        <div className={styles.viewerFullPage}>
          <SoundLibraryViewer
            jsonPath={selectedAnalysis.json}
            basePath={basePath}
            wavFile={selectedFile.filename}
            fftOptions={fftOptions}
            selectedFftIndex={selectedFftIndex}
            onFftChange={setSelectedFftIndex}
            onBack={handleBack}
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
        </div>
      </div>
    );
  }

  // Show thumbnail grid
  return (
    <div className={styles.pageContainer}>
      <div className={styles.thumbnailPage}>
        <h1 className={styles.pageTitle}>Sound Library</h1>
        <div className={styles.thumbnailGrid}>
          {files.map((file, index) => {
            const thumbnailUrl = getThumbnailUrl(file);
            return (
              <div
                key={file.filename || file.baseName}
                className={styles.thumbnailCard}
                onClick={() => handleFileSelect(index)}
              >
                <div className={styles.thumbnailImage}>
                  {thumbnailUrl ? (
                    <img src={thumbnailUrl} alt={file.prefix} />
                  ) : (
                    <div className={styles.noImage}>No preview</div>
                  )}
                </div>
                <div className={styles.thumbnailTitle}>{file.prefix}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default SoundLibraryPage;
