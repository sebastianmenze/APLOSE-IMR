# APLOSE Audio Processor — API Reference

## Package contents

| Module | Main export | Purpose |
|--------|-------------|---------|
| `generator.py` | `AploseAudioProcessor` | Spectrogram generation and PNG/NetCDF output |
| `audio_processor.py` | `AudioProcessor` | Low-level audio resampling and snippet creation |
| `cli.py` | `main()` | Command-line entry point |

---

## `AploseAudioProcessor`

High-level processor. Takes one or more audio files, optionally resamples and splits them into snippets, then generates spectrograms in data-PNG+JSON format (default) or NetCDF format.

### Constructor

```python
AploseAudioProcessor(
    fft_sizes: int | list[int] = 2048,
    window: str = 'hann',
    hop_length_factor: float = 0.25,
    db_ref: float = 1.0,
    db_fullscale: float | None = None,
    normalize_audio: bool = False,
    datetime_format: str = "%Y_%m_%d_%H_%M_%S",
    target_sample_rate: int | None = None,
    snippet_duration: float | None = None,
    snippet_overlap: float = 0.0,
    filename_prefix: str | None = None,
    generate_data_png: bool = True,
    data_png_max_freq_bins: int = 1000,
    data_png_max_time_bins: int = 1000,
    data_png_freq_scale: str = 'log',
    max_duration: float | None = None,
    num_workers: int = 1,
    min_frequency: float | None = None,
    time_offset: float = 0.0,
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fft_sizes` | `int` or `list[int]` | `2048` | FFT size(s). Pass a list to generate one spectrogram per FFT size. |
| `window` | `str` | `'hann'` | Window function applied before FFT. One of `'hann'`, `'hamming'`, `'blackman'`. |
| `hop_length_factor` | `float` | `0.25` | Hop length expressed as a fraction of the FFT size (e.g. `0.25` → 25 % overlap). |
| `db_ref` | `float` | `1.0` | Reference amplitude for dB conversion (`20 * log10(amplitude / db_ref)`). Ignored when `db_fullscale` is set. |
| `db_fullscale` | `float \| None` | `None` | dB re 1 µPa that corresponds to digital full scale (maximum WAV value). When set the output is calibrated to dB re 1 µPa and takes precedence over `db_ref`. |
| `normalize_audio` | `bool` | `False` | If `True`, divide each audio segment by its mean absolute value before computing the spectrogram. |
| `datetime_format` | `str` | `"%Y_%m_%d_%H_%M_%S"` | `strptime` format used to parse the start timestamp from filenames. |
| `target_sample_rate` | `int \| None` | `None` | Resample audio to this rate (Hz) before processing. `None` keeps the original rate. |
| `snippet_duration` | `float \| None` | `None` | Duration in seconds of each output snippet. `None` keeps each file whole. |
| `snippet_overlap` | `float` | `0.0` | Overlap between consecutive snippets in seconds. |
| `filename_prefix` | `str \| None` | `None` | String prepended to every output filename. |
| `generate_data_png` | `bool` | `True` | Generate 16-bit grayscale PNG + JSON metadata pairs (recommended for APLOSE). |
| `data_png_max_freq_bins` | `int` | `1000` | Maximum number of frequency rows in the output PNG. Excess rows are resampled. |
| `data_png_max_time_bins` | `int` | `1000` | Maximum number of time columns in the output PNG. Excess columns are resampled. |
| `data_png_freq_scale` | `str` | `'log'` | Frequency axis scale used when resampling the PNG. One of `'log'`, `'linear'`. |
| `max_duration` | `float \| None` | `None` | Maximum seconds to read from each file. Truncates the file after this point. |
| `num_workers` | `int` | `1` | Number of parallel worker threads used when processing a folder. |
| `min_frequency` | `float \| None` | `None` | Discard spectrogram rows below this frequency (Hz). `None` keeps all frequencies. |
| `time_offset` | `float` | `0.0` | Seconds to skip at the beginning of each file before any other processing. |

---

### `process_folder`

```python
process_folder(
    input_folder: str,
    output_folder: str,
    audio_extensions: list[str] | None = None,
    preserve_timestamps: bool = True,
    datetime_format: str | None = None,
) -> dict[str, list[str]]
```

Process all audio files found in `input_folder`.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_folder` | `str` | — | Path to directory containing audio files. |
| `output_folder` | `str` | — | Directory where output files are written (created if absent). |
| `audio_extensions` | `list[str] \| None` | `['.wav', '.WAV']` | File extensions to include. |
| `preserve_timestamps` | `bool` | `True` | Adjust snippet filenames to reflect their real start timestamp. |
| `datetime_format` | `str \| None` | `None` | Override the instance-level `datetime_format` for this call. |

#### Returns

```python
{
    'wav_files': [str, ...],   # paths to output WAV files
    'png_files': [str, ...],   # paths to output PNG files (when generate_data_png=True)
}
```

---

### `process_file_list`

```python
process_file_list(
    input_list: list[str],
    output_folder: str,
    audio_extensions: list[str] | None = None,
    preserve_timestamps: bool = True,
    datetime_format: str | None = None,
) -> dict[str, list[str]]
```

Process an explicit list of audio file paths. Accepts the same parameters and returns the same structure as `process_folder`.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_list` | `list[str]` | — | List of absolute or relative paths to audio files. |
| `output_folder` | `str` | — | Output directory. |
| `audio_extensions` | `list[str] \| None` | `['.wav', '.WAV']` | Only these extensions are processed; others are silently skipped. |
| `preserve_timestamps` | `bool` | `True` | Adjust snippet filenames to reflect their real start timestamp. |
| `datetime_format` | `str \| None` | `None` | Override the instance-level `datetime_format` for this call. |

#### Returns

Same structure as `process_folder`.

---

### `process_single_file`

```python
process_single_file(
    input_file: str,
    output_folder: str,
    preserve_timestamps: bool = True,
    datetime_format: str | None = None,
) -> dict[str, list[str]]
```

Process a single audio file.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_file` | `str` | — | Path to the audio file. |
| `output_folder` | `str` | — | Output directory. |
| `preserve_timestamps` | `bool` | `True` | Adjust snippet filenames to reflect their real start timestamp. |
| `datetime_format` | `str \| None` | `None` | Override the instance-level `datetime_format` for this call. |

#### Returns

Same structure as `process_folder`.

---

### `_calculate_spectrogram` *(internal)*

```python
_calculate_spectrogram(
    audio: np.ndarray,
    sample_rate: int,
    nfft: int,
    hop_length: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]
```

Compute a Short-Time Fourier Transform spectrogram from a 1-D audio array.

Applies `normalize_audio` (divide by mean absolute value) when the instance flag is set, then runs STFT with the configured window function, and converts the result to dB using `db_ref` or `db_fullscale`.

#### Returns

`(spectrogram_db, frequencies, times)`

| Value | Shape | Unit |
|-------|-------|------|
| `spectrogram_db` | `(n_freq, n_time)` | dB |
| `frequencies` | `(n_freq,)` | Hz |
| `times` | `(n_time,)` | seconds |

---

### `_create_data_png_with_metadata` *(internal)*

```python
_create_data_png_with_metadata(
    wav_path: str,
    spec_data: np.ndarray,
    freqs: np.ndarray,
    times: np.ndarray,
    sample_rate: int,
    nfft: int,
    hop_length: int,
    metadata: dict,
    max_freq_bins: int = 1000,
    max_time_bins: int = 1000,
    freq_scale: str = 'log',
) -> tuple[str, str]
```

Encode a spectrogram array as a 16-bit grayscale PNG alongside a JSON sidecar file. The PNG stores intensity values normalised to the `[0, 65535]` range; the JSON stores `db_min`, `db_max`, timestamps, frequency bounds, and calibration metadata required to reconstruct absolute dB values.

Spectrogram data is resampled to `(max_freq_bins, max_time_bins)` before encoding. `freq_scale='log'` applies logarithmic resampling on the frequency axis.

#### Returns

`(png_path, json_path)` — absolute paths to the written files.

---

### `_create_data_pngs_for_all_fft_sizes` *(internal)*

```python
_create_data_pngs_for_all_fft_sizes(
    wav_path: str,
    metadata: dict,
) -> list[tuple[str, str]]
```

Convenience wrapper that calls `_create_data_png_with_metadata` for every FFT size in `self.fft_sizes`.

#### Returns

List of `(png_path, json_path)` tuples, one per FFT size.

---

### `_parse_datetime` *(internal)*

```python
_parse_datetime(
    filename: str,
    duration: float,
) -> tuple[datetime, datetime]
```

Extract a start timestamp from `filename` using the compiled regex derived from `datetime_format`. Computes the end timestamp by adding `duration` seconds.

#### Returns

`(begin_datetime, end_datetime)` as timezone-aware `datetime` objects (UTC).

---

### `_datetime_format_to_regex` *(internal)*

```python
_datetime_format_to_regex(datetime_format: str) -> str
```

Convert a `strptime` format string (e.g. `"%Y_%m_%d_%H_%M_%S"`) into a regex pattern that can match the corresponding substring in a filename.

#### Returns

Regex pattern string.

---

## `AudioProcessor`

Low-level helper used internally by `AploseAudioProcessor`. Can also be used standalone when only resampling or snippet creation is needed (without spectrogram generation).

### Constructor

```python
AudioProcessor(
    target_sample_rate: int | None = None,
    snippet_duration: float | None = None,
    overlap: float = 0.0,
    filename_prefix: str | None = None,
    max_duration: float | None = None,
    datetime_format: str | None = None,
    time_offset: float = 0.0,
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_sample_rate` | `int \| None` | `None` | Resample to this rate. `None` keeps original. |
| `snippet_duration` | `float \| None` | `None` | Snippet length in seconds. `None` keeps file whole. |
| `overlap` | `float` | `0.0` | Overlap between consecutive snippets in seconds. |
| `filename_prefix` | `str \| None` | `None` | Prefix prepended to output filenames. |
| `max_duration` | `float \| None` | `None` | Truncate files longer than this (seconds). |
| `datetime_format` | `str \| None` | `None` | `strptime` format for timestamp parsing. |
| `time_offset` | `float` | `0.0` | Seconds to skip at the start of each file. |

---

### `process_audio_file`

```python
process_audio_file(
    input_path: str,
    output_dir: str,
    preserve_timestamps: bool = True,
) -> list[tuple[str, dict]]
```

Resample and/or split a single audio file into snippets.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_path` | `str` | — | Path to the input WAV file. |
| `output_dir` | `str` | — | Directory where output WAV files are written. |
| `preserve_timestamps` | `bool` | `True` | Parse the start timestamp from the filename and adjust each snippet's filename accordingly. |

#### Returns

```python
[
    (output_path: str, metadata: dict),
    ...
]
```

`metadata` keys: `begin` (ISO timestamp str), `end` (ISO timestamp str), `sample_rate` (int), `duration` (float).

---

### `_resample` *(internal)*

```python
_resample(
    audio: np.ndarray,
    original_sr: int,
    target_sr: int,
) -> np.ndarray
```

Resample `audio` from `original_sr` to `target_sr` using scipy sinc interpolation.

#### Returns

Resampled audio array.

---

### `_create_snippets` *(internal)*

```python
_create_snippets(
    audio: np.ndarray,
    sample_rate: int,
    base_name: str,
    output_dir: str,
    preserve_timestamps: bool,
    base_time_offset: float = 0.0,
) -> list[tuple[str, dict]]
```

Split `audio` into fixed-length snippets, write each as a WAV file, and return path + metadata tuples.

---

### `_generate_snippet_filename` *(internal)*

```python
_generate_snippet_filename(
    base_name: str,
    snippet_idx: int,
    time_offset: float,
) -> str
```

Derive the output filename for snippet number `snippet_idx`. If a timestamp can be parsed from `base_name`, the filename is the adjusted timestamp; otherwise an index suffix is appended.

---

### `_datetime_format_to_regex` *(internal)*

```python
_datetime_format_to_regex(datetime_format: str) -> str
```

Same as `AploseAudioProcessor._datetime_format_to_regex`. Converts a `strptime` format string to a regex pattern.

---

## CLI entry point

### `main`

```python
# aplose_audio_processor/cli.py
def main() -> int
```

Parses command-line arguments and delegates to `AploseAudioProcessor`. Returns `0` on success, `1` on error. Registered as the `aplose-audio-processor` console script.

### `parse_fft_sizes`

```python
def parse_fft_sizes(fft_str: str) -> list[int]
```

Parse a comma-separated string of FFT sizes (e.g. `"1024,2048,4096"`) into a list of integers. Raises `argparse.ArgumentTypeError` on invalid input.

---

## Data formats

### Data PNG + JSON (default output)

Each spectrogram is stored as a matched pair:

```
recording_2024_01_15_08_30_00_fft2048_data.png   ← 16-bit grayscale image
recording_2024_01_15_08_30_00_fft2048_data.json  ← sidecar metadata
```

**PNG encoding**
Pixel value = `round((db - db_min) / (db_max - db_min) * 65535)`, clamped to `[0, 65535]`.

**JSON structure**

```json
{
  "temporal": { "begin": "2024-01-15T08:30:00Z", "end": "2024-01-15T08:31:00Z" },
  "audio": { "sample_rate": 48000, "duration": 60, "filename": "recording_….wav" },
  "analysis": { "nfft": 2048, "hop_length": 512, "normalize_audio": false },
  "spectrogram": {
    "n_times": 1000, "n_frequencies": 1000,
    "frequency_min": 0.0, "frequency_max": 24000.0
  },
  "encoding": { "db_min": -80.0, "db_max": 20.0 },
  "calibration": { "db_fullscale": 180.0 }
}
```

`calibration.db_fullscale` is only present when `--db-fullscale` was supplied; otherwise `calibration.db_ref` is written.

### Audio normalization

When `normalize_audio=True` (CLI flag `--normalize-audio`), the audio segment is divided by its mean absolute value before the STFT is computed:

```python
audio = audio / np.mean(np.abs(audio))
```

This equalises relative loudness across recordings but does **not** produce a fixed amplitude range. Use `db_fullscale` for calibrated absolute levels.
