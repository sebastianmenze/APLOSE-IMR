"""View for spectrogram file serving (PNG/WAV/JSON)"""
import json
import os
import re
from pathlib import Path
import logging

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


class NetCDFViewSet(ViewSet):
    """
    API endpoints for serving PNG spectrogram files, JSON metadata, and WAV audio.
    """

    @action(detail=False, methods=['get'], url_path='list-example-files')
    def list_example_files(self, request):
        """
        List available PNG/JSON spectrogram files in the example dataset folder.
        Groups files by recording (one WAV with multiple FFT analyses).
        """
        try:
            datawork_dir = Path(settings.DATAWORK_FOLDER if hasattr(settings, 'DATAWORK_FOLDER') else '/opt/datawork')
            example_dir = datawork_dir / 'dataset' / 'example'

            if not example_dir.exists():
                return JsonResponse({
                    'recordings': [],
                    'basePath': '',
                    'message': 'Example folder not found. Place PNG/JSON files in volumes/datawork/dataset/example/'
                })

            json_files = list(example_dir.glob('*_data.json'))

            recordings_dict = {}
            fft_pattern = re.compile(r'(.+)_fft(\d+)_data\.json$')

            for json_file in sorted(json_files):
                match = fft_pattern.match(json_file.name)
                if not match:
                    continue

                base_name = match.group(1)
                fft_size = int(match.group(2))

                try:
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)

                    png_file = metadata.get('png_file', '')
                    wav_file = metadata.get('audio', {}).get('filename', '')
                    timestamp = metadata.get('temporal', {}).get('begin', '')

                    png_path = example_dir / png_file if png_file else None
                    png_exists = png_path and png_path.exists()

                    if base_name not in recordings_dict:
                        recordings_dict[base_name] = {
                            'id': base_name,
                            'wav': wav_file,
                            'timestamp': timestamp,
                            'analyses': []
                        }

                    recordings_dict[base_name]['analyses'].append({
                        'fft': fft_size,
                        'json': json_file.name,
                        'png': png_file if png_exists else None,
                    })

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Could not parse JSON file {json_file}: {e}")
                    continue

            recordings = []
            for rec in recordings_dict.values():
                rec['analyses'].sort(key=lambda x: x['fft'])
                recordings.append(rec)

            recordings.sort(key=lambda x: x['timestamp'])

            return JsonResponse({
                'recordings': recordings,
                'basePath': '/api/netcdf/example-file?file=',
            })

        except Exception as e:
            logger.error(f"Failed to list example files: {e}")
            return Response(
                {'error': 'Failed to list example files'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='example-file')
    def serve_example_file(self, request):
        """
        Serve a file from the example dataset folder (PNG, JSON, WAV).
        """
        filename = request.query_params.get('file')
        if not filename:
            return Response(
                {'error': 'Filename is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            datawork_dir = Path(settings.DATAWORK_FOLDER if hasattr(settings, 'DATAWORK_FOLDER') else '/opt/datawork')
            example_dir = datawork_dir / 'dataset' / 'example'
            # Security: resolve symlinks and verify file stays within example_dir
            file_path = (example_dir / filename).resolve()
            example_dir_resolved = example_dir.resolve()
            if not str(file_path).startswith(str(example_dir_resolved) + os.sep):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            if not file_path.exists() or not file_path.is_file():
                raise Http404("File not found")

            content_types = {
                '.json': 'application/json',
                '.png': 'image/png',
                '.wav': 'audio/wav',
                '.mp3': 'audio/mpeg',
            }
            content_type = content_types.get(file_path.suffix.lower(), 'application/octet-stream')

            return FileResponse(
                open(file_path, 'rb'),
                content_type=content_type,
                as_attachment=False
            )

        except Http404:
            raise
        except Exception as e:
            logger.error(f"Failed to serve example file {filename}: {e}")
            return Response(
                {'error': 'Failed to serve file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='list-sound-library', permission_classes=[AllowAny])
    def list_sound_library(self, request):
        """
        List available audio files in the sound library folder.
        Groups files by prefix (e.g., "Blue whale D-call").
        """
        try:
            datawork_dir = Path(settings.DATAWORK_FOLDER if hasattr(settings, 'DATAWORK_FOLDER') else '/opt/datawork')
            library_dir = datawork_dir / 'dataset' / 'sound_library'

            if not library_dir.exists():
                return JsonResponse({
                    'files': [],
                    'basePath': '',
                    'message': 'Sound library folder not found. Place files in volumes/datawork/dataset/sound_library/'
                })

            json_files = list(library_dir.glob('*_data.json'))

            files_dict = {}
            fft_pattern = re.compile(r'^(.+)_fft(\d+)_data\.json$')

            for json_file in sorted(json_files):
                match = fft_pattern.match(json_file.name)
                if not match:
                    continue

                base_name = match.group(1)
                fft_size = int(match.group(2))

                try:
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)

                    png_file = metadata.get('png_file', '')
                    wav_file = metadata.get('audio', {}).get('filename', '')

                    prefix_match = re.match(r'^(.+)_\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}\.wav$', wav_file)
                    if prefix_match:
                        prefix = prefix_match.group(1).strip()
                    else:
                        prefix = os.path.splitext(wav_file)[0] if wav_file else base_name

                    png_path = library_dir / png_file if png_file else None
                    png_exists = png_path and png_path.exists()

                    file_key = wav_file or base_name

                    if file_key not in files_dict:
                        files_dict[file_key] = {
                            'prefix': prefix,
                            'filename': wav_file,
                            'baseName': base_name,
                            'analyses': []
                        }

                    files_dict[file_key]['analyses'].append({
                        'fft': fft_size,
                        'json': json_file.name,
                        'png': png_file if png_exists else None,
                    })

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Could not parse JSON file {json_file}: {e}")
                    continue

            files = []
            for file_data in files_dict.values():
                file_data['analyses'].sort(key=lambda x: x['fft'])
                files.append(file_data)

            files.sort(key=lambda x: x['prefix'])

            return JsonResponse({
                'files': files,
                'basePath': '/api/netcdf/sound-library-file?file=',
            })

        except Exception as e:
            logger.error(f"Failed to list sound library files: {e}")
            return Response(
                {'error': 'Failed to list sound library files'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='sound-library-file', permission_classes=[AllowAny])
    def serve_sound_library_file(self, request):
        """
        Serve a file from the sound library folder (PNG, JSON, WAV).
        """
        filename = request.query_params.get('file')
        if not filename:
            return Response(
                {'error': 'Filename is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            datawork_dir = Path(settings.DATAWORK_FOLDER if hasattr(settings, 'DATAWORK_FOLDER') else '/opt/datawork')
            library_dir = datawork_dir / 'dataset' / 'sound_library'
            # Security: resolve symlinks and verify file stays within library_dir
            file_path = (library_dir / filename).resolve()
            library_dir_resolved = library_dir.resolve()
            if not str(file_path).startswith(str(library_dir_resolved) + os.sep):
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

            if not library_dir.exists():
                return Response(
                    {'error': 'Sound library directory not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not file_path.exists() or not file_path.is_file():
                raise Http404("File not found")

            content_types = {
                '.json': 'application/json',
                '.png': 'image/png',
                '.wav': 'audio/wav',
                '.mp3': 'audio/mpeg',
            }
            content_type = content_types.get(file_path.suffix.lower(), 'application/octet-stream')

            file_size = file_path.stat().st_size
            range_header = request.META.get('HTTP_RANGE', '')

            if range_header and range_header.startswith('bytes='):
                byte_range = range_header[6:].split('-')
                start = int(byte_range[0]) if byte_range[0] else 0
                end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                with open(file_path, 'rb') as f:
                    f.seek(start)
                    data = f.read(length)

                response = HttpResponse(data, status=206, content_type=content_type)
                response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                response['Accept-Ranges'] = 'bytes'
                response['Content-Length'] = length
                return response

            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type,
                as_attachment=False
            )
            response['Accept-Ranges'] = 'bytes'
            response['Content-Length'] = file_size
            return response

        except Http404:
            raise
        except Exception as e:
            logger.error(f"Failed to serve sound library file {filename}: {e}")
            return Response(
                {'error': 'Failed to serve file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
