# Mars Terrain Segmentation

A personal algorithm-engineering learning case built around **AI4MARS**: inspect real rover imagery, establish a CNN segmentation baseline, analyze errors, and later compare a Transformer model.

## Current status

Dataset download is handed off to the user. Automated local and GitHub Actions downloads have been canceled, and incomplete local data has been removed. No complete AI4MARS dataset or trained model is currently included in this repository.

The selected source is **AI4MARS merged v0.6**, a 16,232,481,989-byte ZIP linked from the [NASA Open Data catalog](https://data.nasa.gov/dataset/ai4mars-a-dataset-for-terrain-aware-autonomous-driving-on-mars) to [Zenodo record 15995036](https://zenodo.org/records/15995036).

Full image/mask data belongs in `data/raw/`. The large dataset archive is distributed separately from ordinary Git history, through an optional checksum-verified GitHub Release. Source versions and checksums are recorded in `metadata/`.

## Download

```bash
python3 scripts/download_data.py --connections 8
```

This resumes interrupted transfers, checks the official MD5, checks ZIP CRCs and extracts the original structure. `HTTPS_PROXY` can be set if your network requires a proxy. The script does not select or change any system proxy.

Allow at least 60 GB of free space for original archives, resumable parts and extracted data. The helper workflow is manually dispatched and publishes data only after the official checksum passes.

## Learning scope

Start with one rover/camera subset and a CNN segmentation baseline. Inspect image/mask alignment, ignored pixels, class imbalance and terrain confusion before changing the model. Keep expert evaluation masks separate. Transformer comparisons and model-quality results are future work.

## Attribution and data terms

AI4Mars was created by R. Michael Swan, Deegan Atha, Henry A. Leopold, Matthew Gildner, Stephanie Oij, Cindy Chiu and Masahiro Ono, with NASA JPL and citizen-science contributors. Cite *AI4MARS: A Dataset for Terrain-Aware Autonomous Driving on Mars*, CVPR Workshops 2021.

The selected Zenodo record declares [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Dataset copyrights and attribution remain with their original owners. This repository is an independent learning project, not an official NASA project.
