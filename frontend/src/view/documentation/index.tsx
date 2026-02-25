import React from 'react';
import styles from './styles.module.scss';

/**
 * Documentation Page
 *
 * Comprehensive guide for using the APLOSE audio processing and annotation workflow.
 */
export const DocumentationPage: React.FC = () => {
  return (
    <div className={styles.documentationPage}>
      <div className={styles.container}>
        <header className={styles.header}>
          <h1>APLOSE Documentation</h1>
          <p className={styles.subtitle}>Audio Processing and Annotation Workflow Guide</p>
        </header>

        <nav className={styles.tableOfContents}>
          <h2>Table of Contents</h2>
          <ol>
            <li><a href="#overview">Overview</a></li>
            <li><a href="#preprocessing">Preprocessing Audio Data</a></li>
            <li><a href="#importing">Importing into APLOSE</a></li>
            <li><a href="#annotating">Annotating Spectrograms</a></li>
            <li><a href="#exporting">Exporting Annotations</a></li>
          </ol>
        </nav>

        <section id="overview" className={styles.section}>
          <h2>Overview</h2>
          <p>
            APLOSE (Annotation Platform for Ocean Sound Exploration) is a web-based tool for visualizing
            and annotating spectrograms from underwater acoustic recordings. The workflow consists of:
          </p>
          <ol>
            <li><strong>Preprocessing</strong>: Convert audio files to spectrogram data using the Python generator package</li>
            <li><strong>Importing</strong>: Load the processed dataset into APLOSE</li>
            <li><strong>Annotating</strong>: Create annotations on spectrograms using the web interface</li>
            <li><strong>Exporting</strong>: Download annotations in various formats for analysis</li>
          </ol>
        </section>

        <section id="preprocessing" className={styles.section}>
          <h2>Preprocessing Audio Data</h2>

          <h3>Installation</h3>
          <p>The audio processor package is located in the <code>examples/aplose_audio_processor/</code> folder.</p>
          <pre className={styles.codeBlock}>{`# Install required dependencies
pip install numpy scipy soundfile tqdm`}</pre>

          <h3>Basic Usage</h3>
          <p>Use the <code>AudioProcessor</code> class to process audio files into spectrogram data:</p>
          <pre className={styles.codeBlock}>{`from audio_processor import AudioProcessor

# Initialize processor with your settings
processor = AudioProcessor(
    input_folder="path/to/audio/files",
    output_folder="path/to/output",
    fft_sizes=[4096, 8192, 16384],      # Multiple FFT sizes for different resolutions
    snippet_duration=60,                  # Duration of each snippet in seconds
    snippet_overlap=0,                    # Overlap between snippets
    target_sample_rate=None,              # Resample if needed (None = keep original)
    datetime_format="%Y%m%d_%H%M%S",     # Format to parse datetime from filename
    normalize_audio=True,                 # Normalize audio before processing
    db_fullscale=None,                    # Optional: dB reference for calibration
)

# Process all files
processor.process_all_files()`}</pre>

          <h3>Datetime Format</h3>
          <p>
            The processor extracts recording timestamps from filenames. Common formats:
          </p>
          <ul>
            <li><code>%Y%m%d_%H%M%S</code> - e.g., <code>recording_20250130_223000.wav</code></li>
            <li><code>%Y_%m_%d_%H_%M_%S</code> - e.g., <code>recording_2025_01_30_22_30_00.wav</code></li>
            <li><code>%Y-%m-%d_%H-%M-%S</code> - e.g., <code>recording_2025-01-30_22-30-00.wav</code></li>
          </ul>

          <h3>Output Format</h3>
          <p>The processor generates two files for each spectrogram:</p>
          <ul>
            <li><strong>PNG file</strong>: 16-bit grayscale image containing the spectrogram power values</li>
            <li><strong>JSON file</strong>: Metadata including frequency range, time range, FFT settings, and calibration info</li>
          </ul>
          <pre className={styles.codeBlock}>{`# Example JSON metadata structure
{
  "format_version": 1,
  "png_file": "recording_2025_01_30_22_30_00_fft8192_data.png",
  "encoding": {
    "bit_depth": 16,
    "db_min": -120.0,
    "db_max": 0.0
  },
  "spectrogram": {
    "frequency_min": 10,
    "frequency_max": 24000,
    "frequency_scale": "log",
    "time_min": 0,
    "time_max": 60
  },
  "audio": {
    "sample_rate": 48000,
    "duration": 60,
    "filename": "recording_2025_01_30_22_30_00.wav"
  },
  "analysis": {
    "nfft": 8192,
    "hop_length": 4096,
    "window": "hann"
  },
  "temporal": {
    "begin": "2025-01-30T22:30:00",
    "end": "2025-01-30T22:31:00"
  }
}`}</pre>

          <h3>Generating Dataset Metadata</h3>
          <p>After processing, use the generator script to create the dataset configuration:</p>
          <pre className={styles.codeBlock}>{`from generator import SpectrogramMetadataGenerator

generator = SpectrogramMetadataGenerator(
    input_folder="path/to/processed/spectrograms",
    output_folder="path/to/dataset/output",
    dataset_name="My Acoustic Dataset",
    datetime_format="%Y_%m_%d_%H_%M_%S"  # Format used in output filenames
)

# Generate metadata files for APLOSE import
generator.generate()`}</pre>
        </section>

        <section id="importing" className={styles.section}>
          <h2>Importing into APLOSE</h2>

          <h3>Dataset Structure</h3>
          <p>Place your processed data in the following structure within <code>volumes/datawork/dataset/</code>:</p>
          <pre className={styles.codeBlock}>{`volumes/datawork/dataset/
  your_dataset_name/
    dataset.json           # Dataset configuration
    data/
      audio/
        original/
          original.json    # Audio file metadata
    processed/
      analysis_name/
        analysis_name.json # Spectrogram metadata`}</pre>

          <h3>Dataset Configuration (dataset.json)</h3>
          <pre className={styles.codeBlock}>{`{
  "name": "My Acoustic Dataset",
  "description": "Underwater recordings from location X",
  "files_type": "png",
  "start_date": "2025-01-01T00:00:00Z",
  "end_date": "2025-12-31T23:59:59Z",
  "audio_metadata_file": "data/audio/original/original.json"
}`}</pre>

          <h3>Import via Admin Interface</h3>
          <ol>
            <li>Log in to APLOSE as an administrator</li>
            <li>Navigate to <strong>Datasets</strong> in the left panel</li>
            <li>Click <strong>Import Dataset</strong></li>
            <li>Select your dataset folder from the dropdown</li>
            <li>Review the configuration and click <strong>Import</strong></li>
          </ol>

          <h3>Verify Import</h3>
          <p>
            After importing, the dataset will appear in the Datasets list. Click on it to view:
          </p>
          <ul>
            <li>Number of spectrograms</li>
            <li>Available FFT analyses</li>
            <li>Time range covered</li>
            <li>Audio file information</li>
          </ul>
        </section>

        <section id="annotating" className={styles.section}>
          <h2>Annotating Spectrograms</h2>

          <h3>Creating an Annotation Campaign</h3>
          <ol>
            <li>Go to <strong>Annotation Campaigns</strong></li>
            <li>Click <strong>New Campaign</strong></li>
            <li>Fill in campaign details:
              <ul>
                <li><strong>Name</strong>: Descriptive name for the campaign</li>
                <li><strong>Dataset</strong>: Select the imported dataset</li>
                <li><strong>Label Set</strong>: Choose or create annotation labels</li>
                <li><strong>Annotators</strong>: Assign users to the campaign</li>
              </ul>
            </li>
            <li>Click <strong>Create Campaign</strong></li>
          </ol>

          <h3>Annotation Interface</h3>
          <p>The spectrogram annotation interface provides:</p>

          <h4>Display Controls</h4>
          <ul>
            <li><strong>Y-Axis Scale</strong>: Switch between linear and logarithmic frequency scale</li>
            <li><strong>Colorscale</strong>: Choose from multiple color palettes (Viridis, Hot, Jet, etc.)</li>
            <li><strong>Intensity Range</strong>: Adjust min/max dB values with sliders</li>
            <li><strong>Analysis Selection</strong>: Switch between different FFT resolutions</li>
          </ul>

          <h4>Creating Annotations</h4>
          <ol>
            <li>Select a label from the label panel on the right</li>
            <li>Click and drag on the spectrogram to draw a bounding box</li>
            <li>The annotation will be saved automatically</li>
            <li>To edit, click on an existing annotation and resize or move it</li>
            <li>To delete, select the annotation and press Delete or use the delete button</li>
          </ol>

          <h4>Keyboard Shortcuts</h4>
          <table className={styles.shortcutTable}>
            <thead>
              <tr>
                <th>Key</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>Space</td><td>Play/Pause audio</td></tr>
              <tr><td>Arrow Left/Right</td><td>Navigate to previous/next spectrogram</td></tr>
              <tr><td>1-9</td><td>Select label by number</td></tr>
              <tr><td>Delete</td><td>Delete selected annotation</td></tr>
              <tr><td>Escape</td><td>Deselect annotation</td></tr>
            </tbody>
          </table>

          <h4>Audio Playback</h4>
          <p>
            Click anywhere on the spectrogram to seek to that time position. Use the play button
            or spacebar to start playback. A red vertical line indicates the current playback position.
          </p>
        </section>

        <section id="exporting" className={styles.section}>
          <h2>Exporting Annotations</h2>

          <h3>Export Options</h3>
          <p>Navigate to your annotation campaign and click <strong>Export</strong> to download annotations.</p>

          <h4>CSV Format</h4>
          <p>Standard tabular format with columns:</p>
          <pre className={styles.codeBlock}>{`filename,start_time,end_time,min_frequency,max_frequency,label,annotator,confidence
recording_001.wav,10.5,15.2,500,2000,whale_call,user1,0.95
recording_001.wav,22.1,24.8,1000,4000,dolphin_click,user1,0.87`}</pre>

          <h4>RAVEN Format</h4>
          <p>Compatible with Cornell Lab's Raven Pro software:</p>
          <pre className={styles.codeBlock}>{`Selection	View	Channel	Begin Time (s)	End Time (s)	Low Freq (Hz)	High Freq (Hz)	Annotation
1	Spectrogram	1	10.5	15.2	500	2000	whale_call
2	Spectrogram	1	22.1	24.8	1000	4000	dolphin_click`}</pre>

          <h4>JSON Format</h4>
          <p>Full annotation data with metadata:</p>
          <pre className={styles.codeBlock}>{`{
  "campaign": "My Campaign",
  "dataset": "My Dataset",
  "annotations": [
    {
      "id": 1,
      "spectrogram": "recording_001",
      "label": "whale_call",
      "start_time": 10.5,
      "end_time": 15.2,
      "min_frequency": 500,
      "max_frequency": 2000,
      "annotator": "user1",
      "created_at": "2025-01-30T10:00:00Z"
    }
  ]
}`}</pre>

          <h3>Bulk Export</h3>
          <p>
            For large datasets, use the <strong>Export All</strong> option to download all annotations
            across the entire campaign as a single file.
          </p>
        </section>

        <footer className={styles.footer}>
          <p>
            For additional help, visit the <a href="https://github.com/Project-OSmOSE/osmose-app" target="_blank" rel="noopener noreferrer">
            APLOSE GitHub repository</a> or contact the development team.
          </p>
        </footer>
      </div>
    </div>
  );
};

export default DocumentationPage;
