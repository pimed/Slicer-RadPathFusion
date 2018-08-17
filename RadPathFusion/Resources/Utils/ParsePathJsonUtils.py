"""
Author: Mirabela Rusu
Created: 2018 Aug 16
"""
from __future__ import print_function
import os
import json
import numpy as np
import SimpleITK as sitk

class ParsePathJsonUtils():
    def __init__(self):
        self.verbose = True
        self.path = None
        self.pathologyVolume = PathologyVolume()
        self.storeVolume = False

    def setPath(self, path):
        self.path=path
    
    def initComponents(self):
        if self.verbose:
            print("initialize components") 
        if self.path:
            self.pathologyVolume.setPath(self.path)
            self.pathologyVolume.initComponents()


class PathologyVolume():

    def __init__(self, parent=None):
        self.verbose = True
        self.path = None

        self.no_regions = None
        self.noSlices = 0
        # in micrometers
        self.pix_size_x = None
        self.pix_size_y = None

        # max image size
        self.maxSliceSize = [0,0]
        self.volumeSize   = [0,0,0]
        self.rgbVolume    = None
        self.storeVolume  = False

        self.inPlaneScaling = 1.2
         
        self.pathologySlices = None
    

    def initComponents(self):
        if self.verbose:
            print("initialize components") 

        if not self.path:
            print("The path was not set");
            return 0;

        if self.verbose:
            print("Loading from", self.path)
        
        data = json.load(open(self.path))

        pix_size_x = 1
        pix_size_y = 1

        self.pathologySlices = []

        for key in np.sort(list(data)):
            ps = PathologySlice()
            ps.rgbImageFn = data[key]['filename']
            ps.maskDict   = data[key]['regions']
            ps.doFlip     = int(data[key]['flip']) 
            ps.doRotate   = data[key].get('rotate',None)
            ps.loadImageSize()
            size = ps.rgbImageSize

            for dim in range(ps.dimension):
                if (self.maxSliceSize[dim]<size[dim]):
                    self.maxSliceSize[dim] = size[dim]

            idx = data[key].get('slice_number', None)
            if idx:
                # assumes numbering in the json file starting from 1
                # but in python starts at 0
                ps.refSliceIdx = int( idx )-1
            else:
                ps.refSliceIdx = len(self.pathologySlices)
            self.pathologySlices.append(ps)
            
            if self.no_regions < len(list(data[key]['regions'])):            
                self.no_regions = len(list(data[key]['regions']))

            if self.pix_size_x > float(data[key]['resolution_x']):
                self.pix_size_x = float(data[key]['resolution_x'])
            if self.pix_size_y > float(data[key]['resolution_y']):
                self.pix_size_y = float(data[key]['resolution_y'])


        self.noSlices = len(list(data))
        self.volumeSize = [int(self.maxSliceSize[0]*self.inPlaneScaling),
            int(self.maxSliceSize[1]*self.inPlaneScaling), 
            self.noSlices]

        if self.verbose:
            print("Found {:d} slices @ max size {}".format(self.noSlices,
                self.maxSliceSize))
            print("Create volume at {}".format(self.volumeSize))


    def setPath(self, path):
        self.path=path

    def loadRgbVolume(self):      
        # create new volume with white background
        vol = sitk.Image(self.volumeSize, sitk.sitkVectorUInt8, 3)

        isSpacingSet = False
        # fill the volume
        # put ps.im in vol at index ps.idx
        for i, ps in enumerate(self.pathologySlices):
            if not isSpacingSet:
                im = ps.loadRgbImage()
            
                if not im:
                    continue

                # set spacing based on the first image spacing
                im_sp = im.GetSpacing()
                vol_sp = [s for s in im_sp]
                vol_sp.append(1.0) 
                vol.SetSpacing(vol_sp)
                isSpacingSet = True
           
            if not ps.refSize:
                ps.setReference(vol) 
            vol = ps.setTransformedRgb(vol)


        if self.storeVolume:
            self.rgbVolume = vol
            return self.rgbVolume
        else:
            return vol
            
    def loadMask(self, idxMask=0):
        # create new volume with 
        vol = sitk.Image(self.volumeSize, sitk.sitkUInt8)

        isSpacingSet = False
        # fill the volume
        # put ps.im in vol at index ps.idx
        for i, ps in enumerate(self.pathologySlices):
            if not isSpacingSet:
                im = ps.loadMask(idxMask)
            
                if not im:
                    continue

                # set spacing based on the first image spacing
                im_sp = im.GetSpacing()
                vol_sp = [s for s in im_sp]
                vol_sp.append(1.0) 
                vol.SetSpacing(vol_sp)
                isSpacingSet = True
          
            if not ps.refSize:
                ps.setReference(vol)
 
            vol = ps.setTransformedMask(vol, idxMask)

        return vol


class PathologySlice():

    def __init__(self):
        self.id = None
        self.rgbImageFn = None
        self.maskDict   = None
        self.doFlip     = None
        self.doRotate   = None

        self.rgbImageSize = None
        self.rgbPixelType = None
        self.dimension    = None
        self.rgbImage   = None
        self.storeImage = False

        #once the slice gets projected on the reference model, we have all this information
        self.transform  = None
        self.refSize    = None
        self.refSpacing = None
        self.refOrigin  = None
        self.refDirection= None
        self.refSliceIdx= None # which slice in the reference volume

        self.unitMode   = 0 #microns; 1-milimeters

        self.verbose    = True

    def loadImageSize(self):
        #Attention: This doesn't actually load the image, just reads the header information
        if not self.rgbImageFn:
            print("The path to the rgb images was not set");
            return None;
    
        reader = sitk.ImageFileReader()
        reader.SetFileName( str(self.rgbImageFn) )
        reader.LoadPrivateTagsOn()
        reader.ReadImageInformation()
        
        self.rgbImageSize = reader.GetSize()
        self.rgbPixelType = sitk.GetPixelIDValueAsString(reader.GetPixelID())
        self.dimension = reader.GetDimension()

        if self.verbose:
            print("Reading from \'{0}\'".format( self.rgbImageFn) )
            print("Image Size     : {0}".format(self.rgbImageSize))
            print("Image PixelType: {0}".format(self.rgbPixelType))

    def loadRgbImage(self):
        if not self.rgbImageFn:
            print("The path to the rgb images was not set");
            return None

        try:
            rgbImage = sitk.ReadImage(str(self.rgbImageFn))
        except Exception as e:
            print(e)
            print("Couldn't read", self.rgbImageFn)
            return None

        #need to units to mm
        #if self.unitMode==0:
        #    rgbImage.SetSpacing([s/1000.0 for s in rgbImage.GetSpacing()])


        if self.verbose:
            print("Reading {:d} ({:d},{}) from \'{}\'".format(self.refSliceIdx, 
                self.doFlip, 
                self.doRotate,
                self.rgbImageFn) )

        #FIXME: use simple ITK (for some reason sitk.Flip and ::-1 didn't work)
        if (not self.doFlip==None) and self.doFlip==1:
            arr = sitk.GetArrayFromImage(rgbImage)
            arr = arr[:,arr.shape[1]:0:-1,:]
            rgbImage2 = sitk.GetImageFromArray(arr, isVector = True)
            rgbImage2.SetSpacing(rgbImage.GetSpacing()) 
            rgbImage2.SetOrigin(rgbImage.GetDirection()) 
            rgbImage2.SetDirection(rgbImage.GetDirection()) 
            rgbImage = rgbImage2 
            


        if self.storeImage:
            # the volume was converted in the other unit above, but just note store info
         #   if self.unitMode==0:
         #       self.unitMode = 1
            self.rgbImage = rgbImage
            return self.rgbImage
        else:
            return rgbImage

    def loadMask(self, idxMask):
        if not self.maskDict:
            print("No mask information was provided");
            return None

        maskFn = None
        for mask_key in list(self.maskDict):
            fn = self.maskDict[mask_key]['filename']
            #FIXME: should be consistent with the slice idx (which is read from tag 
            #slice_number)
            try:
                readIdxMask = int(mask_key[6:])
            except:
                readIdxMask = 1

            if self.verbose:
                print(idxMask, readIdxMask, fn)

            if readIdxMask == idxMask:
                maskFn = fn

        if not maskFn:
            print("Mask", idxMask, "not found for slice", self.refSliceIdx)

        try:
            im = sitk.ReadImage(str(maskFn))
        except Exception as e:
            print(e)
            print("Couldn't read", maskFn)
            return None

        #depending how the masks are made, they may either be a grayscale image 
        # (in house script bases on svs import) or a rgba image (gimp) 
        if im.GetNumberOfComponentsPerPixel()>1:
            select = sitk.VectorIndexSelectionCastImageFilter()
            im  = select.Execute(im, 0, sitk.sitkUInt8) 
           
        #FIXME: use simple ITK (for some reason sitk.Flip and ::-1 didn't work)
        if (not self.doFlip==None) and self.doFlip==1:
            arr = sitk.GetArrayFromImage(im)
            arr = arr[:,arr.shape[1]:0:-1]
            im2 = sitk.GetImageFromArray(arr)
            im2.SetSpacing(im.GetSpacing()) 
            im2.SetOrigin(im.GetDirection()) 
            im2.SetDirection(im.GetDirection()) 
            im =im2
 
        if self.verbose:
            print("Reading {:d} from \'{}\'".format(self.refSliceIdx, maskFn))

        return im

    def setReference(self, vol): 
        # Sets only the characteristics of the refence, not the actual volume        
        self.refSize      = vol.GetSize()
        self.refSpacing   = vol.GetSpacing()
        self.refOrigin    = vol.GetOrigin()
        self.refDirection = vol.GetDirection()

        # when setting a new reference, the Transform needs to be recomputed
        self.transform = None

    def computeCenterTransform(self, im, ref, mode = 0, doRotate=None):
        # 
        #Input
        #----
        #im:  sitk vector image - 2D RGB
        #ref: sitk vector image - 3D RGB
        #mode: int: 0 rgb, 1-grayscale

        #get first channel, needed for input of CenteredTransform
        if not mode:
            select = sitk.VectorIndexSelectionCastImageFilter()
            im0  = select.Execute(im, 0, sitk.sitkUInt8)
            ref0 = select.Execute(ref[:,:,self.refSliceIdx], 0, sitk.sitkUInt8)
        else:
            im0 = im
            ref0 = ref[:,:,self.refSliceIdx]

        tr = sitk.CenteredTransformInitializer(ref0, im0, 
            sitk.AffineTransform(im.GetDimension()), 
            sitk.CenteredTransformInitializerFilter.GEOMETRY)
        
        self.transform = sitk.AffineTransform(tr)

        if doRotate:
            center = ref0.TransformContinuousIndexToPhysicalPoint(
                np.array(ref0.GetSize())/2.0)
            rotation = sitk.AffineTransform(im0.GetDimension())
            rotation.Rotate(0,1,np.radians(doRotate))
            rotation.SetCenter(center)

            composite = sitk.Transform(im.GetDimension(), sitk.sitkComposite)
            composite.AddTransform(self.transform)
            composite.AddTransform(rotation)
            self.transform = composite

    def getFlipped(self, im):
        flipped_im = sitk.Flip(im, (False, True))

        return flipped_im 

    def setTransformedRgb(self, ref):
        im = self.loadRgbImage()

        #nothing was read
        if not im:
            return ref


        if not self.transform:
            self.computeCenterTransform(im, ref, 0, self.doRotate)
            
        try:    
            im_tr  = sitk.Resample(im, ref[:,:,self.refSliceIdx], self.transform)
            ref_tr = sitk.JoinSeries(im_tr)
            ref    = sitk.Paste(ref, ref_tr, ref_tr.GetSize(), 
                destinationIndex=[0,0,self.refSliceIdx])    
        except Exception as e:
            print(e)
            print(im_tr, ref_tr, ref)


        return ref 

    def setTransformedMask(self, ref, idxMask):
        im = self.loadMask(idxMask)
        
        #nothing was read
        if not im:
            return ref

        if not self.transform:
            self.computeCenterTransform(im, ref, 1, self.doRotate)
       
        try:    
            im_tr  = sitk.Resample(im, ref[:,:,self.refSliceIdx], 
                    self.transform, 
                    sitk.sitkNearestNeighbor)
            ref_tr = sitk.JoinSeries(im_tr)
            ref    = sitk.Paste(ref, ref_tr, ref_tr.GetSize(), 
                destinationIndex=[0,0,self.refSliceIdx])
        except Exception as e:
            print(e)
            print(im_tr, ref_tr, ref)

        return ref 
    

