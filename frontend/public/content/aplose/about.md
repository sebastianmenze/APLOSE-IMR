# About APLOSE

APLOSE (Annotation Platform for Ocean Sound Exploration) is a web-based platform for visualising and annotating underwater acoustic recordings. It was originally developed at [Ifremer](https://www.ifremer.fr/en) and has been extended and deployed at the [Institute of Marine Research (IMR)](https://www.hi.no/en) to support passive acoustic monitoring programs in Norwegian and polar waters.

The source code for the IMR deployment is available on [GitHub](https://github.com/sebastianmenze/APLOSE-IMR).

## What APLOSE Does

APLOSE provides a collaborative environment for marine biologists, acoustic researchers, and annotators to work efficiently with large hydrophone datasets. Instead of copying terabyte-sized recordings between machines, researchers access the data directly through the browser.

Key capabilities include:

- **Spectrogram visualisation** — Browse recordings as interactive spectrograms with adjustable FFT parameters and frequency scales
- **Annotation campaigns** — Organise annotation work across teams, with defined label sets, assigned annotators, and progress tracking
- **Bounding-box annotation** — Draw precise time–frequency boxes on spectrograms to mark and classify acoustic events
- **Verification phase** — A second reviewer can validate or correct existing annotations before export
- **Detector import** — Upload output from automatic detectors and verify predictions collaboratively
- **Multi-FFT support** — Switch between multiple pre-computed spectrogram resolutions for the same recording
- **Export** — Download completed annotations in standard formats (CSV, RAVEN, JSON) for downstream analysis

## The Annotation Workflow

1. **Prepare data** — Audio files are pre-processed into snippets and spectrograms using the [APLOSE Audio Processor](https://github.com/sebastianmenze/APLOSE-IMR/tree/main/aplose_audio_processor) package
2. **Import** — An administrator imports the processed dataset into APLOSE
3. **Create a campaign** — A campaign is configured with a dataset, a label set (species / sound types), and assigned annotators
4. **Annotate** — Annotators open files in the spectrogram viewer, draw bounding boxes, and optionally listen to the audio segment
5. **Verify** — A verification phase allows a second expert to review and confirm each annotation
6. **Export** — Finished annotations are exported for statistical analysis or use as machine-learning training data

## Spectrogram Viewer

The annotation interface displays a spectrogram labelled with time and frequency axes. Several tools are available directly in the viewer:

- **FFT selector** — Choose between available FFT window sizes (e.g. 512, 1024, 2048, 4096) to trade time resolution for frequency resolution
- **Frequency scale** — Switch between linear, audible, and multi-linear scales designed for specific taxa (e.g. odontocetes, large baleen whales)
- **Zoom** — Zoom into time segments using the zoom buttons or the mouse wheel; each zoom level is pre-computed for instant loading
- **Audio playback** — Listen to the recording with adjustable playback speed (0.25× to 4×); click on the spectrogram to set the playback position

## Data Preparation

APLOSE expects pre-segmented audio files and pre-calculated spectrograms. No computation is performed inside the platform, which keeps loading times short during annotation sessions.

The recommended preparation pipeline uses the **APLOSE Audio Processor** Python package, which can:

- Resample audio to a target sample rate
- Split long recordings into fixed-length snippets with optional overlap
- Skip leading transients with a configurable time offset
- Generate spectrograms for one or more FFT sizes
- Export 16-bit grayscale PNG images with JSON metadata for fast browser display

See the [APLOSE Audio Processor documentation](https://github.com/sebastianmenze/APLOSE-IMR/tree/main/aplose_audio_processor) for installation and usage instructions.

## Technology

APLOSE is built with a **Django** REST backend and a **React / TypeScript** frontend. Spectrograms are pre-computed from audio files using a Python pipeline and served as PNG images paired with JSON metadata files that store the dB scale information needed for accurate display.

User accounts, annotation campaigns, and results are stored in a PostgreSQL database. The platform is deployed as a Docker container for reproducibility and portability.

## Getting Started

1. **Request an account** — Contact the administrator to obtain login credentials (there is no self-registration)
2. **Log in** — Click "Login" in the header and enter your credentials
3. **Join a campaign** — Navigate to "Annotation Campaigns" to find campaigns you have been assigned to
4. **Annotate** — Open a file from the campaign page and start annotating; your work is saved automatically
5. **Export results** — Administrators can export annotation results from the campaign management page

## Contact

For questions about the IMR OceanSound deployment, contact **sebastian.menze@imr.no** or open an issue on [GitHub](https://github.com/sebastianmenze/APLOSE-IMR/issues).
