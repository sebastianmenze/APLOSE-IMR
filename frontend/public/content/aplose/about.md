# About APLOSE

APLOSE (Annotation Platform for Ocean Sound Exploration) is a web-based platform for visualising and annotating underwater acoustic recordings, developed at the [Institute of Marine Research (IMR)](https://www.hi.no/en).

## What APLOSE Does

APLOSE provides a collaborative environment for marine biologists, acoustic researchers, and annotators to:

- Visualise spectrograms from hydrophone recordings
- Create and manage annotation campaigns
- Label acoustic events with species or sound type labels
- Track annotation progress across teams
- Export annotations in standard formats (CSV, RAVEN, JSON)

## The Annotation Workflow

1. **Import** — An administrator imports a processed acoustic dataset into APLOSE
2. **Campaign** — A campaign is created, defining the dataset, label set, and assigned annotators
3. **Annotate** — Annotators draw bounding boxes on spectrograms to mark acoustic events
4. **Export** — Completed annotations are exported for downstream analysis

## Technology

APLOSE is built with a Django backend and a React/TypeScript frontend. Spectrograms are generated from audio files using a Python preprocessing pipeline and served as PNG images or NetCDF data.

The source code is available on [GitHub](https://github.com/Project-OSmOSE/osmose-app).

## Contact

For questions about the platform, please contact the IMR acoustic team or open an issue on GitHub.
