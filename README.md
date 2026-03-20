# APLOSE-IMR

[![Continuous integration][ci-badge]][ci-link]
[![Code style: black][black-badge]][black-link]
[![][coverage-badge]][coverage-link]

[ci-badge]: https://github.com/Project-OSmOSE/osmose-app/actions/workflows/continuous-integration.yml/badge.svg
[ci-link]: https://github.com/Project-OSmOSE/osmose-app/actions/workflows/continuous-integration.yml
[black-badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-link]: https://github.com/psf/black
[coverage-badge]: https://Project-OSmOSE.github.io/osmose-app/coverage/badge.svg
[coverage-link]: https://Project-OSmOSE.github.io/osmose-app/coverage

**APLOSE** (Annotation Platform for Large Ocean Sound Exploration) is a scalable web-based annotation platform for acoustic spectrograms, developed for marine bioacoustics research and extensible to any acoustic study domain.

> Read the [documentation](https://project-osmose.github.io/APLOSE/)

---

## Table of Contents

- [Overview](#overview)
- [Platform Architecture](#platform-architecture)
- [Features & Functionalities](#features--functionalities)
- [Interactive Plotly Annotation Interface](#interactive-plotly-annotation-interface)
- [Data Models](#data-models)
- [Audio Processing](#audio-processing)
- [Dataset Format](#dataset-format)
- [User Roles & Permissions](#user-roles--permissions)
- [Deployment](#deployment)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Environment Variables](#environment-variables)

---

## Overview

APLOSE-IMR is a full-stack web application that allows researchers to annotate acoustic spectrograms collaboratively. Annotators view time-frequency spectrograms rendered interactively in the browser, draw annotations directly on the plot, and associate them with labels, confidence levels, and acoustic features.

**Key use cases:**
- Marine mammal call detection and classification
- Ship noise and anthropogenic sound annotation
- Multi-annotator campaigns with verification phases
- Machine learning detector result review and validation

---

## Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Annotator)                      │
│  React 18 + TypeScript + Redux Toolkit + Plotly.js              │
└──────────────────────────┬──────────────────────────────────────┘
                           │ GraphQL / REST
┌──────────────────────────▼──────────────────────────────────────┐
│                      Django Backend                             │
│  Django 3.2 · Graphene-Django (GraphQL) · Django REST Framework │
│  ┌────────────┐  ┌──────────────────┐  ┌─────────────────────┐  │
│  │   api app  │  │  aplose app      │  │  utils/spectrogram  │  │
│  │ (datasets, │  │  (users, auth)   │  │  (NetCDF / PNG I/O) │  │
│  │ campaigns, │  │                  │  │                     │  │
│  │ annotation)│  └──────────────────┘  └─────────────────────┘  │
│  └────────────┘                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│             PostgreSQL + PostGIS  (via Docker)                  │
└─────────────────────────────────────────────────────────────────┘

                    ┌────────────────────────┐
                    │  APLOSE Audio Processor │  (standalone Python package)
                    │  WAV → Data PNG + JSON  │
                    │       or NetCDF         │
                    └────────────────────────┘
```

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript 5, Redux Toolkit, Vite, React Router 7 |
| **Visualization** | Plotly.js 2.27, react-plotly.js |
| **UI Components** | React Bootstrap, Ionic React, Ionicons |
| **API Client** | graphql-request, RxJS |
| **Backend** | Django 3.2, Graphene-Django 3.2, Django REST Framework 3.12 |
| **Database** | PostgreSQL + PostGIS |
| **Audio / Science** | xarray, netcdf4, soundfile, Pillow, numpy |
| **Deployment** | Docker Compose, Nginx |
| **Testing** | Playwright (E2E), Vitest (unit), pytest, coverage |
| **Code Quality** | ESLint, Black, Pylint, GraphQL Codegen |

---

## Features & Functionalities

### Annotation Campaigns

A **campaign** is the top-level unit of work. It links a dataset to a label set and organises annotators into phases.

- Create campaigns with custom name, description, deadline, and instructions URL
- Choose from existing label sets or define new ones
- Optionally attach a confidence set (annotators rate their certainty)
- Allow or restrict point annotations and visual tuning per campaign
- Archive completed campaigns

### Two-Phase Annotation Workflow

| Phase | Purpose |
|-------|---------|
| **Annotation (A)** | Annotators draw labels on assigned spectrograms |
| **Verification (V)** | Reviewers validate or correct previous annotations |

Both phases produce independent sets of annotations, preserving original work.

### Annotation Types

| Type | Description |
|------|-------------|
| **Weak (W)** | Presence/absence label at file level — no time/frequency coordinates |
| **Point (P)** | Single point in time-frequency space |
| **Box (B)** | Rectangular region spanning a time range and frequency band |

### File Range Assignment

Campaign owners assign ranges of spectrograms to each annotator. The system creates **AnnotationTask** records automatically, one per spectrogram per annotator.

### Label Sets & Confidence Sets

- Labels can be shared across campaigns (reusable `LabelSet`)
- Confidence levels are customisable (e.g., High / Medium / Low with numeric values)
- Labels can be tagged as requiring **Acoustic Features** — a detailed sub-form with quantitative parameters (duration, bandwidth, frequency peak, etc.)

### Detector Integration

Import machine-learning detector results as pre-populated annotations. Annotators then review, accept, or correct them in a standard campaign workflow.

### Audio Playback Controls

- Play / pause with **spacebar** (active immediately on page load — no click needed)
- Adjustable **playback rate**
- **Audio normalisation** toggle (Web Audio API dynamics compressor + gain)
- Configurable **stop time** to loop over a region of interest
- Download audio file button (available to all users)

### Spectrogram Visual Tuning

- **Brightness** and **Contrast** sliders
- **Colormap** selector (viridis, plasma, inferno, jet, greys, and more, with inversion)
- **Z-range (dB min / max)** adjustment for dynamic range control
- **Frequency axis** toggle: linear or logarithmic scale
- **Zoom** controls for time and frequency axes

### Comments

Annotators can attach free-text comments to individual spectrograms, optionally linked to a specific annotation.

---

## Interactive Plotly Annotation Interface

The annotation page is the core of APLOSE. It renders spectrograms as interactive Plotly heatmaps and overlays a canvas layer for annotation drawing.

### Spectrogram Rendering

```
┌──────────────────────────────────────────────────────────────┐
│  Visual Configuration bar  (brightness · contrast · colormap)│
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   Plotly Heatmap (time × frequency spectrogram)              │
│   ─────────────────────────────────────────────              │
│   • Interactive hover: shows time, frequency, dB value       │
│   • Click-drag: creates box annotations                      │
│   • Single click: creates point annotation                   │
│   • Vertical cursor: tracks current audio playback position  │
│                                                              │
│   Canvas overlay (annotations rendered as coloured shapes)   │
│   ─────────────────────────────────────────────              │
│   • Box annotations = coloured rectangles                    │
│   • Point annotations = coloured dots                        │
│   • Active annotation highlighted with thicker border        │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Audio controls  (play/pause · rate · normalise · download)  │
├──────────────────────────────────────────────────────────────┤
│  Annotation list  (label · confidence · time/freq info)      │
│  Label selector   (colour-coded chips with keyboard shortcuts)│
└──────────────────────────────────────────────────────────────┘
```

### Data Pipeline: Spectrogram → Browser

1. Frontend requests an `AnnotationTask` via GraphQL.
2. Backend loads the spectrogram file (NetCDF or Data PNG + JSON).
3. The 2-D matrix is **downsampled to ~4 000 time samples** for fast JSON transfer.
4. Time array, frequency array, dB matrix, and metadata are returned together.
5. Plotly renders a `Heatmap` trace; the canvas layer is sized and positioned to match.

### Supported Spectrogram Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| **Data PNG + JSON** | `*_fft{N}_data.png` + `.json` | 16-bit grayscale image + dB reconstruction metadata. Preferred format. |
| **NetCDF** | `*.nc` | xarray-compatible, supports multiple FFT sizes in one file. |

### Annotation Drawing Flow

1. Annotator selects a **label** (keyboard shortcut: number key or letter key).
2. Optionally selects a **confidence level**.
3. Clicks or click-drags on the spectrogram to create an annotation.
4. A GraphQL mutation saves the annotation immediately.
5. The annotation appears in the canvas overlay and in the annotation list below.
6. Pressing **Delete** removes the focused annotation.
7. Pressing **Enter** (or NumpadEnter) submits the task and advances to the next spectrogram.

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play / pause audio |
| `←` / `→` | Navigate to previous / next spectrogram |
| `Enter` / `NumpadEnter` | Submit task |
| `Delete` | Remove focused annotation |
| `1`–`9` / letters | Select label by shortcut |

### Zoom & Navigation

- **Zoom in/out** buttons adjust the visible time-frequency window.
- Zoom level is shown on the Download Spectrogram button (`Download spectrogram (zoom x2)` etc.).
- Navigation buttons and arrow-key shortcuts move between spectrograms.

---

## Data Models

### Dataset & Spectrogram

```
Dataset
 └── SpectrogramAnalysis  (one per FFT size)
      └── Spectrogram      (one per audio file)
```

- `Dataset`: name, path on server, owner, timestamps.
- `SpectrogramAnalysis`: nfft, hop length, sample rate, frequency range, dB display range, colormap.
- `Spectrogram`: filename, start/end datetime, file format (PNG or NC).

### Annotation Hierarchy

```
AnnotationCampaign
 ├── LabelSet  →  Label (×N)
 ├── ConfidenceSet  →  Confidence (×N)
 └── AnnotationPhase  (Annotation or Verification)
      └── AnnotationFileRange  (annotator assignment)
           └── AnnotationTask  (per spectrogram)
                └── Annotation  (per drawn label)
                     └── AcousticFeatures (optional)
```

---

## Audio Processing

The `aplose_audio_processor` package (located in `aplose_audio_processor/`) prepares raw WAV recordings for import into APLOSE.

### Features

- Resample audio to a target sample rate
- Split long recordings into fixed-length **snippets** with optional overlap
- Apply a **time offset** or maximum duration to trim recordings
- Generate spectrograms with **multiple FFT sizes** in one pass
- Export to **Data PNG + JSON** (default) or **NetCDF**
- Calibrated dB output via `--db-fullscale`
- **Parallel batch processing** with configurable worker count

### CLI Usage

```bash
pip install -e aplose_audio_processor/

aplose-audio-processor \
  -i input_recordings/ \
  -o output_dataset/ \
  --sample-rate 48000 \
  --snippet-duration 60 \
  --overlap 10 \
  --fft-sizes 1024,2048,4096 \
  --window hann \
  --workers 4
```

### Output Structure

```
output_dataset/
├── recording_2024_01_15_08_00_00.wav
├── recording_2024_01_15_08_00_00_fft1024_data.png
├── recording_2024_01_15_08_00_00_fft1024_data.json
├── recording_2024_01_15_08_00_00_fft2048_data.png
├── recording_2024_01_15_08_00_00_fft2048_data.json
└── ...
```

---

## Dataset Format

APLOSE uses a simple **folder-based dataset format**. Files are matched by filename stem; datetimes are parsed from filenames.

### Naming Convention

```
{prefix}_{YYYY_MM_DD_HH_MM_SS}{suffix}.wav
```

Examples: `hydrophone_2024_01_15_08_30_00.wav`, `2024_01_15_08_30_00.wav`

### Import

```bash
# Via management command
python manage.py import_simple_dataset "Dataset Name" path/to/folder/

# Via GraphQL
mutation {
  importSimpleDataset(name: "Dataset Name", path: "relative/path") {
    ok
    message
  }
}
```

### Utilities

Remove short WAV files and their associated spectrograms:

```bash
# Preview (dry run)
python scripts/clean_short_files.py /path/to/dataset --dry-run

# Delete files shorter than 30 s (default)
python scripts/clean_short_files.py /path/to/dataset

# Custom threshold
python scripts/clean_short_files.py /path/to/dataset --min-duration 60
```

---

## User Roles & Permissions

| Role | Capabilities |
|------|-------------|
| **Superuser / Staff** | Import datasets, create campaigns, manage label sets, assign annotators |
| **Campaign Owner** | Create phases, assign file ranges, archive campaign |
| **Annotator** | Access assigned tasks, draw annotations, add comments |

Annotators can have an expertise level: `NOVICE`, `AVERAGE`, or `EXPERT`, which is recorded on each annotation.

---

## Deployment

### Docker Compose (recommended)

```bash
cp .env.example .env   # edit variables (see below)
docker compose up -d
```

### Ifremer Infrastructure

Follow the comments in `.gitlab-ci.yml` for CI/CD pipeline setup.

---

## Development Setup

### Backend

```bash
# Install dependencies
pip install poetry
poetry install

# Start database
docker run --name devdb -e POSTGRES_PASSWORD=postgres -p 127.0.0.1:5432:5432 -d postgis/postgis
docker start devdb

# Apply migrations and seed data
poetry run ./manage.py migrate
poetry run ./manage.py seed

# Run dev server
poetry run ./manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Before Pushing

```bash
# Check for missing migrations
poetry run ./manage.py makemigrations

# Lint
poetry run pylint backend

# Format
poetry run black backend
```

---

## Testing

```bash
# Backend tests
docker start devdb
poetry run ./manage.py test

# Backend coverage
coverage run ./manage.py test && coverage report
coverage html   # HTML report in htmlcov/

# Frontend unit tests
cd frontend && npm test

# Frontend E2E tests (Playwright)
cd frontend && npx playwright test
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ENV` | `development` or `production` |
| `STAGING` | `true` if running in staging (installs dev libs) |
| `SECRET_KEY` | Django secret key |
| `OSMOSE_HOST` | Hostname (e.g. `osmose.ifremer.fr`) |
| `OSMOSE_DB_USER` | Database username |
| `OSMOSE_DB_PWD` | Database password |
| `HTTPS_PORTAL_STAGE` | `local` for local TLS testing |
| `OSMOSE_SENTRY_URL` | Sentry DSN (optional) |
