import os
import sys
import json

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the local library (assuming it's in a subdirectory called "mylibrary")
library_path = os.path.join(current_dir, '..', "RadPathFusion","Resources","Utils")
if os.path.exists(library_path):
    sys.path.append(library_path)
    from ImageStack import PathologyVolume
else:
    print(f"Error: Library not found at {library_path}")
    
    
    

from parse_registration_json import ParserRegistrationJson
from parse_study_dict import ParserStudyDict

import argparse

import time
import SimpleITK as sitk

def post_process_labels(msk_in):    
    # work well for page 3 and deep bio annotations
    print(msk_in.GetSize())
    msk_out = sitk.SmoothingRecursiveGaussian(msk_in, 0.250)
    msk_out = sitk.Cast(msk_out>255*1/4,sitk.sitkUInt8)

    return msk_out

def output_results(path, studyParser, inputStack, imStack,
    discard_orientation = False, extension = "nii.gz", debug = False):
    #create folder
    try:
        os.mkdir(path)
    except OSError as e:
        print ("Creation of the directory %s failed" % path)
        print (e)
    else:
        print ("Successfully created the directory %s " % path)
    
    #### save the transforms    
    json_transf = {}
    for ps in imStack.pathologySlices:
        slice_key = ps.jsonKey 
        fn = os.path.join(path, studyParser.id+"_transform_"+slice_key+".tfm")
        tr = ps.transform
        tr.FlattenTransform()
        #print(fn, ps.transform)
        sitk.WriteTransform(ps.transform, fn)
        json_transf[slice_key] = {"transform_fn":fn}
    
    big_json = { "transforms": json_transf, 
        "fixed": os.path.join(path,studyParser.id+"_fixed_image."+extension), 
        "fixed-segmentation": os.path.join(path,studyParser.id+"_fixed_mask_label."+extension)  }
       
    json_transf_fn = os.path.join(path, studyParser.id+"_transform.json")
    with open(json_transf_fn, 'w') as outfile:
        json.dump(big_json, outfile, indent=4, sort_keys=True)
    

    output_path = os.path.join(path,str(studyParser.id))
    if not debug:
        #try output all inputs: T2, ADC, DWI
        img = None
        try:
            img = studyParser.ReadImage(studyParser.T2_filename)
        except Exception as e:
            print(e)
        
        if img:
            if discard_orientation:
                tr = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
                img.SetDirection(tr)
            fn = os.path.join(path,studyParser.id+"_input_T2."+extension)
            sitk.WriteImage(img, fn)

        img = None
        try:
            img = studyParser.ReadImage(studyParser.ADC_filename)
            
        except Exception as e:
            print(e)
        
        
        if img:
            if discard_orientation:
                tr = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
                img.SetDirection(tr)
            fn = os.path.join(path,studyParser.id+"_input_ADC."+extension)
            sitk.WriteImage(img, fn)
            save_path = os.path.join(path,studyParser.id)
            
            #write out ADC segmentation
            if studyParser.ADC_segmentation_filename:
                ADC_seg = sitk.ReadImage(studyParser.ADC_segmentation_filename, sitk.sitkUInt8)
                sitk.WriteImage(ADC_seg, output_path+"_input_ADC_mask_label.nii.gz")
            
            path_T2_segmentation = os.path.join(path,studyParser.id+"_input_T2."+extension)
            registerADCtoT2(os.path.join(path,studyParser.id+"_input_T2."+extension),fn,save_path, 
                studyParser.fixed_segmentation_filename,
                studyParser.ADC_segmentation_filename)

        img = None
        try:
            img = studyParser.ReadImage(studyParser.DWI_filename)
        except Exception as e:
            print(e)
        
        if img:
            if discard_orientation:
                tr = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
                img.SetDirection(tr)
            fn = os.path.join(path,studyParser.id+"_input_DWI."+extension)
            sitk.WriteImage(img, fn)
    
    if studyParser.CG_segmentation_filename and os.path.exists(studyParser.CG_segmentation_filename):
        CG_seg = sitk.ReadImage(studyParser.CG_segmentation_filename, sitk.sitkUInt8)
        Pr_seg = sitk.Cast(sitk.ReadImage(studyParser.fixed_segmentation_filename, sitk.sitkUInt8)>0, sitk.sitkUInt8)
        CG_seg = sitk.Resample(CG_seg, Pr_seg, sitk.Transform(), sitk.sitkNearestNeighbor)

        CG_seg *= Pr_seg # only have CG within the prostate
        sitk.WriteImage(CG_seg, output_path+"_input_T2_CG_mask_label.nii.gz")

    #read and write inputs
    fixed_img = studyParser.ReadImage(studyParser.fixed_filename)
    fixed_msk = studyParser.ReadImage(studyParser.fixed_segmentation_filename)

    if discard_orientation:
        tr = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        fixed_img.SetDirection(tr)
        fixed_msk.SetDirection(tr)
    
    
    fn = os.path.join(path,studyParser.id+"_fixed_image."+extension)
    sitk.WriteImage(fixed_img, fn)

    fn = os.path.join(path,studyParser.id+"_fixed_mask_label."+extension)
    sitk.WriteImage(fixed_msk, fn)


    
    #write labels high-res
    #write Labels in vivo resolution

    rIds = imStack.regionIDs
    if not debug:
        rIds = imStack.regionIDs
        nr1   = imStack.noRegions
        nr = range(nr1)
    else:
        rIds1 = imStack.regionIDs
        nr1   = imStack.noRegions
        
        nr = []
        rIds = []
        for i,r in enumerate(rIds1):
            if int(r[6:len(r)])<=10:
                #nr += 1
                rIds.append(r)
                nr.append(i)

    print("Run Registration: Debug", debug, nr)
    
    
    for i,id in enumerate(nr):
        #print(i,nr, rIds[i])
        moved = imStack.loadMask(id)
        fn = os.path.join(path,"{:s}_moved_highres_{:s}_label.{:s}".format(studyParser.id,rIds[i],extension))
        sitk.WriteImage(moved, fn)
        
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


    #write rgb high-res
    moved = imStack.loadRgbVolume()
    moved = sitk.Cast(moved, sitk.sitkVectorUInt8)
    fn = os.path.join(path,studyParser.id+"_moved_highres_rgb."+extension)
    sitk.WriteImage(moved, fn)
    
    if not debug:
        #write rgb high-res
        inIm = inputStack.loadRgbVolume()
        inIm = sitk.Cast(inIm, sitk.sitkVectorUInt8)
        fn = os.path.join(path,studyParser.id+"_input_highres_rgb."+extension)
        sitk.WriteImage(inIm, fn)
        
        #write labels high-res
        #write Labels in vivo resolution
        nr = inputStack.noRegions
        rIds = imStack.regionIDs
        for i in range(nr):
            print(i,nr, rIds[i])
            if i>2:
                break
            inMsk = inputStack.loadMask(i)
            fn = os.path.join(path,"{:s}_input_highres_{:s}_label.{:s}".format(studyParser.id, rIds[i],extension))
            sitk.WriteImage(inMsk, fn)
    


def register(fixed_fn, fixed_mask_fn, moving_fn, doReconstruct = True,
    useImagingConstraints = True, doAffine=True, doDeformable = False,
    fastExecution = False, discard_orientation = False):

    print("Starting Registration")
    
    im_stack = PathologyVolume()
    
    if not (doAffine==None):
        im_stack.doAffine   = doAffine
    im_stack.doDeformable   = doDeformable
    im_stack.doReconstruct  = doReconstruct
    im_stack.fastExecution  = fastExecution
    im_stack.discardOrientation = discard_orientation
    
    im_stack.setPath(moving_fn)
    im_stack.initComponents()
            
    print("Run Registration: Run Fast:      ",im_stack.fastExecution)
    print("Run Registration: Do reconstruct:",im_stack.doReconstruct)
    print("Run Registration: Do affine:     ",im_stack.doAffine)
    print("Run Registration: Do deformable: ",im_stack.doDeformable)
    print("Run Registration: Use Imaging Constraints:",useImagingConstraints)



    im_stack.registerSlices()

    im_stack.imagingContraintFilename       = fixed_fn
    im_stack.imagingContraintMaskFilename   = fixed_mask_fn

    ### only if value is provided, then assign, because affine should be on by default
    if not (doAffine==None):
        im_stack.doAffine   = doAffine
    im_stack.doDeformable   = doDeformable
      
    print("Run Registration: Run Fast:      ",im_stack.fastExecution)
    print("Run Registration: Do reconstruct:",im_stack.doReconstruct)
    print("Run Registration: Do affine:     ",im_stack.doAffine)
    print("Run Registration: Do deformable: ",im_stack.doDeformable)
    print("Run Registration: Use Imaging Constraints:",useImagingConstraints)
    
    if useImagingConstraints:
        im_stack.registerSlices(useImagingConstraints)
        
        
    return im_stack

def registerADCtoT2(fixed_path,moving_path,save_path,
    fixed_seg_path = None, moving_seg_path= None):
    print("Start registering")
    
    fixed_image = sitk.ReadImage(fixed_path, sitk.sitkFloat32) #T2
    moving_image = sitk.ReadImage(moving_path,sitk.sitkFloat32)#ADC
    
    fixed_seg = None
    moving_seg = None
    if fixed_seg_path and moving_seg_path:
        fixed_seg  = sitk.ReadImage(fixed_seg_path, sitk.sitkFloat32)
        moving_seg = sitk.ReadImage(moving_seg_path, sitk.sitkFloat32)
        fixed_seg = sitk.Resample(fixed_seg, fixed_image, sitk.Transform(), sitk.sitkNearestNeighbor)
        moving_seg = sitk.Resample(moving_seg, moving_image, sitk.Transform(), sitk.sitkNearestNeighbor)
        
        fixed_image *= fixed_seg
        moving_image *= moving_seg
        
        
    

    #set fixed image mask
    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    registration_method.SetMetricSamplingPercentage(0.2)
    #if fixed_seg and moving_seg:
    #    registration_method.SetMetricFixedMask(fixed_seg)
    #    registration_method.SetMetricMovingMask(moving_seg)
        
    registration_method.SetInterpolator(sitk.sitkLinear)
    registration_method.SetOptimizerAsGradientDescent(learningRate=0.1, numberOfIterations=100,convergenceMinimumValue=1e-4, convergenceWindowSize=10)
    registration_method.SetOptimizerScalesFromPhysicalShift()
    registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4,2,1])
    registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2,1,0])
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    #registration_method.SetInitialTransform(sitk.TranslationTransform(3), inPlace=False)
    
    initial_transform = sitk.AffineTransform(sitk.CenteredTransformInitializer(fixed_image, 
                                                                            moving_image, 
                                                                            sitk.AffineTransform(3), 
                                                                            sitk.CenteredTransformInitializerFilter.MOMENTS))
                                                                            
    registration_method.SetInitialTransform(initial_transform, inPlace=False)
    translation_transform = registration_method.Execute(sitk.Cast(fixed_image, sitk.sitkFloat32),sitk.Cast(moving_image, sitk.sitkFloat32))
    moving_image = sitk.ReadImage(moving_path,sitk.sitkFloat32)#ADC
    translation_reg = sitk.Resample(moving_image,fixed_image,translation_transform,sitk.sitkLinear,0.0,moving_image.GetPixelID())
    sitk.WriteImage(translation_reg, save_path +'_T2ADC_translation.nii.gz')
    print("Done registering T2 and ADC")
    print ("Results in", save_path +'_T2ADC_translation.nii.gz')


def getInputStack(moving_fn):
    im_stack = PathologyVolume()
    im_stack.setPath(moving_fn)
    im_stack.initComponents()

    return im_stack
    
def main():

    
    parser = argparse.ArgumentParser(description='Parse data')
    parser.add_argument('-v','--verbose', action='store_true',
        help='verbose output')
    parser.add_argument('-i','--in_path', type=str, required=True,
        default=".",help="json file")
    opt = parser.parse_args()
    

    verbose = opt.verbose
    
    discard_orientation = False;

    timings = {}
    
    if verbose:
        print("Reading", opt.in_path)
            
    json_obj = ParserRegistrationJson(opt.in_path)
    
    for s in json_obj.studies:
        if json_obj.ToProcess:
            if not (s in json_obj.ToProcess):
                print("Skipping", s)
                continue
            
        print("x"*30, "Processing", s,"x"*30)
        studyDict = json_obj.studies[s]
        
        
        studyParser = ParserStudyDict(studyDict)
        moving_dict = studyParser.ReadMovingImage()
               
        if verbose:
            print(studyDict)
            print(studyParser.fixed_filename)
            print(moving_dict)

        do_mri_hist_register = True
        if do_mri_hist_register:
            start = time.time()
            imStack = register(studyParser.fixed_filename,
                studyParser.fixed_segmentation_filename,
                studyParser.moving_filename,
                json_obj.do_reconstruction,
                json_obj.use_imaging_constraints,
                json_obj.do_affine,
                json_obj.do_deformable,
                json_obj.fast_execution,
                discard_orientation
                )
            
            end = time.time()
            print("Registration done in {:6.3f}(min)".format((end-start)/60.0))
            
            timings[s] = (end-start)/60.0
            output_path = os.path.join(json_obj.output_path,str(studyParser.id))
            output_results(output_path, studyParser,
                getInputStack(studyParser.moving_filename),  imStack,
                discard_orientation)
   
   
        do_ADC_T2_registration = False
        if do_ADC_T2_registration:
            #try:
                ADC = None
                if len(studyParser.ADC_filename)>0 and os.path.exists(studyParser.ADC_filename):
                    output_path = os.path.join(json_obj.output_path,str(studyParser.id),str(studyParser.id))
                    ADC_seg = sitk.ReadImage(studyParser.ADC_segmentation_filename, sitk.sitkUInt8)
                    sitk.WriteImage(ADC_seg, output_path+"_input_ADC_mask_label.nii.gz")
                    registerADCtoT2(studyParser.fixed_filename,
                        studyParser.ADC_filename,
                        output_path,
                        studyParser.fixed_segmentation_filename,
                        studyParser.ADC_segmentation_filename)
            #except Exception as e:
            #    print(e)
            #    return
        do_write_Cg = False
        if do_write_Cg:
            output_path = os.path.join(json_obj.output_path,str(studyParser.id),str(studyParser.id))
            if len(studyParser.CG_segmentation_filename) > 0 and os.path.exists(studyParser.CG_segmentation_filename):
                CG_seg = sitk.ReadImage(studyParser.CG_segmentation_filename, sitk.sitkUInt8)
                Pr_seg = sitk.Cast(sitk.ReadImage(studyParser.fixed_segmentation_filename, sitk.sitkUInt8)>0, sitk.sitkUInt8)
                CG_seg = sitk.Resample(CG_seg, Pr_seg, sitk.Transform(), sitk.sitkNearestNeighbor)
        
                CG_seg *= Pr_seg # only have CG within the prostate
                sitk.WriteImage(CG_seg, output_path+"_input_T2_CG_mask_label.nii.gz")
                    
   
    print("Done!")

    return timings

if __name__=="__main__":
    timings = main()

    print("studyID",",", "Runtime (min)")
    for s in timings:
        print(s,",", timings[s])
