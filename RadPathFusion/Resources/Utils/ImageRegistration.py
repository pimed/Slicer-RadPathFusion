import SimpleITK as sitk
import numpy as np
        
class RegisterImages():
    def __init__(self):
        self.fixed = None
        self.moving = None
        self.initial_transform = None
        
    def Register(self, fixed_img, moving_img, initial_transf, debug=False):
    
        self.fixed  = sitk.Cast(fixed_img, sitk.sitkFloat32)
        self.moving = sitk.Cast(moving_img, sitk.sitkFloat32)
        
        self.initial_transform = initial_transf
                                                             
        
        if debug:
            moving_resampled = sitk.Resample(self.moving, self.fixed,
                self.initial_transform, sitk.sitkLinear, 0.0, self.moving.GetPixelID())
            sitk.WriteImage(moving_resampled,'moving.mha')
            sitk.WriteImage(self.fixed,'fixed.mha')

        registration_method = sitk.ImageRegistrationMethod()
        registration_method.SetMetricAsMeanSquares()
        
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
            
        return final_transform