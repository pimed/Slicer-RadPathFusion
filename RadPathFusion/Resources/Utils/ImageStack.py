import os
import json
import numpy as np
import SimpleITK as sitk
from ImageRegistration import RegisterImages

class PathologyVolume():

    def __init__(self, parent=None):
        self.verbose    = False
        self.path       = None

        self.noRegions  = 0
        self.regionIDs  = None
        self.noSlices   = 0
        # in micrometers
        self.pix_size_x = 0
        self.pix_size_y = 0

        # max image size
        self.maxSliceSize = [0,0]
        self.volumeSize   = [0,0,0]
        self.rgbVolume    = None
        self.storeVolume  = False

        self.inPlaneScaling     = 1.2
         
        self.pathologySlices    = None
        self.jsonDict           = None
        
        #filenames if needed to load here
        self.imagingContraintFilename       = None
        self.imagingContraintMaskFilename   = None
        
        #files 
        self.imagingContraint       = None
        self.imagingContraintMask   = None
        
        self.volumeOrigin       = None
        self.volumeDirection    = None
        self.volumeSpacing      = None
        
        self.refWoContraints    = None
        self.refWContraints     = None
        self.mskRefWoContraints = None
        self.mskRefWContraints  = None
        self.doAffine           = True
        self.doDeformable       = None

        self.successfulInitialization = False;
    
    def initComponents(self):
        """
        Reads json and identifies size needed for output volume; 
        Does NOT Read the actual images; Does NOT Create the volume
        """
        if self.verbose:
            print("PathologyVolume: Initialize components") 

        if not self.path:
            print("The path was not set");
            self.successfulInitialization = False
            return 0;

        if self.verbose:
            print("PathologyVolume: Loading from", self.path)
        
        try:
            data = json.load(open(self.path))
        except Exception as e:
            print(e)
            self.successfulInitialization = False
            return 0
        self.jsonDict = data

        self.pix_size_x = 0
        self.pix_size_y = 0

        self.pathologySlices = []
        self.regionIDs = []
        for key in np.sort(list(self.jsonDict)):
            ps            = PathologySlice()
            ps.jsonKey    = key
            ps.rgbImageFn = data[key]['filename']
            ps.maskDict   = data[key]['regions']
            try: # new format
                ps.transformDict = data[key]['transform']
                ps.doFlip     = ps.transformDict['flip']
                ps.doRotate   = ps.transformDict['rotation_angle']
            except: #old format
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
            
            for r in list(data[key]['regions']):
                if not r in self.regionIDs:
                    self.regionIDs.append(r)
            self.noRegions = len(self.regionIDs)
            
            # set the list with region ID so the slice know what ids to assign to
            # regions that are global
            ps.regionIDs = self.regionIDs
            
            self.pathologySlices.append(ps)
  
  
            xml_res_x = None
            try: #new xml format
                xml_res_x = float(data[key]['resolution_x_um'])
            except: #old xml format
                xml_res_x = float(data[key]['resolution_x'])
                
            xml_res_y = None                
            try: #new xml format
                xml_res_y = float(data[key]['resolution_y_um'])
            except: #old xml format
                xml_res_y = float(data[key]['resolution_y'])

            if self.pix_size_x==0 and xml_res_x>0:
                self.pix_size_x = xml_res_x
            if self.pix_size_y==0 and xml_res_y>0:
                self.pix_size_y = xml_res_y
                
            if self.pix_size_x > xml_res_x:
                self.pix_size_x = xml_res_x
            if self.pix_size_y > xml_res_y:
                self.pix_size_y = xml_res_y


        self.noSlices = len(list(data))
        self.volumeSize = [int(self.maxSliceSize[0]*self.inPlaneScaling),
            int(self.maxSliceSize[1]*self.inPlaneScaling), 
            self.noSlices]

        if self.verbose:
            print("PathologyVolume: Found {:d} slices @ max size {}".format(self.noSlices,
                self.maxSliceSize))
            print("PathologyVolume: Create volume at {}".format(self.volumeSize))
        
        self.successfulInitialization = True;
        return 1

    def printTransform(self, ref=None):
        for i, ps in enumerate(self.pathologySlices):
            print(i, ps.transform)

    def setPath(self, path):
        self.path=path

    def loadRgbVolume(self): 
        if self.verbose:
            print("Loading RGB")
        # create new volume with white background
        vol = sitk.Image(self.volumeSize, sitk.sitkVectorUInt8, 3)
        if self.volumeOrigin:
            vol.SetOrigin(self.volumeOrigin)
        if self.volumeDirection:
            vol.SetDirection(self.volumeDirection)          
        isSpacingSet = False
        if self.volumeSpacing:
            vol.SetSpacing(self.volumeSpacing)
            isSpacingSet = True
            
            
        # fill the volume
        # put ps.im in vol at index ps.idx
        for i, ps in enumerate(self.pathologySlices):
            if self.verbose:
                print("Loading slice", i)
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
            #print("Rotate in sl",i, ps.doRotate, self.pathologySlices[i].doRotate)
            relativeIdx = int(i>0)
            vol = ps.setTransformedRgb(vol, relativeIdx)


        if self.storeVolume:
            self.rgbVolume = vol
            return self.rgbVolume
        else:
            return vol
            
    def loadMask(self, idxMask=0):
        # create new volume with 
        vol = sitk.Image(self.volumeSize, sitk.sitkUInt8)
        if self.volumeOrigin:
            vol.SetOrigin(self.volumeOrigin)
        if self.volumeDirection:
            vol.SetDirection(self.volumeDirection)
        isSpacingSet = False
        if self.volumeSpacing:
            vol.SetSpacing(self.volumeSpacing)
            isSpacingSet = True
            
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
 
            relativeIdx = int(i>0)
            vol = ps.setTransformedMask(vol, idxMask, relativeIdx)

        return vol
        
    def getInfo4UI(self):
        data = []
        
        for idx, ps in enumerate(self.pathologySlices):
            masks = []
            for mask_key in list(ps.maskDict):
                fn = ps.maskDict[mask_key]['filename']
                try:
                    readIdxMask = int(mask_key[6:])
                except:
                    readIdxMask = 1
                masks.append([readIdxMask, fn])
                
            el = [idx,
                ps.refSliceIdx+1, #start count from 1 in the UI
                ps.rgbImageFn, 
                masks, 
                ps.doFlip, 
                ps.doRotate]
            data.append(el)
        
        return data
        
    def updateSlice(self, idx, param, value):
        if len(self.pathologySlices)> idx:
            #the transorm needs to be updated
            self.pathologySlices[idx].transform  = None 
            jsonKey = False
            if param  == 'slice_number':
                """
                oldKey = 'slice'+str(idx)
                newKey = 'slice'+str(int(value))
                print("Changing", oldKey, newKey)
                self.jsonDict[newKey] = self.jsonDict[self.pathologySlices[idx].jsonKey]
                self.pathologySlices[idx].jsonKey = newKey
                if not oldKey == newKey:
                    del self.jsonDict[oldKey]
                """
                
                self.pathologySlices[idx].refSliceIdx = value 
                jsonKey = True
                jsonValue = value+1
                
            if param  == 'filename':
                self.pathologySlices[idx].rgbImageFn = value
                jsonKey = True           
                jsonValue = str(value)
                
            if param  == 'flip':
                self.pathologySlices[idx].doFlip = value
                jsonKey = True   
                jsonValue = value
                
            if param  == 'rotation_angle':
                
                self.pathologySlices[idx].doRotate = value
                jsonKey = True        
                print('Rotating', idx,self.pathologySlices[idx].doRotate )
                jsonValue = value
                
            if not jsonKey:
                print("Adding new key", param)
                
            if param  == 'flip' or param  == 'rotation_angle':
                #if not 'transform' in self.jsonDict[self.pathologySlices[idx].jsonKey]['transform']:
                #key doesn't not exit
                if not 'transform' in self.jsonDict[self.pathologySlices[idx].jsonKey]:
                    self.jsonDict[self.pathologySlices[idx].jsonKey]['transform']={}
                self.jsonDict[self.pathologySlices[idx].jsonKey]['transform'][param] = jsonValue
            else:
                self.jsonDict[self.pathologySlices[idx].jsonKey][param] = jsonValue
            
    def updateSliceMask(self, idxSlice, idxMask, param, value):
        if len(self.pathologySlices)> idxSlice:
            #the transorm needs to be updated
            
            jsonKey = False
            if param  == 'key':
                oldKey = 'region'+str(idxMask)
                newKey = 'region'+str(int(value))
                self.pathologySlices[idxSlice].maskDict[newKey] = self.pathologySlices[idxSlice].maskDict[oldKey]
                del self.pathologySlices[idxSlice].maskDict[oldKey]
                
            if param  == 'filename':
                self.pathologySlices[idxSlice].maskDict['region'+str(idxMask)]['filename'] = value
                    

    def saveJson(self, path_out_json):
        if self.verbose: 
            print("Saving Json File")
        
        with open(path_out_json, 'w') as outfile:
            json.dump(self.jsonDict, outfile, indent=4, sort_keys=True)

    def getConstraint(self):
    
        # if we have a filename but not volume
        if not self.imagingContraint and self.imagingContraintFilename:
            try:
                self.imagingContraint  = sitk.ReadImage(self.imagingContraintFilename,sitk.sitkFloat32)
            except Exception as e:
                print(e)
        
        # if we have a filename but not mask        
        if not self.imagingContraintMask and self.imagingContraintMaskFilename:
            try:
                self.imagingContraintMask = sitk.ReadImage(self.imagingContraintMaskFilename)
            except Exception as e:
                print(e)

        self.imagingContraintMask = sitk.Cast(
            sitk.Resample(self.imagingContraintMask>0, 
                self.imagingContraint, 
                sitk.Transform(), 
                sitk.sitkNearestNeighbor),
            sitk.sitkUInt16)            
            
        ### get bounding box
        labelStats = sitk.LabelStatisticsImageFilter()
        labelStats.Execute(self.imagingContraint, self.imagingContraintMask)
        box     = labelStats.GetBoundingBox(1)
        
        ### pad the box
        pad = 15
        minX = box[0]-pad
        if box[0]-pad<0:
            minX = 0
        maxX = box[1]+pad
        if box[1]+pad>self.imagingContraint.GetSize()[0]:
            maxX = self.imagingContraint.GetSize()[0]
        minY = box[2]-pad
        if box[2]-pad<0:
            minY = 0
        maxY = box[3]+pad
        if box[3]+pad>self.imagingContraint.GetSize()[1]:
            minY = self.imagingContraint.GetSize()[1]         
        cropImC = self.imagingContraint[minX:maxX,minY:maxY,box[4]:box[5]+1]
        boxSize = cropImC.GetSize()
        sp      = self.imagingContraint.GetSpacing()
        

        ### create image with the same pixel size as the pathology volume, 
        ### but containting the contraint
        #convert mm (from constraint) to um from histology
        roiSize = [int(boxSize[0]*1000*sp[0]/self.pix_size_x),
            int(boxSize[1]*1000*sp[1]/self.pix_size_y),
            int(boxSize[2])]
        roiSp   = [self.pix_size_x/1000.0, self.pix_size_y/1000.0, sp[2]]
        constraint = sitk.Image(roiSize, sitk.sitkUInt16)      
        constraint.SetSpacing(roiSp)
        constraint.SetOrigin(cropImC.GetOrigin())
        constraint.SetDirection(cropImC.GetDirection())

        ##Resample to the new size
        imCM = sitk.Cast(
            sitk.Resample(self.imagingContraintMask, constraint, sitk.Transform(), sitk.sitkNearestNeighbor),
            sitk.sitkUInt16)

        imC = sitk.Cast(
            sitk.Resample(self.imagingContraint, constraint, sitk.Transform(), sitk.sitkLinear),
            sitk.sitkUInt16)
        
        #sitk.WriteImage(imC, "moving3d.mha")
        
        imC = imC*imCM
        constraint_range=[i for i in range(imC.GetSize()[2])]

        return imC, constraint_range
            
    def registerSlices(self, useImagingConstaint=False):
    
        
        if not useImagingConstaint:
            if (not self.doAffine and not self.doDeformable ):
                print("Nothing to be done as no affine and no deformable were selected")
                return
        
        self.store_volume = True
        ref = self.loadRgbVolume()
        refMask = self.loadMask(0)

        ### if constraints are set, then use them and output the volume relative 
        ### to the constraint
        if useImagingConstaint:
            if (self.imagingContraintFilename and self.imagingContraintMaskFilename) or (self.imagingContraint and self.imagingContraintMask):
                imC, constraint_range = self.getConstraint()
                self.volumeSize         = imC.GetSize()
                self.volumeOrigin       = imC.GetOrigin()
                self.volumeDirection    = imC.GetDirection()
                self.volumeSpacing      = imC.GetSpacing()
            else:
                print("Using Imaging Constraints was set, but no filenames were set")
                print("set magingContraintFilename and imagingContraintMaskFilename")
                print("No contraints will be used")
                useImagingConstaint = False
                return
            
                                

            self.refWContraints     = self.loadRgbVolume()
            self.mskRefWContraints  = self.loadMask(0)

            if self.verbose:
                sitk.WriteImage(imC, "fixed3D.nii.gz")
                sitk.WriteImage(ref, "reference3D.nii.gz")
                
            for imov in range(self.noSlices):
                if imov >= len(constraint_range):
                    break
                ifix = constraint_range[imov]
                print("----Refine slice to imaging constraint", imov, ifix, "------")
                movPs = self.pathologySlices[imov]
                movPs.doAffine      = self.doAffine
                movPs.doDeformable  = self.doDeformable
                        
                print("Do affine 1:",movPs.doAffine)
                print("Do deformable 1:",movPs.doDeformable)

                if self.refWoContraints == None or  self.mskRefWContraints==None:
                    movPs.registerToConstrait(imC[:,:,ifix], self.refWContraints,self.mskRefWContraints, ref, refMask, ifix)
                else:
                    movPs.registerToConstrait(imC[:,:,ifix], self.refWoContraints,self.mskRefWoContraints, ref, refMask, ifix)

        else:
            self.refWoContraints = ref
            self.mskRefWoContraints = self.loadMask(0)
            
            
            length = len(self.pathologySlices)
            middleIdx = int(length/2)+1
            idxFixed = []
            idxMoving = []
            for i in range(middleIdx-1,length-1):
                idxFixed.append(i)
                idxMoving.append(i+1)
            for i in range(middleIdx-1, 0, -1):
                idxFixed.append(i)
                idxMoving.append(i-1)
            
            #print(idxFixed)
            #print(idxMoving)
            
            ### register consecutive histology slices
            for ifix,imov in zip(idxFixed,idxMoving):
                print("----Registering slices", ifix, imov, "------")
                fixPs = self.pathologySlices[ifix]
                movPs = self.pathologySlices[imov]
                movPs.doAffine      = self.doAffine
                movPs.registerTo(fixPs, ref, refMask, True, 10+imov)

                
    def deleteData(self):
        print("Deleting Volume")
        for ps in self.pathologySlices:
            ps.deleteData()
        self.__init__()

class PathologySlice():

    def __init__(self):
        self.verbose    = False
        self.id         = None
        self.rgbImageFn = None
        self.maskDict   = None
        self.doFlip     = None
        self.doRotate   = None

        self.rgbImageSize   = None
        self.rgbPixelType   = None
        self.dimension      = None
        self.rgbImage       = None
        self.storeImage     = False

        #once the slice gets projected on the reference model, we have all this information
        self.transform      = None
        self.refSize        = None
        self.refSpacing     = None
        self.refOrigin      = None
        self.refDirection   = None
        self.refSliceIdx    = None # which slice in the reference volume

        self.unitMode       = 0 #microns; 1-milimeters

        self.regionIDs      = None
        self.doAffine       = True
        self.doDeformable   = None
        

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
            print("PathologySlice: Reading from \'{0}\'".format( self.rgbImageFn) )
            print("PathologySlice: Image Size     : {0}".format(self.rgbImageSize))
            #print("Image PixelType: {0}".format(self.rgbPixelType))

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
            print("PathologySlice: Reading {:d} ({:d},{}) from \'{}\'".format(self.refSliceIdx, 
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
            
    def getGrayFromRGB(self, im, invert=True):
        select  = sitk.VectorIndexSelectionCastImageFilter()
        im_gray = select.Execute(im, 0, sitk.sitkUInt8)/3
        im_gray +=select.Execute(im, 1, sitk.sitkUInt8)/3
        im_gray +=select.Execute(im, 2, sitk.sitkUInt8)/3
       
        if invert:
            im_gray  = 255 - im_gray
            
        
        return im_gray
        

    def loadMask(self, idxMask):
        if not self.maskDict:
            print("No mask information was provided");
            return None

        maskFn = None
        for mask_key in list(self.maskDict):
            fn = self.maskDict[mask_key]['filename']
            for idxRegion, r in enumerate(self.regionIDs):
                if mask_key == r:
                    readIdxMask = idxRegion
            
            if self.verbose:
                print("PathologySlice: Mask:", idxMask, readIdxMask, fn)

            if readIdxMask == idxMask:
                maskFn = fn

        if self.verbose and not maskFn:
            print("PathologySlice: Mask", idxMask, "not found for slice", self.refSliceIdx)

        if not maskFn:
            return None

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
            print("PathologySlice: Reading {:d} from \'{}\'".format(self.refSliceIdx, maskFn))

        return im

    def setReference(self, vol): 
        # Sets only the characteristics of the refence, not the actual volume        
        self.refSize      = vol.GetSize()
        self.refSpacing   = vol.GetSpacing()
        self.refOrigin    = vol.GetOrigin()
        self.refDirection = vol.GetDirection()

        # when setting a new reference, the Transform needs to be recomputed
        self.transform = None

    def computeCenterTransform(self, im, ref, relativeIdx=0, mode = 0, doRotate=None, tranform_type = 0):
        # 
        #Input
        #----
        #im:  sitk vector image - 2D RGB
        #ref: sitk vector image - 3D RGB
        #relative IDX - if 0 - ref is the same index as as self, 
        #                  1 - ref is one before
        #mode: int: 0 rgb, 1-grayscale

        #get first channel, needed for input of CenteredTransform
        if not mode:
            select = sitk.VectorIndexSelectionCastImageFilter()
            im0  = select.Execute(im, 0, sitk.sitkUInt8)/3
            im0  += select.Execute(im, 1, sitk.sitkUInt8)/3
            im0  += select.Execute(im, 2, sitk.sitkUInt8)/3
            
            # since rgb also invert the intensities
            im0 = 255-im0
            
            # if there are more slices in the exvivo than invivo
            try: 
                ref0 = select.Execute(ref[:,:,self.refSliceIdx-relativeIdx], 0, sitk.sitkUInt8)/3
                ref0 += select.Execute(ref[:,:,self.refSliceIdx-relativeIdx], 1, sitk.sitkUInt8)/3
                ref0 += select.Execute(ref[:,:,self.refSliceIdx-relativeIdx], 2, sitk.sitkUInt8)/3
            except Exception as e:
                print (e)
                ref0 = select.Execute(ref[:,:,self.refSliceIdx-1], 0, sitk.sitkUInt8)/3
                ref0 += select.Execute(ref[:,:,self.refSliceIdx-1], 1, sitk.sitkUInt8)/3
                ref0 += select.Execute(ref[:,:,self.refSliceIdx-1], 2, sitk.sitkUInt8)/3
            
            ref0 = 255-ref0            
        else:
            im0 = im
            
            # if there are more slices in the exvivo than invivo
            try:
                ref0 = ref[:,:,self.refSliceIdx-relativeIdx]
            except Exception as e:
                print (e)
                ref0 = ref[:,:,self.refSliceIdx-1]

        if self.verbose:
            print("Computing Center of mass", self.refSliceIdx, np.max(sitk.GetArrayFromImage(im0)), 
                np.min(sitk.GetArrayFromImage(ref0)), np.max(sitk.GetArrayFromImage(ref0)), doRotate)
        
        """
        transform = None     
        try:
            tr = sitk.CenteredTransformInitializer(ref0, im0, 
                sitk.AffineTransform(im.GetDimension()), 
                sitk.CenteredTransformInitializerFilter.MOMENTS)
            transform = sitk.AffineTransform(tr)    
            print("Using COM")
        except:
            tr = sitk.CenteredTransformInitializer(ref0, im0, 
                sitk.AffineTransform(im.GetDimension()), 
                sitk.CenteredTransformInitializerFilter.GEOMETRY)
            print("Using Geometric")
            transform = sitk.AffineTransform(tr)    
            
        self.transform = sitk.Transform(transform)
        """
        
        #try to limit the numbers of transorms at this step, first rotate then translate
        if doRotate:
            center = ref0.TransformContinuousIndexToPhysicalPoint(
                np.array(ref0.GetSize())/2.0)
                
            if tranform_type == 0:
                rotation = sitk.AffineTransform(im0.GetDimension())
                rotation.Rotate(0,1,np.radians(doRotate))
            else:
                rotation = sitk.Euler2DTransform()
                rotation.SetAngle(np.radians(doRotate))
                
            rotation.SetCenter(center)
            
            #self.transform.AddTransform(rotation)
            self.transform = sitk.Transform(rotation)
            
            #apply rotation
            im0 = sitk.Resample(im0, ref0, self.transform)
        else:
            self.transform = None
                 
        # recompute centering
        transform = None     
        try:
            tr = sitk.CenteredTransformInitializer(ref0, im0, 
                sitk.AffineTransform(im.GetDimension()), 
                sitk.CenteredTransformInitializerFilter.MOMENTS)
            transform = sitk.AffineTransform(tr)
            if self.verbose:
                print("Using COM")
        except:
            tr = sitk.CenteredTransformInitializer(ref0, im0, 
                sitk.AffineTransform(im.GetDimension()), 
                sitk.CenteredTransformInitializerFilter.GEOMETRY)
            if self.verbose:
                print("Using Geometric")
            transform = sitk.AffineTransform(tr)     

        if self.transform:
            self.transform.AddTransform(transform)
        else:
            self.transform = sitk.Transform(transform)
            

    def getFlipped(self, im):
        flipped_im = sitk.Flip(im, (False, True))

        return flipped_im 

    def setTransformedRgb(self, ref, relativeIdx):
        im = self.loadRgbImage()

        #nothing was read
        if not im:
            return ref
            
        #print("Set Transformed image", self.doRotate)

        if not self.transform:
            self.computeCenterTransform(im, ref, relativeIdx, 0, self.doRotate)
            
            
        #print(self.refSliceIdx, self.transform)

        try:    
            im_tr  = sitk.Resample(im, ref[:,:,self.refSliceIdx], self.transform,
                sitk.sitkNearestNeighbor,255)
            ref_tr = sitk.JoinSeries(im_tr)
            ref    = sitk.Paste(ref, ref_tr, ref_tr.GetSize(), 
                destinationIndex=[0,0,self.refSliceIdx])    
        except Exception as e:
            print(e)
            im_tr  = sitk.Resample(im, ref[:,:,self.refSliceIdx-1], self.transform,
                sitk.sitkNearestNeighbor, 255)
            ref_tr = sitk.JoinSeries(im_tr)
            ref    = sitk.Paste(ref, ref_tr, ref_tr.GetSize(), 
                destinationIndex=[0,0,self.refSliceIdx])  



        return ref 

    def setTransformedMask(self, ref, idxMask, relativeIdx):
        im = self.loadMask(idxMask)
        
        #nothing was read
        if not im:
            return ref

        if not self.transform:
            self.computeCenterTransform(im, ref, relativeIdx, 1, self.doRotate)
       
        try:    
            im_tr  = sitk.Resample(im, ref[:,:,self.refSliceIdx], 
                    self.transform, 
                    sitk.sitkNearestNeighbor)
            ref_tr = sitk.JoinSeries(im_tr)
            ref    = sitk.Paste(ref, ref_tr, ref_tr.GetSize(), 
                destinationIndex=[0,0,self.refSliceIdx])
        except Exception as e:
            print(e)
            print("The index doesn't exist",self.refSliceIdx)
            im_tr  = sitk.Resample(im, ref[:,:,self.refSliceIdx-1], 
                    self.transform, 
                    sitk.sitkNearestNeighbor)
            ref_tr = sitk.JoinSeries(im_tr)
            ref    = sitk.Paste(ref, ref_tr, ref_tr.GetSize(), 
                destinationIndex=[0,0,self.refSliceIdx])

        return ref 
 
    def registerTo(self, refPs, ref, refMask, applyTranf2Ref = True, idx = 0):
        if applyTranf2Ref:
            old = refPs.refSliceIdx
            refPs.refSliceIdx = self.refSliceIdx
            fixed_image = refPs.setTransformedRgb(ref, 1)[:,:,self.refSliceIdx]
            refPs.refSliceIdx = old
        else:
            fixed_image = refPs.loadRgbImage()
        
        #sitk.WriteImage(refPs.setTransformedRgb(ref, 1),"{:02d}_Fixed.nii.gz".format(idx))
        #sitk.WriteImage(refPs.setTransformedMask(refMask,0,1),"{:02d}_Fixed_mask.nii.gz".format(idx))
        
        fixed_image  = self.getGrayFromRGB(fixed_image)
        moving_image = self.loadRgbImage()
        moving_image = self.getGrayFromRGB(moving_image)
        
        #apply mask to fixed image
        try:
            if applyTranf2Ref:
                fixed_mask = refPs.setTransformedMask(refMask,0,1)[:,:,refPs.refSliceIdx]  
            else:
                fixed_mask = refPs.loadMask(0)
        except Exception as e:
            print("No mask 0 was found")
            fixed_mask = None
         
        if fixed_mask:
            fixed_mask = sitk.Cast(sitk.Resample(fixed_mask,fixed_image, sitk.Transform(), 
                sitk.sitkNearestNeighbor, 0.0, fixed_image.GetPixelID())>0,
                fixed_image.GetPixelID())
                
            #sitk.WriteImage(fixed_image,"{:02d}_Fixed_im1.nii.gz".format(idx))
            #sitk.WriteImage(fixed_mask,"{:02d}_Fixed_mask1.nii.gz".format(idx))
            fixed_image = fixed_image*fixed_mask
            
            
            
        #apply mask to moving image
        try:
            moving_mask = self.loadMask(0)
        except Exception as e:
            print("No mask 0 was found")
            moving_mask = None
         
        if moving_mask:
            moving_mask = sitk.Cast(sitk.Resample(moving_mask, moving_image, sitk.Transform(), 
                sitk.sitkNearestNeighbor, 0.0, moving_image.GetPixelID())>0,
                moving_image.GetPixelID())
                
            #sitk.WriteImage(moving_image,"{:02d}_Moving_im.nii.gz".format(idx))
            #sitk.WriteImage(moving_mask,"{:02d}_Moving_mask.nii.gz".format(idx))                
            moving_image = moving_image*moving_mask
        
        
        if self.verbose:
            print("PathologySlice: Do no constraints affine:",self.doAffine)
            print("PathologySlice: Do no constraints deformable:",self.doDeformable)
        
        if self.doAffine:
            reg = RegisterImages()
            self.transform = reg.RegisterAffine(fixed_image, moving_image, self.transform, idx, 1)
      
            
    def registerToConstrait(self, fixed_image, refMov, refMovMask, ref, refMask, idx, applyTranf = True):  
        if applyTranf:
            moving_image =  self.setTransformedRgb(ref, 0)[:,:,self.refSliceIdx]  
        else:
            moving_image = self.loadRgbImage()
        
        moving_image = self.getGrayFromRGB(moving_image)
          
        # if image has mask; use it!
        try:
            if applyTranf:
                mask =  self.setTransformedMask(refMask,0,0)[:,:,self.refSliceIdx]  
            else:
                mask = self.loadMask(0)
        except Exception as e:
            print("No mask 0 was found")
            mask = None
        
        if mask:
            mask = sitk.Cast(sitk.Resample(mask, moving_image, sitk.Transform(), 
                sitk.sitkNearestNeighbor, 0.0, moving_image.GetPixelID())>0,
                moving_image.GetPixelID())
            
            moving_image = moving_image*mask
            
        
        if self.verbose:
            sitk.WriteImage(fixed_image,"{:02d}_Center_Fixed.nii.gz".format(idx))
            sitk.WriteImage(moving_image,"{:02d}_Center_Moving.nii.gz".format(idx))

        # use moments, except if mask doesn't exist then use geometric
        try:
            transform = sitk.CenteredTransformInitializer(
                    sitk.Cast(fixed_image>0, sitk.sitkFloat32), 
                    sitk.Cast(moving_image>0, sitk.sitkFloat32),
                    sitk.AffineTransform(moving_image.GetDimension()), 
                    sitk.CenteredTransformInitializerFilter.MOMENTS)
        except:
            transform = sitk.CenteredTransformInitializer(
                    sitk.Cast(fixed_image, sitk.sitkFloat32), 
                    sitk.Cast(moving_image, sitk.sitkFloat32), 
                    sitk.AffineTransform(moving_image.GetDimension()), 
                    sitk.CenteredTransformInitializerFilter.GEOMETRY)

        # if affine and deformable are not done, then just center. 
        #if not self.doAffine and not self.doDeformable:
        # center by COM
        self.transform.AddTransform(transform)
            
        
        if self.verbose:
            print("PathologySlice: Do constraints affine:",self.doAffine)
            print("PathologySlice: Do constraints deformable:",self.doDeformable)
            
        reg = RegisterImages()
        
        # reload moving, without transform, so the transform gets to be identified in the affine registration
        # starting with the COM alignment. 
        moving_image = self.loadRgbImage()
        moving_image = self.getGrayFromRGB(moving_image)
        mask = self.loadMask(0)
        if mask:
            mask = sitk.Cast(sitk.Resample(mask, moving_image, sitk.Transform(), 
                sitk.sitkNearestNeighbor, 0.0, moving_image.GetPixelID())>0,
                moving_image.GetPixelID())
            
            moving_image = moving_image*mask
            
        if self.verbose:
            moved_image = sitk.Resample(moving_image, fixed_image,
                self.transform, sitk.sitkLinear, 0.0, fixed_image.GetPixelID())
            sitk.WriteImage(moved_image,"{:02d}_Center_Moved.nii.gz".format(idx))
 
        if self.doAffine:
            self.transform = reg.RegisterAffine(sitk.Cast(fixed_image>0, sitk.sitkFloat32)*255, 
                sitk.Cast(moving_image>0, sitk.sitkFloat32)*255, self.transform, idx, 0, 0, True, False)
            #self.transform = reg.RegisterAffine(fixed_image,moving_image, self.transform, idx, 0, 1, True, False)
            #self.transform = reg.RegisterAffine(sitk.Cast(fixed_image, sitk.sitkFloat32)/np.max(sitk.GetArrayFromImage(fixed_image))*255, 
            #    sitk.Cast(moving_image, sitk.sitkFloat32)/np.max(sitk.GetArrayFromImage(moving_image))*255,
            #    self.transform, idx, 0, 0, True, False)

        if self.doDeformable:
            transform_def = reg.RegisterDeformable(fixed_image, moving_image, self.transform, 10, idx)
            self.transform.AddTransform(transform_def)

    def deleteData(self):
        print("Deleting Slice")
        self.__init__();
