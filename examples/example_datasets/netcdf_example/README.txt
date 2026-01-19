NetCDF Example Dataset
======================

This is a template dataset structure for NetCDF spectrograms.

To generate the actual NetCDF spectrogram files, run:

    python ../../generate_netcdf_dataset.py --output . --name netcdf_example

This will populate the spectrogram/ directory with 5 example NetCDF files.

Alternatively, place your own NetCDF spectrogram files in:
    processed/netcdf_analysis/spectrogram/

The files should follow the naming convention:
    YYYY_MM_DD_HH_MM_SS_ffffff.nc

And must match the entries in:
    processed/netcdf_analysis/netcdf_analysis.json
