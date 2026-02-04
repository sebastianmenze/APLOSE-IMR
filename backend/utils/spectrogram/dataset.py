"""
Simple dataset structure for APLOSE

Reads a folder containing WAV files and corresponding spectrograms
(NetCDF or data PNG + JSON format)
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import xarray as xr
except ImportError:
    logger.warning("xarray not installed. Install with: pip install xarray netcdf4")
    xr = None

try:
    from PIL import Image
    import numpy as np
except ImportError:
    logger.warning("Pillow/numpy not installed for PNG support")
    Image = None
    np = None


class SpectrogramFile:
    """Represents a single spectrogram file in the dataset"""

    def __init__(self, netcdf_path: Path, wav_path: Optional[Path] = None, nfft: Optional[int] = None):
        """
        Initialize spectrogram file

        Args:
            netcdf_path: Path to NetCDF spectrogram file
            wav_path: Optional path to corresponding WAV file
            nfft: Optional FFT size to extract (for multi-FFT files)
        """
        self.netcdf_path = netcdf_path
        self.wav_path = wav_path
        self.nfft = nfft
        self._metadata = None
        self._ds = None

    @property
    def metadata(self) -> Dict:
        """Get metadata from NetCDF file without loading full data"""
        if self._metadata is None:
            self._metadata = self._read_metadata()
        return self._metadata

    def _read_metadata(self) -> Dict:
        """Read metadata from NetCDF file"""
        if xr is None:
            raise ImportError("xarray is required. Install with: pip install xarray netcdf4")

        try:
            with xr.open_dataset(self.netcdf_path) as ds:
                # Check if this is a multi-FFT file
                fft_sizes_str = ds.attrs.get('fft_sizes', '')
                is_multi_fft = bool(fft_sizes_str)

                if is_multi_fft and self.nfft:
                    # Extract metadata for specific FFT size
                    var_name = f'spectrogram_fft{self.nfft}'
                    time_coord = f'time_fft{self.nfft}'
                    freq_coord = f'frequency_fft{self.nfft}'

                    if var_name in ds.data_vars:
                        metadata = {
                            'begin': ds.attrs.get('begin', ''),
                            'end': ds.attrs.get('end', ''),
                            'sample_rate': ds.attrs.get('sample_rate', 0),
                            'duration': ds.attrs.get('duration', 0),
                            'nfft': self.nfft,
                            'hop_length': self._infer_hop_length(ds, time_coord, self.nfft),
                            'audio_file': ds.attrs.get('audio_file', ''),
                            'time_shape': len(ds.coords[time_coord]),
                            'frequency_shape': len(ds.coords[freq_coord]),
                            'frequency_min': float(ds.coords[freq_coord].min()),
                            'frequency_max': float(ds.coords[freq_coord].max()),
                        }
                    else:
                        logger.error(f"FFT size {self.nfft} not found in {self.netcdf_path}")
                        return {}
                else:
                    # Legacy single-FFT file format
                    metadata = {
                        'begin': ds.attrs.get('begin', ''),
                        'end': ds.attrs.get('end', ''),
                        'sample_rate': ds.attrs.get('sample_rate', 0),
                        'duration': ds.attrs.get('duration', 0),
                        'nfft': ds.attrs.get('nfft', 0),
                        'hop_length': ds.attrs.get('hop_length', 0),
                        'audio_file': ds.attrs.get('audio_file', ''),
                        'time_shape': len(ds.coords.get('time', [])),
                        'frequency_shape': len(ds.coords.get('frequency', [])),
                        'frequency_min': float(ds.coords.get('frequency', [0]).min()) if 'frequency' in ds.coords else 0,
                        'frequency_max': float(ds.coords.get('frequency', [0]).max()) if 'frequency' in ds.coords else 0,
                    }

            return metadata
        except Exception as e:
            logger.error(f"Failed to read metadata from {self.netcdf_path}: {e}")
            return {}

    def _infer_hop_length(self, ds: xr.Dataset, time_coord: str, nfft: int) -> int:
        """Infer hop length from time coordinate spacing"""
        try:
            sample_rate = ds.attrs.get('sample_rate', 48000)
            time_vals = ds.coords[time_coord].values
            if len(time_vals) > 1:
                time_step = float(time_vals[1] - time_vals[0])
                hop_length = int(time_step * sample_rate)
                return hop_length
            return nfft // 4  # Default guess
        except Exception:
            return nfft // 4  # Default guess

    def load_dataset(self) -> Optional[xr.Dataset]:
        """Load the full xarray dataset"""
        if xr is None:
            raise ImportError("xarray is required. Install with: pip install xarray netcdf4")

        if self._ds is None:
            try:
                full_ds = xr.open_dataset(self.netcdf_path)

                # Check if this is a multi-FFT file and we have a specific nfft
                fft_sizes_str = full_ds.attrs.get('fft_sizes', '')
                if fft_sizes_str and self.nfft:
                    # Extract only the relevant spectrogram for this FFT size
                    var_name = f'spectrogram_fft{self.nfft}'
                    time_coord = f'time_fft{self.nfft}'
                    freq_coord = f'frequency_fft{self.nfft}'

                    if var_name in full_ds.data_vars:
                        # Create a new dataset with standard names
                        self._ds = xr.Dataset(
                            {
                                'spectrogram': full_ds[var_name].rename({
                                    time_coord: 'time',
                                    freq_coord: 'frequency'
                                })
                            },
                            attrs=full_ds.attrs.copy()
                        )
                        # Update attrs to reflect this specific FFT
                        self._ds.attrs['nfft'] = self.nfft
                        self._ds.attrs['hop_length'] = self._infer_hop_length(full_ds, time_coord, self.nfft)
                    else:
                        logger.error(f"FFT size {self.nfft} not found in {self.netcdf_path}")
                        return None
                else:
                    # Legacy single-FFT file
                    self._ds = full_ds

            except Exception as e:
                logger.error(f"Failed to load dataset from {self.netcdf_path}: {e}")
                return None
        return self._ds

    def close(self):
        """Close the dataset if it's open"""
        if self._ds is not None:
            self._ds.close()
            self._ds = None

    def __repr__(self):
        return f"SpectrogramFile(netcdf={self.netcdf_path.name}, wav={self.wav_path.name if self.wav_path else 'None'})"


class DataPngSpectrogramFile:
    """Represents a data PNG + JSON spectrogram file"""

    def __init__(self, json_path: Path, wav_path: Optional[Path] = None):
        """
        Initialize data PNG spectrogram file

        Args:
            json_path: Path to JSON metadata file (PNG path is derived from it)
            wav_path: Optional path to corresponding WAV file
        """
        self.json_path = json_path
        self.png_path = None
        self.wav_path = wav_path
        self.nfft = None
        self._metadata = None
        self._json_data = None

    @property
    def metadata(self) -> Dict:
        """Get metadata from JSON file"""
        if self._metadata is None:
            self._metadata = self._read_metadata()
        return self._metadata

    @property
    def json_data(self) -> Dict:
        """Get raw JSON data"""
        if self._json_data is None:
            self._load_json()
        return self._json_data

    def _load_json(self):
        """Load JSON metadata file"""
        try:
            with open(self.json_path, 'r') as f:
                self._json_data = json.load(f)

            # Set PNG path from JSON
            png_filename = self._json_data.get('png_file', '')
            if png_filename:
                self.png_path = self.json_path.parent / png_filename
            else:
                # Derive from JSON filename
                self.png_path = self.json_path.with_suffix('.png')

            # Extract FFT size from JSON or filename
            if 'analysis' in self._json_data:
                self.nfft = self._json_data['analysis'].get('nfft')

        except Exception as e:
            logger.error(f"Failed to load JSON from {self.json_path}: {e}")
            self._json_data = {}

    def _read_metadata(self) -> Dict:
        """Read and convert metadata to standard format"""
        if self._json_data is None:
            self._load_json()

        if not self._json_data:
            return {}

        try:
            json_data = self._json_data

            # Convert to standard metadata format (compatible with NetCDF)
            metadata = {
                'begin': json_data.get('temporal', {}).get('begin', ''),
                'end': json_data.get('temporal', {}).get('end', ''),
                'sample_rate': json_data.get('audio', {}).get('sample_rate', 0),
                'duration': int(json_data.get('audio', {}).get('duration', 0)),
                'nfft': json_data.get('analysis', {}).get('nfft', 0),
                'hop_length': json_data.get('analysis', {}).get('hop_length', 0),
                'audio_file': json_data.get('audio', {}).get('filename', ''),
                'time_shape': json_data.get('spectrogram', {}).get('n_times', 0),
                'frequency_shape': json_data.get('spectrogram', {}).get('n_frequencies', 0),
                'frequency_min': json_data.get('spectrogram', {}).get('frequency_min', 0),
                'frequency_max': json_data.get('spectrogram', {}).get('frequency_max', 0),
                # PNG-specific fields
                'is_data_png': True,
                'db_min': json_data.get('encoding', {}).get('db_min', 0),
                'db_max': json_data.get('encoding', {}).get('db_max', 0),
            }

            # Add calibration info
            calibration = json_data.get('calibration', {})
            if calibration.get('db_fullscale') is not None:
                metadata['db_fullscale'] = calibration['db_fullscale']
            elif calibration.get('db_ref') is not None:
                metadata['db_ref'] = calibration['db_ref']

            return metadata

        except Exception as e:
            logger.error(f"Failed to read metadata from {self.json_path}: {e}")
            return {}

    def load_spectrogram_data(self) -> Optional[Dict]:
        """
        Load and decode PNG to get spectrogram data

        Returns:
            Dictionary with 'spectrogram', 'time', 'frequency' arrays
        """
        if Image is None or np is None:
            raise ImportError("Pillow and numpy are required for PNG support")

        if self._json_data is None:
            self._load_json()

        if not self.png_path or not self.png_path.exists():
            logger.error(f"PNG file not found: {self.png_path}")
            return None

        try:
            # Load PNG as 16-bit grayscale
            img = Image.open(self.png_path)
            img_array = np.array(img, dtype=np.uint16)

            # Get encoding parameters
            encoding = self._json_data.get('encoding', {})
            db_min = encoding.get('db_min', 0)
            db_max = encoding.get('db_max', 1)
            db_range = db_max - db_min

            # Convert pixels back to dB values
            # PNG is stored with low frequencies at top after flipud, so flip back
            img_array = np.flipud(img_array)
            spectrogram = (img_array.astype(np.float32) / 65535) * db_range + db_min

            # Generate time and frequency arrays
            spec_info = self._json_data.get('spectrogram', {})
            n_times = spec_info.get('n_times', spectrogram.shape[1])
            n_freqs = spec_info.get('n_frequencies', spectrogram.shape[0])
            time_min = spec_info.get('time_min', 0)
            time_max = spec_info.get('time_max', 1)
            freq_min = spec_info.get('frequency_min', 0)
            freq_max = spec_info.get('frequency_max', 1)

            time = np.linspace(time_min, time_max, n_times)
            frequency = np.linspace(freq_min, freq_max, n_freqs)

            return {
                'spectrogram': spectrogram,
                'time': time,
                'frequency': frequency,
                'attributes': self.metadata
            }

        except Exception as e:
            logger.error(f"Failed to load PNG spectrogram from {self.png_path}: {e}")
            return None

    def get_netcdf_data_json(self) -> Optional[str]:
        """
        Get spectrogram data in JSON format compatible with NetCDF frontend

        Returns:
            JSON string with spectrogram data
        """
        data = self.load_spectrogram_data()
        if data is None:
            return None

        # Convert to format expected by frontend (same as NetCDF data)
        result = {
            'spectrogram': data['spectrogram'].tolist(),
            'time': data['time'].tolist(),
            'frequency': data['frequency'].tolist(),
            'attributes': data['attributes'],
            'shape': list(data['spectrogram'].shape),
            'downsampling': {
                'time_step': 1,
                'freq_step': 1
            }
        }

        return json.dumps(result)

    def close(self):
        """No-op for compatibility with SpectrogramFile"""
        pass

    def __repr__(self):
        return f"DataPngSpectrogramFile(json={self.json_path.name}, wav={self.wav_path.name if self.wav_path else 'None'})"


class SimpleDataset:
    """
    Simple dataset structure for APLOSE

    A dataset is a folder containing:
    - WAV files (audio recordings)
    - Spectrograms in one of these formats:
      - Data PNG + JSON files (preferred, compact format for Plotly display)
      - NetCDF files (legacy format)
    - Optional: metadata.json with dataset-level information
    """

    def __init__(self, folder: Path):
        """
        Initialize dataset from a folder

        Args:
            folder: Path to dataset folder
        """
        self.folder = Path(folder)
        self.name = self.folder.name
        self._spectrograms = None
        self._metadata = None
        self._format = None  # 'data_png' or 'netcdf'

        if not self.folder.exists():
            raise ValueError(f"Dataset folder does not exist: {self.folder}")

    @property
    def format(self) -> str:
        """Get the format of spectrograms in this dataset"""
        if self._format is None:
            # Determine format by scanning
            self._scan_spectrograms()
        return self._format or 'unknown'

    @property
    def spectrograms(self) -> List:
        """Get list of spectrogram files in the dataset"""
        if self._spectrograms is None:
            self._spectrograms = self._scan_spectrograms()
        return self._spectrograms

    def _scan_spectrograms(self) -> List:
        """Scan folder for spectrograms (data PNG or NetCDF) and match with WAV files"""

        # First, try to find data PNG files (preferred format)
        spectrograms = self._scan_data_png_files()
        if spectrograms:
            self._format = 'data_png'
            logger.info(f"Found {len(spectrograms)} data PNG spectrograms in {self.folder}")
            return spectrograms

        # Fall back to NetCDF files
        spectrograms = self._scan_netcdf_files()
        if spectrograms:
            self._format = 'netcdf'
            logger.info(f"Found {len(spectrograms)} NetCDF spectrograms in {self.folder}")
            return spectrograms

        logger.warning(f"No spectrogram files found in {self.folder}")
        return []

    def _scan_data_png_files(self) -> List[DataPngSpectrogramFile]:
        """Scan folder for data PNG + JSON spectrogram files"""
        # Look for *_data.json files (our data PNG metadata format)
        json_files = sorted(self.folder.glob("*_data.json"))

        if not json_files:
            return []

        spectrograms = []
        for json_path in json_files:
            # Extract base filename and FFT size from pattern: filename_fft1024_data.json
            stem = json_path.stem  # e.g., "filename_fft1024_data"
            if stem.endswith('_data'):
                base_stem = stem[:-5]  # Remove "_data" suffix

                # Find corresponding WAV file
                wav_path = self._find_wav_file_for_data_png(base_stem)

                spec_file = DataPngSpectrogramFile(
                    json_path,
                    wav_path if wav_path and wav_path.exists() else None
                )
                spectrograms.append(spec_file)

        return spectrograms

    def _find_wav_file_for_data_png(self, base_stem: str) -> Optional[Path]:
        """
        Find WAV file for a data PNG spectrogram.
        Base stem is like 'filename_fft1024', need to find 'filename.wav'
        """
        # Remove FFT suffix pattern (_fft followed by digits)
        wav_stem = re.sub(r'_fft\d+$', '', base_stem)

        # Try exact match
        wav_path = self.folder / f"{wav_stem}.wav"
        if wav_path.exists():
            return wav_path

        # Try case-insensitive
        return self._find_wav_file(wav_stem)

    def _scan_netcdf_files(self) -> List[SpectrogramFile]:
        """Scan folder for NetCDF spectrogram files"""
        netcdf_files = sorted(self.folder.glob("*.nc"))

        if not netcdf_files:
            return []

        spectrograms = []
        for nc_path in netcdf_files:
            # Look for corresponding WAV file
            wav_path = nc_path.with_suffix('.wav')
            if not wav_path.exists():
                # Try case-insensitive search, stripping FFT suffix if present
                wav_path = self._find_wav_file(nc_path.stem)

            # Check if this is a multi-FFT file
            try:
                if xr is None:
                    raise ImportError("xarray is required")

                with xr.open_dataset(nc_path) as ds:
                    fft_sizes_str = ds.attrs.get('fft_sizes', '')

                    if fft_sizes_str:
                        # Multi-FFT file: create one SpectrogramFile per FFT size
                        fft_sizes = [int(s.strip()) for s in fft_sizes_str.split(',')]
                        logger.info(f"Found multi-FFT file {nc_path.name} with FFT sizes: {fft_sizes}")

                        for nfft in fft_sizes:
                            spec_file = SpectrogramFile(
                                nc_path,
                                wav_path if wav_path and wav_path.exists() else None,
                                nfft=nfft
                            )
                            spectrograms.append(spec_file)
                    else:
                        # Legacy single-FFT file
                        spec_file = SpectrogramFile(nc_path, wav_path if wav_path and wav_path.exists() else None)
                        spectrograms.append(spec_file)

            except Exception as e:
                logger.error(f"Failed to read {nc_path}: {e}")
                # Fallback: treat as legacy file
                spec_file = SpectrogramFile(nc_path, wav_path if wav_path and wav_path.exists() else None)
                spectrograms.append(spec_file)

        logger.info(f"Found {len(spectrograms)} spectrograms in {self.folder}")
        return spectrograms

    def _find_wav_file(self, stem: str) -> Optional[Path]:
        """
        Find WAV file with given stem (case-insensitive)
        """
        # Try exact match first
        for wav_path in self.folder.glob("*.wav"):
            if wav_path.stem.lower() == stem.lower():
                return wav_path
        for wav_path in self.folder.glob("*.WAV"):
            if wav_path.stem.lower() == stem.lower():
                return wav_path

        return None

    @property
    def metadata(self) -> Dict:
        """Get dataset-level metadata"""
        if self._metadata is None:
            self._metadata = self._read_dataset_metadata()
        return self._metadata

    def _read_dataset_metadata(self) -> Dict:
        """Read dataset metadata from metadata.json if it exists"""
        metadata_path = self.folder / "metadata.json"

        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"Loaded metadata from {metadata_path}")
                return metadata
            except Exception as e:
                logger.error(f"Failed to read metadata.json: {e}")

        # Generate default metadata
        metadata = {
            'name': self.name,
            'folder': str(self.folder),
            'n_spectrograms': len(self.spectrograms),
            'created_at': datetime.now().isoformat(),
        }

        # Add time range if spectrograms exist
        if self.spectrograms:
            begin_times = []
            end_times = []
            for spec in self.spectrograms:
                if spec.metadata.get('begin'):
                    begin_times.append(spec.metadata['begin'])
                if spec.metadata.get('end'):
                    end_times.append(spec.metadata['end'])

            if begin_times:
                metadata['begin'] = min(begin_times)
            if end_times:
                metadata['end'] = max(end_times)

        return metadata

    def save_metadata(self, additional_info: Optional[Dict] = None):
        """
        Save dataset metadata to metadata.json

        Args:
            additional_info: Additional metadata to include
        """
        metadata = self.metadata.copy()
        if additional_info:
            metadata.update(additional_info)

        metadata_path = self.folder / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved metadata to {metadata_path}")

    def get_spectrogram_by_time(self, timestamp: datetime) -> Optional[SpectrogramFile]:
        """
        Find spectrogram that contains the given timestamp

        Args:
            timestamp: Datetime to search for

        Returns:
            SpectrogramFile or None if not found
        """
        for spec in self.spectrograms:
            begin_str = spec.metadata.get('begin')
            end_str = spec.metadata.get('end')

            if begin_str and end_str:
                try:
                    begin = datetime.fromisoformat(begin_str.replace('+0000', ''))
                    end = datetime.fromisoformat(end_str.replace('+0000', ''))

                    if begin <= timestamp <= end:
                        return spec
                except Exception as e:
                    logger.warning(f"Failed to parse timestamps: {e}")

        return None

    def get_spectrogram_list(self) -> List[Dict]:
        """
        Get list of spectrograms with metadata

        Returns:
            List of dictionaries with spectrogram info
        """
        result = []
        for spec in self.spectrograms:
            if isinstance(spec, DataPngSpectrogramFile):
                info = {
                    'json_path': str(spec.json_path),
                    'json_name': spec.json_path.name,
                    'png_path': str(spec.png_path) if spec.png_path else None,
                    'png_name': spec.png_path.name if spec.png_path else None,
                    'wav_path': str(spec.wav_path) if spec.wav_path else None,
                    'wav_name': spec.wav_path.name if spec.wav_path else None,
                    'format': 'data_png',
                    **spec.metadata
                }
            else:
                # NetCDF format
                info = {
                    'netcdf_path': str(spec.netcdf_path),
                    'netcdf_name': spec.netcdf_path.name,
                    'wav_path': str(spec.wav_path) if spec.wav_path else None,
                    'wav_name': spec.wav_path.name if spec.wav_path else None,
                    'format': 'netcdf',
                    **spec.metadata
                }
            result.append(info)
        return result

    def close_all(self):
        """Close all open datasets"""
        if self._spectrograms:
            for spec in self._spectrograms:
                spec.close()

    def __repr__(self):
        return f"SimpleDataset(name='{self.name}', spectrograms={len(self.spectrograms)})"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()
