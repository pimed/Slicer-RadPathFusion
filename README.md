# Slicer-RadPathFusion
Contains the Slicer Extension for radiology pathology fusion

# Install

## Requirements

* Download [3D Slicer](https://download.slicer.org/)
* Download [Elastix 4.9.0](https://github.com/SuperElastix/elastix/releases/tag/4.9.0).
* Clone    Slicer-RadPathFusion (this repository) 

## How to install 

1. Open 3D Slicer
2. Edit > Application Settings > Modules > Add
3. Choose path to Slicer-RadPathFusion / RadPathFusion
4. Choose Ok, Yes (Note! This will restart slicer)

# How to use

1. Open Slicer
2. Modules > Radiology-Pathology Fusion


# To do

1. Parse Json
* add progress bar at loading
* add ability to actually load and edit loaded json (not only the volumes and masks)
* add ability to create new Json files or json entry
1. Reconstruction 
* Add functionality for reconstruction
1. RadPathFusion
*. Multi-threaded
*. Dynamic instead of Hardcoded path for elastix
