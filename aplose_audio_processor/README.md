# APLOSE Audio Processor

A Python package to generate APLOSE-compatible spectrogram files from audio files.

## Features

- **Audio Resampling**: Convert audio to different sample rates
- **Audio Snippets**: Split long recordings into shorter snippets with configurable overlap
- **Time Offset / Max Duration**: Skip leading seconds or cap file length before processing
- **Multi-FFT Support**: Generate spectrograms with multiple FFT sizes
- **Data PNG Export**: 16-bit grayscale PNG + JSON metadata for fast browser display
- **Calibrated Output**: Absolute dB re 1 µPa levels via `--db-fullscale`
- **Batch Processing**: Process entire folders with optional parallel workers
- **APLOSE Compatible**: Outputs files that work seamlessly with APLOSE

## Installation

### From Source

```bash
cd aplose_audio_processor
pip install -e .
```

### Requirements

- Python >= 3.8
- numpy >= 1.20.0
- scipy >= 1.7.0
- xarray >= 2023.0.0
- netcdf4 >= 1.6.0
- soundfile >= 0.12.0

## Usage

### Command Line Interface

The package provides a command-line tool `aplose-audio-processor`:

#### Basic Usage

```bash
aplose-audio-processor -i /path/to/audio_files/ -o /path/to/output/
```

#### Resample Audio

```bash
aplose-audio-processor -i audio_files/ -o output/ --sample-rate 48000
```

#### Skip Leading Noise / Limit Duration

Skip the first 2 seconds of each file and use at most 60 seconds:

```bash
aplose-audio-processor -i audio_files/ -o output/ \
  --time-offset 2.0 --max-duration 60
```

#### Create Audio Snippets

Split 10-minute recordings into 1-minute snippets:

```bash
aplose-audio-processor -i audio_files/ -o output/ --snippet-duration 60
```

#### Snippets with Overlap

```bash
aplose-audio-processor -i audio_files/ -o output/ \
  --snippet-duration 60 --overlap 10
```

#### Multi-FFT Spectrograms

```bash
aplose-audio-processor -i audio_files/ -o output/ \
  --fft-sizes 1024,2048,4096
```

#### Calibrated Output (dB re 1 µPa)

```bash
aplose-audio-processor -i audio_files/ -o output/ \
  --db-fullscale 180.0
```

#### Normalize Audio

Divide each file's audio by its mean absolute value before computing the spectrogram:

```bash
aplose-audio-processor -i audio_files/ -o output/ --normalize-audio
```

#### Complete Example

```bash
aplose-audio-processor -i audio_files/ -o output/ \
  --sample-rate 48000 \
  --snippet-duration 60 \
  --overlap 10 \
  --fft-sizes 1024,2048,4096 \
  --window hann \
  --workers 4
```

### Python API

#### Basic Example

```python
from aplose_audio_processor import AploseAudioProcessor

processor = AploseAudioProcessor(fft_sizes=2048)
results = processor.process_folder(
    input_folder='audio_files/',
    output_folder='output/'
)
print(f"Generated {len(results['wav_files'])} WAV files")
print(f"Generated {len(results['png_files'])} PNG files")
```

#### Advanced Example with Resampling and Snippets

```python
from aplose_audio_processor import AploseAudioProcessor

processor = AploseAudioProcessor(
    fft_sizes=[1024, 2048, 4096],
    window='hann',
    hop_length_factor=0.25,
    target_sample_rate=48000,
    snippet_duration=60.0,
    snippet_overlap=10.0
)
results = processor.process_folder(
    input_folder='long_recordings/',
    output_folder='processed_snippets/',
    preserve_timestamps=True
)
```

#### Process Single File

```python
from aplose_audio_processor import AploseAudioProcessor

processor = AploseAudioProcessor(fft_sizes=2048, target_sample_rate=48000)
results = processor.process_single_file(
    input_file='recording.wav',
    output_folder='output/'
)
```

## Output Format

### WAV Files

Processed audio files (resampled and/or split into snippets):
- `recording_2024_01_15_08_30_00.wav`
- `recording_2024_01_15_08_31_00.wav`

### Data PNG + JSON Files (default)

Each spectrogram is stored as a pair of files:
- `recording_2024_01_15_08_30_00_fft2048_data.png` — 16-bit grayscale image
- `recording_2024_01_15_08_30_00_fft2048_data.json` — metadata for dB reconstruction

The PNG pixels encode normalised spectrogram intensity; the JSON contains the
`db_min`/`db_max` range plus timing, frequency, and calibration metadata needed
to display the correct dB values in APLOSE.

### NetCDF Files (legacy / optional)

APLOSE-compatible NetCDF files with the same basename:
- `recording_2024_01_15_08_30_00.nc`

## File Naming

When creating snippets, timestamps are parsed from filenames and adjusted per snippet:

**Input:** `recording_2024_01_15_08_30_00.wav` (10 minutes)

**Output (60-second snippets):**
- `2024_01_15_08_30_00.wav` (0:00–1:00)
- `2024_01_15_08_31_00.wav` (1:00–2:00)
- `2024_01_15_08_32_00.wav` (2:00–3:00)

### Supported Datetime Formats

Default: `%Y_%m_%d_%H_%M_%S` → `2024_01_15_08_30_00`

Custom example:

```bash
aplose-audio-processor -i audio/ -o output/ --datetime-format "%Y%m%d_%H%M%S"
```

## CLI Options

### Input / Output

| Option | Description | Default |
|--------|-------------|---------|
| `-i, --input` | Input folder or single audio file | Required |
| `-o, --output` | Output folder | Required |
| `--extensions` | Comma-separated audio extensions | `.wav,.WAV` |

### Audio Processing

| Option | Description | Default |
|--------|-------------|---------|
| `--sample-rate` | Resample to this rate (Hz) | Original |
| `--time-offset` | Seconds to skip at the start of each file | `0.0` |
| `--max-duration` | Maximum seconds to use from each file | Full file |
| `--snippet-duration` | Split into snippets of this length (s) | No split |
| `--overlap` | Overlap between snippets (s) | `0.0` |
| `--filename-prefix` | Prefix added to all output filenames | None |
| `--no-preserve-timestamps` | Don't adjust timestamps in snippet filenames | Off |

### Spectrogram

| Option | Description | Default |
|--------|-------------|---------|
| `--fft-sizes` | Comma-separated FFT sizes | `2048` |
| `--window` | Window function (`hann`/`hamming`/`blackman`) | `hann` |
| `--hop-length-factor` | Hop length as fraction of FFT size | `0.25` |
| `--db-ref` | Reference value for dB conversion | `1.0` |
| `--db-fullscale` | dB re 1 µPa at digital full scale (overrides `--db-ref`) | None |
| `--normalize-audio` | Divide audio by its mean absolute value | Off |
| `--min-frequency` | Minimum frequency to include (Hz) | None |

### Data PNG Export

| Option | Description | Default |
|--------|-------------|---------|
| `--no-data-png` | Disable data PNG + JSON generation | Off |
| `--data-png-max-freq` | Max frequency bins in PNG | `1000` |
| `--data-png-max-time` | Max time bins in PNG | `1000` |
| `--data-png-freq-scale` | Frequency axis resampling (`log`/`linear`) | `log` |

### Other

| Option | Description | Default |
|--------|-------------|---------|
| `--datetime-format` | strptime format for parsing filename timestamps | `%Y_%m_%d_%H_%M_%S` |
| `--workers` | Number of parallel worker threads | `1` |

## Examples

### Example 1: Prepare Long Recordings for APLOSE

Split 1-hour whale recordings into 5-minute snippets:

```bash
aplose-audio-processor -i whale_recordings/ -o aplose_dataset/ \
  --snippet-duration 300 \
  --fft-sizes 1024,2048,4096
```

### Example 2: Downsample High Sample Rate Recordings

```bash
aplose-audio-processor -i high_res_audio/ -o downsampled/ \
  --sample-rate 48000 \
  --fft-sizes 2048
```

### Example 3: Overlapping Analysis Windows

```bash
aplose-audio-processor -i continuous_recordings/ -o overlapped/ \
  --snippet-duration 60 \
  --overlap 30 \
  --fft-sizes 2048
```

### Example 4: Skip Transient Noise at Recording Start

```bash
aplose-audio-processor -i field_recordings/ -o output/ \
  --time-offset 5.0 \
  --fft-sizes 4096
```

### Example 5: Parallel Processing

```bash
aplose-audio-processor -i large_folder/ -o output/ \
  --fft-sizes 2048,4096 \
  --workers 8
```

## Importing into APLOSE

After generating files, import them into APLOSE:

```bash
python manage.py import_simple_dataset <dataset_name>
```

See `API_REFERENCE.md` for the full Python API documentation.

## License

GNU General Public License v3.0 — part of the APLOSE project.

## Support

- GitHub Issues: https://github.com/Project-ODE/APLOSE-IMR/issues
