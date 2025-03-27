import argparse
import os
import sys

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the local library (assuming it's in a subdirectory called "mylibrary")
library_path = os.path.join(current_dir, '..', "RadPathFusion","Resources","Utils")
if os.path.exists(library_path):
    sys.path.append(library_path)
    from ImageStack import PathologyVolume
else:
    print(f"Error: Library not found at {library_path}")

from test_run_registration import getInputStack    
import json
import SimpleITK as sitk

def apply_transform(input_stack, trans_dict, out_path, extension='nii.gz'):
    ###
    # Apply registration transforms to any file
    ###
    
    os.makedirs(out_path, exist_ok=True)
    
    #write the input, before transformation
    
    inIm = input_stack.loadRgbVolume()
    case_id = input_stack.pathologySlices[0].id
    print(out_path,case_id, extension, inIm.GetSize())
    inIm = sitk.Cast(inIm, sitk.sitkVectorUInt8)
    fn = os.path.join(out_path,case_id+"_input_highres_rgb."+extension)
    sitk.WriteImage(inIm, fn)
    
    #write labels high-res
    #write Labels in vivo resolution
    nr = input_stack.noRegions
    rIds = input_stack.regionIDs
    for i in range(nr):
        print(i,nr, rIds[i])
        inMsk = input_stack.loadMask(i)
        fn = os.path.join(out_path,"{:s}_input_highres_{:s}_label.{:s}".format(case_id, rIds[i],extension))
        sitk.WriteImage(inMsk, fn)   
        
    input_stack.imagingContraintFilename       = trans_dict['fixed']
    input_stack.imagingContraintMaskFilename   = trans_dict['fixed-segmentation']
    
    trs = []
    for idx, s in enumerate(trans_dict['transforms'].keys()):
        fn_tr = trans_dict['transforms'][s]['transform_fn']
        print (s, fn_tr)
        tr = sitk.ReadTransform(fn_tr)
        #not sure if this one works, lets see
        
        ##FIXME for some reason this didn't work
        #input_stack.pathologySlices[idx].tranform = tr
        trs.append(tr)

        
    #input_stack.printTransform()
    moved=input_stack.applyTransformsOntoConstraint(trs)
    
    #write rgb high-res
    #moved = input_stack.loadRgbVolume()
    print(moved.GetOrigin())
    moved = sitk.Cast(moved, sitk.sitkVectorUInt8)
    fn = os.path.join(out_path,case_id+"_moved_highres_rgb."+extension)
    sitk.WriteImage(moved, fn)
    
   
    rIds = input_stack.regionIDs
    rIds = input_stack.regionIDs
    nr1   = input_stack.noRegions
    nr = range(nr1)
   
    
    
    for i,id in enumerate(nr):
        #print(i,nr, rIds[i])
        moved = input_stack.applyTransformsOntoConstraintMask(i, trs)
        fn = os.path.join(out_path,"{:s}_moved_highres_{:s}_label.{:s}".format(case_id,rIds[i],extension))
        sitk.WriteImage(moved, fn)
     
        """
        #not prostate, urethra, landmarks
        #everything else: cancer, cancer from automated 
        if (not rIds == "00") and (not rIds == "09") and (not rIds == "10"): 
            try:
                moved_invivo = post_process_labels(moved)
            except Exception as e:
                print("Something went wrong when smoothing labels")
                print(e)
                moved_invivo = moved
        moved_invivo = sitk.Resample(moved_invivo, fixed_msk, sitk.Transform(), sitk.sitkNearestNeighbor)
        moved_invivo = moved_invivo*sitk.Cast(fixed_msk>0,sitk.sitkUInt8)
        fn = os.path.join(path,"{:s}_moved_{:s}_label.{:s}".format(studyParser.id,rIds[i],extension))
        sitk.WriteImage(moved_invivo, fn)
        """

   


    return
    
    
    

if __name__=="__main__": 
    parser = argparse.ArgumentParser(description='Parse data')
    parser.add_argument('-v','--verbose', action='store_true',
        help='verbose output')
    parser.add_argument('-ii','--in_path_ImagesToTransform', type=str, required=True,
        default=".",help="json file")
    parser.add_argument('-it','--in_path_Transforms', type=str, required=True,
        default=".",help="json file")
    parser.add_argument('-o','--out_path', type=str, required=True,
        default=".",help="json file")
        
    opt = parser.parse_args()
    print(opt)
    
    # get the image stack to transform
    input_stack = getInputStack(opt.in_path_ImagesToTransform)
    
    #get the transform json dict
    with open(opt.in_path_Transforms,'r') as infile:
        trans_dict = json.load(infile)
        
    apply_transform(input_stack, trans_dict, opt.out_path)
    
    