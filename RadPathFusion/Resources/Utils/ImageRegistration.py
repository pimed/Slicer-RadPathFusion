import SimpleITK as sitk
import numpy as np
        
class RegisterImages():
    def __init__(self):
        self.fixed = None
        self.moving = None
        self.initial_transform = None
        self.deformable_transform = None
        self.verbose = False
        
    def display_images(self, fixed_npa, fixed, moving, registration_method, fn):
        # Create a figure with two subplots and the specified size.
        #global metric_values
        import matplotlib.pyplot as plt
        plt.subplots(1,2,figsize=(10,8))
		
        # Draw the fixed image in the first subplot.
        plt.subplot(1,2,1)
        plt.imshow(fixed_npa,cmap=plt.cm.Greys_r)
        plt.title('fixed image')
        plt.axis('off')
		
        print(registration_method.GetCurrentLevel(), np.min(fixed_npa),np.max(fixed_npa))
        #get_current_transform
        current_transform = sitk.Transform(registration_method.GetInitialTransform())
        print(current_transform)
        print(registration_method.GetOptimizerPosition())
        current_transform.SetParameters(registration_method.GetOptimizerPosition())
        print(current_transform)
        
        moving = sitk.Resample(moving,fixed, current_transform)
        moving_npa = sitk.GetArrayFromImage(moving)
        print(np.min(moving_npa), np.max(moving_npa))
        # Draw the moving image in the second subplot.
        plt.subplot(1,2,2)
        plt.imshow(moving_npa-fixed_npa,cmap=plt.cm.Greys_r);
        plt.title('moving image')
        plt.axis('off')
		
		#plt.show()
        fn = "{:s}_{:03d}.png".format(fn,len(metric_values))
        plt.savefig(fn)
        plt.close()
        
        """
        print(registration_method.GetCurrentLevel(), np.min(fixed_npa),np.max(fixed_npa))
        #get_current_transform
        current_transform = sitk.Transform(registration_method.GetInitialTransform())
        current_transform.SetParameters(registration_method.GetOptimizerPosition())
        
        fn1 = "{:s}_{:03d}.mha".format(fn,len(metric_values))
        moving = sitk.Resample(moving,fixed, current_transform)
        
        sitk.WriteImage(moving-fixed, fn1)
        fn1 = "{:s}_m_{:03d}.mha".format(fn,len(metric_values))
        sitk.WriteImage(moving, fn1)
        fn1 = "{:s}_f_{:03d}.mha".format(fn,len(metric_values))
        sitk.WriteImage(fixed, fn1)
		"""
		# Callback invoked by the IPython interact method for scrolling and modifying the alpha blending
# of an image stack of two images that occupy the same physical space. 
    def display_images_with_alpha(self, image_z, alpha, fixed, moving):
        img = (1.0 - alpha)*fixed[:,:,image_z] + alpha*moving[:,:,image_z] 
        plt.imshow(sitk.GetArrayViewFromImage(img),cmap=plt.cm.Greys_r);
        plt.axis('off')
        plt.show()
	
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
        import matplotlib.pyplot as plt
        plt.close()

    # Callback invoked when the IterationEvent happens, update our data and display new figure.    
    def plot_values(self, registration_method, fn):
        global metric_values, multires_iterations
        
        metric_values.append(registration_method.GetMetricValue())                                       
        # Plot the similarity metric values
        import matplotlib.pyplot as plt
        plt.plot(metric_values, 'r')
        plt.plot(multires_iterations, [metric_values[index] for index in multires_iterations], 'b*')
        plt.xlabel('Iteration Number',fontsize=12)
        plt.ylabel('Metric Value',fontsize=12)
        #plt.show()
        plt.savefig(fn)
        
        
    # Callback invoked when the IterationEvent happens, update our data and display new figure.    
    def get_values(self, registration_method):
        #global metric_values, multires_iterations
        
        #metric_values.append(registration_method.GetMetricValue())                                       
        print("RegisterImages: ",len(metric_values), registration_method.GetMetricValue(),
            registration_method.GetOptimizerPosition(), registration_method.GetOptimizerScales())
        
    # Callback invoked when the sitkMultiResolutionIterationEvent happens, update the index into the 
    # metric_values list. 
    def update_multires_iterations(self):
        global metric_values, multires_iterations
        multires_iterations.append(len(metric_values))   
            
    def RegisterAffine(self, fixed_img, moving_img, initial_transf, idx = 0, 
        mode = 0, mode_score=0, apply_tr=False, debug=False):
        if debug:
            import time
            start_time = time.time()
            moving_resampled = sitk.Resample(moving_img, fixed_img,
                initial_transf, sitk.sitkLinear, 0.0, fixed_img.GetPixelID())
            sitk.WriteImage(moving_resampled,'{:d}_moving.nii.gz'.format(idx))
            sitk.WriteImage(fixed_img,'{:d}_fixed.nii.gz'.format(idx))
            
            print("mode_Tra:", mode, "\nMode_score", mode_score, "\nApply Transofrm", apply_tr)
        
        if not apply_tr:
            if mode==1: # do rigid
                initial_transf.AddTransform(sitk.Euler2DTransform())    
            else:
                initial_transf.AddTransform(sitk.AffineTransform(2))    
        else:
            moving_img = sitk.Resample(moving_img, fixed_img,
                initial_transf, sitk.sitkLinear, 0.0, fixed_img.GetPixelID())
            output_tr = initial_transf
            if mode==1: # do rigid
                initial_transf = sitk.Euler2DTransform() 
            else:
                initial_transf = sitk.AffineTransform(2)
            
        
        self.fixed  = sitk.Cast(fixed_img, sitk.sitkFloat32)
        self.moving = sitk.Cast(moving_img, sitk.sitkFloat32)
        

        registration_method = sitk.ImageRegistrationMethod()
        if mode_score==0:
            registration_method.SetMetricAsMeanSquares()
            if debug:
                print("Use mse")
        else:
            registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
            if debug:
                print("Use mutual information")

        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.05)
        registration_method.SetInterpolator(sitk.sitkLinear)


        # Optimizer settings.
        nIterations = 250
        convergenceWindowSize = 50
        
        registration_method.SetOptimizerAsGradientDescent(learningRate=0.01, #changed learning rate from 0.1 to 0.01
            numberOfIterations=nIterations, convergenceMinimumValue=1e-4, convergenceWindowSize=convergenceWindowSize)
        #registration_method.SetOptimizerScalesFromPhysicalShift()
        if mode==0: #affine + mse
            registration_method.SetOptimizerScales([2000,2000,2000,2000,1,1])
        elif mode==1: # do rigid + mse
            registration_method.SetOptimizerScales([2000,1,1])
        else: # affine+mi
            registration_method.SetOptimizerScales([100,100,100,100,1,1])
            


        registration_method.SetShrinkFactorsPerLevel(shrinkFactors = [16,8,4])
        registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[4,2,1])
        registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOff()

        # Don't optimize in-place, we would possibly like to run this cell multiple times.
        registration_method.SetInitialTransform(initial_transf, inPlace=False)
        
        if debug:
            registration_method.AddCommand(sitk.sitkStartEvent, self.start_plot)
            registration_method.AddCommand(sitk.sitkEndEvent, self.end_plot)
            registration_method.AddCommand(sitk.sitkMultiResolutionIterationEvent, self.update_multires_iterations) 
            registration_method.AddCommand(sitk.sitkIterationEvent, lambda: self.get_values(registration_method))
            registration_method.AddCommand(sitk.sitkIterationEvent, lambda: self.plot_values(registration_method, '{:d}_plot.png'.format(idx)))
            #registration_method.AddCommand(sitk.sitkIterationEvent, 
            #    lambda: self.display_images(sitk.GetArrayFromImage(self.fixed), 
            #    self.fixed,
            #    self.moving, registration_method,'{:d}_frame'.format(idx)))
       
        final_transform = registration_method.Execute(self.fixed, self.moving)
        #print('RegisterImages: Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
        
        if debug:
            print ("Initial transform", self.initial_transform )
            print ("Optimized transform", final_transform )
            print ("Optimized transform", final_transform.FlattenTransform() )
        

            print('RegisterImages: Final metric value: {0}'.format(registration_method.GetMetricValue()))
            print('RegisterImages: Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
            
            end_time = time.time()
            moving_resampled = sitk.Resample(self.moving, self.fixed,
                final_transform, sitk.sitkLinear, 0.0, moving_img.GetPixelID())
            sitk.WriteImage(moving_resampled,'{:d}_moved.nii.gz'.format(idx))
            print("RegisterImages: Done Running Affine Registration in", (end_time-start_time)/60, "(min)")

        if self.verbose: 
            print("RegisterImages: Done Running Affine Registration!")
        
        #only add the last Affine
        if apply_tr:
            output_tr.AddTransform(final_transform)
            return output_tr
        else:
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
        registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
        
        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.05)

        registration_method.SetInterpolator(sitk.sitkLinear)


        
        nIterations = 10

        # Optimizer settings.
        registration_method.SetOptimizerAsLBFGSB(gradientConvergenceTolerance=1e-5, numberOfIterations=nIterations)
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
