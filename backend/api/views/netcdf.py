"""View for NetCDF spectrogram operations"""
import json
import os
from pathlib import Path
import logging

import numpy as np
import xarray as xr
from django.http import JsonResponse
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status

from backend.api.models import SpectrogramAnalysis

logger = logging.getLogger(__name__)


class NetCDFViewSet(ViewSet):
    """
    API endpoints for NetCDF spectrogram operations.

    Provides functionality to parse and serve NetCDF spectrogram files
    for visualization in the frontend.
    """

    @action(detail=False, methods=['get'], url_path='parse')
    def parse_netcdf(self, request):
        """
        Parse a NetCDF spectrogram file and return its data as JSON.

        Query parameters:
            path: Path to the NetCDF file (optional)

        If no path is provided, serves the static example spectrogram.

        Returns:
            JSON response with spectrogram data:
            {
                "spectrogram": [[...]], 2D array of power values
                "time": [...],          1D array of time values
                "frequency": [...],     1D array of frequency values
                "attributes": {...}     File metadata
            }
        """
        # Get file path from query params, default to example file
        file_path = request.query_params.get('path')

        if not file_path:
            # Use static example file
            backend_dir = Path(__file__).parent.parent.parent
            file_path = backend_dir / 'static' / 'examples' / 'example_spectrogram.nc'
        else:
            file_path = Path(file_path)

        # Security: Ensure file exists and is readable
        if not file_path.exists():
            return Response(
                {'error': f'NetCDF file not found: {file_path}'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not file_path.is_file():
            return Response(
                {'error': f'Path is not a file: {file_path}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Open and parse NetCDF file
            ds = xr.open_dataset(file_path)

            # Extract spectrogram data
            spectrogram = ds['spectrogram'].values
            time = ds['time'].values
            frequency = ds['frequency'].values

            # Get downsampling info if available
            downsampling = {}
            if 'downsampling_time_step' in ds.attrs:
                downsampling['time_step'] = int(ds.attrs['downsampling_time_step'])
            if 'downsampling_freq_step' in ds.attrs:
                downsampling['freq_step'] = int(ds.attrs['downsampling_freq_step'])

            # Convert numpy types to Python types for JSON serialization
            response_data = {
                'spectrogram': spectrogram.tolist(),
                'time': time.tolist(),
                'frequency': frequency.tolist(),
                'attributes': {k: str(v) for k, v in ds.attrs.items()},
                'shape': list(spectrogram.shape),
            }

            if downsampling:
                response_data['downsampling'] = downsampling

            ds.close()

            return JsonResponse(response_data)

        except Exception as e:
            return Response(
                {'error': f'Failed to parse NetCDF file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='example')
    def get_example(self, request):
        """
        Get information about the static example spectrogram.

        Returns metadata without loading the full data array.
        """
        try:
            backend_dir = Path(__file__).parent.parent.parent
            file_path = backend_dir / 'static' / 'examples' / 'example_spectrogram.nc'

            if not file_path.exists():
                return Response(
                    {'error': 'Example spectrogram file not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Open file and get metadata only
            ds = xr.open_dataset(file_path)

            metadata = {
                'path': str(file_path),
                'attributes': {k: str(v) for k, v in ds.attrs.items()},
                'dimensions': {
                    'time': len(ds['time']),
                    'frequency': len(ds['frequency']),
                },
                'time_range': [
                    float(ds['time'].min()),
                    float(ds['time'].max())
                ],
                'frequency_range': [
                    float(ds['frequency'].min()),
                    float(ds['frequency'].max())
                ],
            }

            ds.close()

            return JsonResponse(metadata)

        except Exception as e:
            return Response(
                {'error': f'Failed to read example file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='dataset-spectrogram')
    def get_dataset_spectrogram(self, request):
        """
        Get spectrogram data for a dataset analysis.

        Query parameters:
            analysis_id: ID of the SpectrogramAnalysis
            downsample: Optional downsampling factor (default: 1, no downsampling)

        Returns:
            JSON response with spectrogram data
        """
        analysis_id = request.query_params.get('analysis_id')

        if not analysis_id:
            return Response(
                {'error': 'analysis_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get analysis
            analysis = SpectrogramAnalysis.objects.get(pk=analysis_id)
        except SpectrogramAnalysis.DoesNotExist:
            return Response(
                {'error': f'SpectrogramAnalysis not found: {analysis_id}'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Get NetCDF file path
            netcdf_path = analysis.get_netcdf_path()

            if not netcdf_path.exists():
                return Response(
                    {'error': f'NetCDF file not found: {netcdf_path}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Open and parse NetCDF file
            ds = xr.open_dataset(netcdf_path)

            # Get downsampling factor
            downsample = int(request.query_params.get('downsample', 1))

            # Check if this is a multi-FFT file
            fft_sizes_str = ds.attrs.get('fft_sizes', '')
            is_multi_fft = bool(fft_sizes_str)

            if is_multi_fft:
                # Multi-FFT file: extract the spectrogram for this analysis's FFT size
                nfft = analysis.nfft
                var_name = f'spectrogram_fft{nfft}'
                time_coord = f'time_fft{nfft}'
                freq_coord = f'frequency_fft{nfft}'

                if var_name not in ds.data_vars:
                    ds.close()
                    return Response(
                        {'error': f'FFT size {nfft} not found in NetCDF file. Available: {list(ds.data_vars.keys())}'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Extract and optionally downsample data
                spectrogram = ds[var_name].values
                time = ds[time_coord].values
                frequency = ds[freq_coord].values
            else:
                # Legacy single-FFT file
                spectrogram = ds['spectrogram'].values
                time = ds['time'].values
                frequency = ds['frequency'].values

            if downsample > 1:
                # Downsample for performance
                spectrogram = spectrogram[::downsample, ::downsample]
                time = time[::downsample]
                frequency = frequency[::downsample]
                logger.info(f"Downsampled by factor {downsample}: {spectrogram.shape}")

            # Convert numpy types to Python types for JSON serialization
            response_data = {
                'spectrogram': spectrogram.tolist(),
                'time': time.tolist(),
                'frequency': frequency.tolist(),
                'attributes': {k: str(v) for k, v in ds.attrs.items()},
                'shape': list(spectrogram.shape),
                'analysis': {
                    'id': analysis.id,
                    'name': analysis.name,
                    'dataset': analysis.dataset.name,
                    'start': analysis.start.isoformat() if analysis.start else None,
                    'end': analysis.end.isoformat() if analysis.end else None,
                    'sample_rate': analysis.sample_rate,
                    'duration': analysis.duration,
                },
            }

            if downsample > 1:
                if is_multi_fft:
                    original_shape = [len(ds[freq_coord]), len(ds[time_coord])]
                else:
                    original_shape = [len(ds['frequency']), len(ds['time'])]

                response_data['downsampling'] = {
                    'factor': downsample,
                    'original_shape': original_shape,
                }

            ds.close()

            return JsonResponse(response_data)

        except Exception as e:
            logger.error(f"Failed to load spectrogram for analysis {analysis_id}: {e}")
            return Response(
                {'error': f'Failed to load spectrogram: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
