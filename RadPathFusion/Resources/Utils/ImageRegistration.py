import SimpleITK as sitk
import numpy as np
        
class RegisterImages():
    def __init__(self):
        self.fixed = None
        self.moving = None
        self.initial_transform = None
        self.deformable_transform = None
        self.verbose = True
        
    def RegisterAffine(self, fixed_img, moving_img, initial_transf, debug=False     ):
        self.fixed  = sitk.Cast(fixed_img, sitk.sitkFloat32)
        self.moving = sitk.Cast(moving_img, sitk.sitkFloat32)
        
        self.initial_transform = initial_transf
                                                             
        
        if debug:
            moving_resampled = sitk.Resample(self.moving, self.fixed,
                self.initial_transform, sitk.sitkLinear, 0.0, self.moving.GetPixelID())
            sitk.WriteImage(moving_resampled,'moving.mha')
            sitk.WriteImage(self.fixed,'fixed.mha')

        registration_method = sitk.ImageRegistrationMethod()
        #registration_method.SetMetricAsMeanSquares()
        registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
        
        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.05)

        registration_method.SetInterpolator(sitk.sitkLinear)


        # Optimizer settings.
        registration_method.SetOptimizerAsGradientDescent(learningRate=.1, numberOfIterations=100, convergenceMinimumValue=1e-6, convergenceWindowSize=10)
        registration_method.SetOptimizerScalesFromPhysicalShift()

        # Setup for the multi-resolution framework.            
        registration_method.SetShrinkFactorsPerLevel(shrinkFactors = [16,8,4])
        registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[4,2,1])
        registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOff()

        # Don't optimize in-place, we would possibly like to run this cell multiple times.
        registration_method.SetInitialTransform(self.initial_transform, inPlace=False)
       
        final_transform = registration_method.Execute(self.fixed, self.moving)

        if debug:
            moving_resampled = sitk.Resample(self.moving, self.fixed,
                self.initial_transform, sitk.sitkLinear, 0.0, self.moving.GetPixelID())
            sitk.WriteImage(moving_resampled,'moved.mha')

        if self.verbose: 
            print("Done Running Affine Registration!")
            
        return final_transform

    def RegisterDeformable(self, fixed_img, moving_img, initial_transf, dist_between_grid_points = 10, idx = 0, debug=False):
        """
            dist_between_grid_points is in mm. 
        """
        self.fixed  = sitk.Cast(fixed_img, sitk.sitkFloat32)
        self.moving = sitk.Cast(moving_img, sitk.sitkFloat32)
        
        #self.initial_transform = initial_transf
                                                             
        moved = sitk.Resample(self.moving, self.fixed, initial_transf, 
            sitk.sitkLinear, 0.0, self.moving.GetPixelID())

        # Determine the number of BSpline control points using the physical spacing we want for the control grid. 
        grid_physical_spacing = [dist_between_grid_points, dist_between_grid_points, dist_between_grid_points] # A control point every 50mm
        image_physical_size = [size*spacing for size,spacing in zip(self.fixed.GetSize(), moved.GetSpacing())]
        mesh_size = [int(image_size/grid_spacing + 0.5) \
                     for image_size,grid_spacing in zip(image_physical_size,grid_physical_spacing)]

        initial_transform = sitk.BSplineTransformInitializer(image1 = self.fixed, 
                                                             transformDomainMeshSize = mesh_size, order=3)    


        if debug:
            sitk.WriteImage(moved,'moving_deformable_{:d}.mha'.format(idx))
            sitk.WriteImage(self.fixed,'fixed_deformable_{:d}.mha'.format(idx))

        registration_method = sitk.ImageRegistrationMethod()
        #registration_method.SetMetricAsMeanSquares()
        registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
        
        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.05)

        registration_method.SetInterpolator(sitk.sitkLinear)


        # Optimizer settings.
        registration_method.SetOptimizerAsLBFGSB(gradientConvergenceTolerance=1e-5, numberOfIterations=10)
        #registration_method.SetOptimizerAsGradientDescent(learningRate=.1, numberOfIterations=100, convergenceMinimumValue=1e-6, convergenceWindowSize=10)
        #registration_method.SetOptimizerScalesFromPhysicalShift()

        # Setup for the multi-resolution framework.            
        registration_method.SetShrinkFactorsPerLevel(shrinkFactors = [16,8,4])
        registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[4,2,1])
        registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOff()

        registration_method.SetInitialTransform(initial_transform)
	
        #scales = np.ones(mesh_size[0]*mesh_size[1])
        #print(scales)
        #for s in scales:
        #    s = 1
        #print(scales)
        #registration_method.SetOptimizerScales(scales)
        
        
        final_transform = registration_method.Execute(self.fixed, moved)
        
        if debug:
            moving_resampled = sitk.Resample(moved, self.fixed,
                final_transform, sitk.sitkLinear, 0.0, self.moving.GetPixelID())
            print(np.max(sitk.GetArrayFromImage(moving_resampled)))
            sitk.WriteImage(moving_resampled,'moved_deformable_{:d}.mha'.format(idx))

        if self.verbose: 
            print("Done Running Deformable Registration!")
            
        return final_transform