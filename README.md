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


# Video tutorial

A short tutorial on how to run the registration can be found here: [https://youtu.be/B2o8EMmRsHw]

# How to use

1. Open Slicer 
2. Modules > Radiology-Pathology Fusion > Parse Pathology

# Use our test example

Example is case aaa0060 from [https://wiki.cancerimagingarchive.net/display/Public/Prostate+Fused-MRI-Pathology](https://wiki.cancerimagingarchive.net/display/Public/Prostate+Fused-MRI-Pathology). The case was pre-precessed and provided here to show the registration

1. Open Slicer 
* at the location of TCIA_Test_Case 

  ``` open terminal (that has python)
      cd Path_To_Slicer-RadPathFusion/TCIA_Test_Case
      "C:\Program Files\Slicer 4.9.0-2018-07-09\Slicer.exe" ```
      or 
  * make the paths to the data absolute in all json files    
2. go to Modules > Radiology-Pathology Fusion > Parse Pathology
3. Choose histopathology json file, e.g., the one provided as example  
4. In Slicer, load MRI and prostate segmentation on MRI
5. Push "Load Volume" to load the histopathology images a volume
6. Push "Load Mask" to see the different masks relative to the histopathology volume
6. Push "Refine Volume" to do a volume reconstruction
7. Push Register to Run the registraiton. !!! It will take a few minutes during which 3D Slicer will be frozen.



# How to run/test using command line

```
cd Path_To_Slicer-RadPathFusion/TCIA_Test_Case
python ..\CmdLineTools\test_run_registration.py -i registration.json
```
Notes:
* Script tested on Windows, proceed with care on Linux or Mac (biggest issues is associated with paths, so if it can't find the files, is because the paths in the json files don't work on our OS)
* Registration assumes slice-to-slice correspondances between radiology and pathology images. First slice in the MRI prostate segmentation corresponds to slice01 in histopathology json file. And so on so forth. 
* Some MRIs have an orientation information (a rotation transform - not identity- that can be displayed using sitkImage.GetOrientation()) especially if they are acquired with an endorectal coil. If the data has that issue, you can discard the orientation using the flag "Discard Orientation" in [test_run_registration]() on line 250. Set the flag to True by ```discard_orientation = True```
* Registration is a slow process, be patient!
* Registration overfits easily, often because of masks not matching well! If it happens, check the masks on both radiology and pathology images and update them to match better



# To do

1. Parse Json
* add progress bar at loading
* add ability to actually load and edit loaded json (not only the volumes and masks)
* add ability to create new Json files or json entry
1. Reconstruction 
* Add functionality for reconstruction
1. RadPathFusion
* Multi-threaded
* Dynamic instead of Hardcoded path for elastix

# Create RGB volume from the Histology Slices (using json)

In order to create a 3D RGB histology volume from the histology slices one needs to have already a json file [https://github.com/pimed/parse_data/blob/master/parse_digital_scans/parse_svs.py](https://github.com/pimed/parse_data/blob/master/parse_digital_scans/parse_svs.py). The path to tiff files within the json need to point to existing files. The ParsePathology module will allow one to load the stack of images and correct the rotation, flipping and order in the json file. 

1. Open Parse Pathology module: "ModuleMenu> RAdiology-Pathology Fusion > Parse Pathology"

Arguments:
1. Input json: select path to json file
1. Output volume: create a volume to see the 3D volume in slices
1. Output Mask: create a mask to show as mask
1. Mask ID: different regions have different id, so update as needed

Actions
1. Load Json: loads the json and shows it content
1. Load the volume: uses the entered information to create a volume 
1. Load Mask: as as Load volume


# IMPORTANT Tips on how to work around issues

1. Manually number the slices from 1.. and on word before loading volume
1. change the mask numbering: All same region in the stack should have the same index
    * WARNING
    * if there are 2 regions, eg. 0 and 1, that need to be changed, don't just write 1 instead of 0. That will internally delete the json information.
    * if 0 and 1 need to be swapped: type 2 instead of 1, type 1 instead of 0, type 0 instead of 2 
1. Close and reopen slicer to open a new json

