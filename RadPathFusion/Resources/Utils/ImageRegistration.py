import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
import time
        
class RegisterImages():
    def __init__(self):
        self.fixed = None
        self.moving = None
        self.initial_transform = None
        self.deformable_transform = None
        self.verbose = False
        
        
        # Callback invoked when the StartEvent happens, sets up our new data.
    def start_plot(self):
        global metric_values, multires_iterations
        
        metric_values = []
        multires_iterations = []

    # Callback invoked when the EndEvent happens, do cleanup of data and figure.
    def end_plot(self):
        global metric_values, multires_iterations
        
        del metric_values
        del multires_iterations
        # Close figure, we don't want to get a duplicate of the plot latter on.
        plt.close()

    # Callback invoked when the IterationEvent happens, update our data and display new figure.    
    def plot_values(self, registration_method, fn):
        global metric_values, multires_iterations
        
        metric_values.append(registration_method.GetMetricValue())                                       
        # Plot the similarity metric values
        plt.plot(metric_values, 'r')
        plt.plot(multires_iterations, [metric_values[index] for index in multires_iterations], 'b*')
        plt.xlabel('Iteration Number',fontsize=12)
        plt.ylabel('Metric Value',fontsize=12)
        #plt.show()
        plt.savefig(fn)
        
        
    # Callback invoked when the IterationEvent happens, update our data and display new figure.    
    def get_values(self, registration_method):
        global metric_values, multires_iterations
        
        metric_values.append(registration_method.GetMetricValue())                                       
        print("RegisterImages: ",len(metric_values), registration_method.GetMetricValue())
        
    # Callback invoked when the sitkMultiResolutionIterationEvent happens, update the index into the 
    # metric_values list. 
    def update_multires_iterations(self):
        global metric_values, multires_iterations
        multires_iterations.append(len(metric_values))   
            
    def RegisterAffine(self, fixed_img, moving_img, initial_transf, idx = 0, debug=False):
        if debug:
            start_time = time.time()
            moving_resampled = sitk.Resample(moving_img, fixed_img,
                initial_transf, sitk.sitkLinear, 0.0, fixed_img.GetPixelID())
            sitk.WriteImage(moving_resampled,'{:d}_moving.mha'.format(idx))
            sitk.WriteImage(fixed_img,'{:d}_fixed.mha'.format(idx))
            
        self.fixed  = sitk.Cast(fixed_img, sitk.sitkFloat32)
        self.moving = sitk.Cast(moving_img, sitk.sitkFloat32)
        
        self.initial_transform = initial_transf
                                                             
        


        registration_method = sitk.ImageRegistrationMethod()
        registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)

        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.01)

        registration_method.SetInterpolator(sitk.sitkLinear)


        # Optimizer settings.
        registration_method.SetOptimizerAsGradientDescent(learningRate=.2, 
            numberOfIterations=250, convergenceMinimumValue=1e-4, convergenceWindowSize=30)
        #registration_method.SetOptimizerAsGradientDescent(learningRate=.1, 
        #    numberOfIterations=100, convergenceMinimumValue=1e-6, convergenceWindowSize=10)
        #registration_method.SetOptimizerScalesFromPhysicalShift()

        # Setup for the multi-resolution framework.            
        #registration_method.SetShrinkFactorsPerLevel(shrinkFactors = [16,8,4])
        #registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[4,2,1])
        registration_method.SetShrinkFactorsPerLevel(shrinkFactors = [32,16,8,4])
        registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[8,4,2,1])
        #registration_method.SetShrinkFactorsPerLevel(shrinkFactors = [32,16,8])
        #registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[8,4,2])
        #
        # Uncomment these following 2lines for phantom study
        #
        #registration_method.SetShrinkFactorsPerLevel(shrinkFactors = [2,1])
        #registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2,1])
        registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOff()

        # Don't optimize in-place, we would possibly like to run this cell multiple times.
        registration_method.SetInitialTransform(self.initial_transform, inPlace=False)
        
        if debug:
            registration_method.AddCommand(sitk.sitkStartEvent, self.start_plot)
            registration_method.AddCommand(sitk.sitkEndEvent, self.end_plot)
            registration_method.AddCommand(sitk.sitkMultiResolutionIterationEvent, self.update_multires_iterations) 
            registration_method.AddCommand(sitk.sitkIterationEvent, lambda: self.get_values(registration_method))
            registration_method.AddCommand(sitk.sitkIterationEvent, lambda: self.plot_values(registration_method, '{:d}_plot.png'.format(idx)))
       
        final_transform = registration_method.Execute(self.fixed, self.moving)
        
        if debug:
            print('RegisterImages: Final metric value: {0}'.format(registration_method.GetMetricValue()))
            print('RegisterImages: Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))

        if debug:
            end_time = time.time()
            print(final_transform)
            moving_resampled = sitk.Resample(self.moving, self.fixed,
                final_transform, sitk.sitkLinear, 0.0, moving_img.GetPixelID())
            sitk.WriteImage(moving_resampled,'{:d}_moved.mha'.format(idx))
            print("RegisterImages: Done Running Affine Registration in", (end_time-start_time)/60, "(min)")

        if self.verbose: 
            print("RegisterImages: Done Running Affine Registration!")
            
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
            print("RegisterImages: Done Running Deformable Registration!")
            
        return final_transform