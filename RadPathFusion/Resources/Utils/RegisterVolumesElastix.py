"""
Base on https://github.com/lassoan/SlicerElastix/blob/master/Elastix/Elastix.py
"""
import os

class RegisterVolumesElastix():
    def __init__(self):
        self.verbose = True
        self.elastixBinDir = None 
        self.elastixLibDir = None

        self.registrationParameterFilesDir = None

        import platform
        executableExt = '.exe' if platform.system() == 'Windows' else ''
        self.elastixFilename = 'elastix' + executableExt
        self.transformixFilename = 'transformix' + executableExt

        self.bySlicer = True
        self.deleteTemporaryFiles = True

        self.abortRequested = None

    def registerVolumes(self, 
        fixedVolumeNode, 
        movingVolumeNode, 
        parameterFilenames = None, 
        outputVolumeNode = None, 
        outputTransformNode = None,
        fixedVolumeMaskNode = None, 
        movingVolumeMaskNode = None):
        
        output = self.getInputParameters(fixedVolumeNode, 
            movingVolumeNode, 
            parameterFilenames, 
            outputVolumeNode, 
            outputTransformNode,
            fixedVolumeMaskNode, 
            movingVolumeMaskNode)

        inputParamsElastix, inputParamsTransformix, tmpDir, resultResampleDir = output

        # Run registration
        ep = self.startElastix(inputParamsElastix)
        self.logProcessOutput(ep)

        tp = self.startTransformix(inputParamsTransformix)
        self.logProcessOutput(tp)
 
      
        if outputVolumeNode:
            outputVolumePath = os.path.join(resultResampleDir, "result.mhd")
            self.loadResultVolume(outputVolumePath, outputVolumeNode)

        if outputTransformNode:
            outputTransformPath = os.path.join(resultResampleDir, "deformationField.mhd")
            self.loadResultTransform(outputTransformPath, outputTransformNode)

        self.cleanUpTempFiles(tmpDir)


    def getInputParameters(self, 
        fixedVolumeNode, 
        movingVolumeNode, 
        parameterFilenames = None, 
        outputVolumeNode = None, 
        outputTransformNode = None,
        fixedVolumeMaskNode = None, 
        movingVolumeMaskNode = None):

        if self.verbose:
            print("Register Volumes")
    
        tempDir,inputDir,resultTransformDir,resultResampleDir = self.createTempDirectory()
        if self.verbose:
            print('Volume registration is started in working directory: '+tempDir)

        inputParamsElastix = []

        # Add input volumes
        inputVolumes = []
        inputVolumes.append([fixedVolumeNode, 'fixed.mha', '-f'])
        inputVolumes.append([movingVolumeNode, 'moving.mha', '-m'])
        inputVolumes.append([fixedVolumeMaskNode, 'fixedMask.mha', '-fMask'])
        inputVolumes.append([movingVolumeMaskNode, 'movingMask.mha', '-mMask'])
        for [volumeNode, filename, paramName] in inputVolumes:
            if not volumeNode:
                continue
            filePath = os.path.join(inputDir, filename)

            if self.bySlicer:
                import slicer
                slicer.util.saveNode(volumeNode, filePath, {"useCompression": False})
                inputParamsElastix.append(paramName)
                inputParamsElastix.append(filePath)

        # Specify output location
        inputParamsElastix += ['-out', resultTransformDir]

        # Specify parameter files
        for parameterFilename in parameterFilenames:
            inputParamsElastix.append('-p')
            parameterFilePath = os.path.abspath(os.path.join(
                self.registrationParameterFilesDir, parameterFilename))
            inputParamsElastix.append(parameterFilePath)
 
        # Resample
        inputParamsTransformix = ['-in', os.path.join(inputDir, 'moving.mha'), '-out', resultResampleDir]
        if outputTransformNode:
            inputParamsTransformix += ['-def', 'all']
        if outputVolumeNode:
            inputParamsTransformix += ['-tp', resultTransformDir+'/TransformParameters.'+str(len(parameterFilenames)-1)+'.txt']


        return inputParamsElastix, inputParamsTransformix, tempDir, resultResampleDir

    def loadResultVolume(self, path, outputVolumeNode):
        if self.bySlicer:
            import slicer, vtk
            [success, loadedOutputVolumeNode] = slicer.util.loadVolume(path, 
                returnNode = True)
            if success:
                outputVolumeNode.SetAndObserveImageData(
                    loadedOutputVolumeNode.GetImageData())
                ijkToRas = vtk.vtkMatrix4x4()
                loadedOutputVolumeNode.GetIJKToRASMatrix(ijkToRas)
                outputVolumeNode.SetIJKToRASMatrix(ijkToRas)
                slicer.mrmlScene.RemoveNode(loadedOutputVolumeNode)
            else:
                print("Failed to load output volume from "+path)


    def loadResultTransform(self, path, outputTransformNode):
        if self.bySlicer:
            import slicer
            [success, loadedOutputTransformNode] = slicer.util.loadTransform(path, 
                returnNode = True)
            if success:
                if loadedOutputTransformNode.GetReadAsTransformToParent():
                    outputTransformNode.SetAndObserveTransformToParent(
                        loadedOutputTransformNode.GetTransformToParent())
                else:
                    outputTransformNode.SetAndObserveTransformFromParent(
                        loadedOutputTransformNode.GetTransformFromParent())
                slicer.mrmlScene.RemoveNode(loadedOutputTransformNode)
            else:
                print("Failed to load output transform from "+path)


    def getStartupInfo(self):
        import platform
        if platform.system() != 'Windows':
          return None

        # Hide console window (only needed on Windows)
        import subprocess
        info = subprocess.STARTUPINFO()
        info.dwFlags = 1
        info.wShowWindow = 0
        return info

    def startElastix(self, cmdLineArguments):
        import subprocess
        executableFilePath = os.path.join(self.getElastixBinDir(),self.elastixFilename)
        if self.verbose:
            print("Register volumes...")
            print("Register volumes using: "+executableFilePath+": "+repr(cmdLineArguments))
            #print("Enviroment: ", repr(self.getElastixEnv())) 
        if subprocess.mswindows:
          return subprocess.Popen([executableFilePath] + cmdLineArguments, 
                env=self.getElastixEnv(),
                stdout=subprocess.PIPE, 
                universal_newlines=True, 
                startupinfo=self.getStartupInfo())
        else:
          return subprocess.Popen([executableFilePath] + cmdLineArguments, 
                                env=self.getElastixEnv(),
                                stdout=subprocess.PIPE, universal_newlines=True)

    def startTransformix(self, cmdLineArguments):
        import subprocess
        executableFilePath = os.path.join(self.getElastixBinDir(), self.transformixFilename)
        if self.verbose:
            print("Generate output...")
            print("Generate output using: " + executableFilePath + ": " + repr(cmdLineArguments))    
        if subprocess.mswindows:
            return subprocess.Popen([os.path.join(self.getElastixBinDir(),
                self.transformixFilename)] + cmdLineArguments, 
                env=self.getElastixEnv(),
                stdout=subprocess.PIPE, 
                universal_newlines = True, 
                startupinfo=self.getStartupInfo())
        else:
          return subprocess.Popen([os.path.join(self.getElastixBinDir(), 
                self.transformixFilename)] + cmdLineArguments, 
                env=self.getElastixEnv(),
                stdout=subprocess.PIPE, 
                universal_newlines = True)

    def logProcessOutput(self, process):
        # save process output so that it can be displayed in case of an error
        processOutput = ''
        import subprocess
        for stdout_line in iter(process.stdout.readline, ""):
            #if self.logStandardOutput:
            #  self.addLog(stdout_line.rstrip())
            #else:
            processOutput += stdout_line.rstrip() + '\n'

            if self.bySlicer:
                import slicer
                slicer.app.processEvents()  # give a chance to click Cancel button
                if self.abortRequested:
                    process.kill()

        process.stdout.close()
        return_code = process.wait()
        if return_code:
          if self.abortRequested:
            raise ValueError("User requested cancel.")
          else:
            if processOutput:
              #self.addLog(processOutput)
              print('Return code:', return_code)
            raise subprocess.CalledProcessError(return_code, "elastix")

    def setElastixBinDir(self, path):
        self.elastixBinDir = path
        self.elastixLibDir = self.getElastixEnv()

    def setRegistrationParameterFilesDir(self, path):
        self.registrationParameterFilesDir = path

    def getElastixBinDir(self):
        return self.elastixBinDir 

    def getElastixEnv(self):
        """Create an environment for elastix where executables are added to the path"""
        elastixBinDir   = self.getElastixBinDir()
        elastixEnv      = os.environ.copy()

        if elastixEnv.get("PATH"):
            elastixEnv["PATH"] = elastixBinDir + os.pathsep + elastixEnv["PATH"] 
        else:
            elastixEnv["PATH"] = elastixBinDir

        import platform
        if platform.system() != 'Windows':
          elastixLibDir = os.path.abspath(os.path.join(elastixBinDir, '../lib'))

        #if elastixEnv.get("LD_LIBRARY_PATH"):
        #    elastixEnv["LD_LIBRARY_PATH"] = elastixLibDir + os.pathsep + \
        #        elastixEnv["LD_LIBRARY_PATH"]  
        #else:
        #    elastixEnv["LD_LIBRARY_PATH"] = elastixLibDir
        #FIXME: somehow the enviroment of slicer was messing up the elastix run
        #This might end up messing the slicer behavior, but hopefully not
        elastixEnv["LD_LIBRARY_PATH"] = elastixLibDir

        return elastixEnv
    def getTempDirectoryBase(self, bySlicer=True):
        if bySlicer:
            import qt, slicer
            tempDir = qt.QDir(slicer.app.temporaryPath)
            fileInfo = qt.QFileInfo(qt.QDir(tempDir), "RadPathFusion")
            dirPath = fileInfo.absoluteFilePath()
            qt.QDir().mkpath(dirPath)
        return dirPath

    def createTempDirectory(self, bySlicer=True):
        if bySlicer:
            import qt, slicer
            tempDir = qt.QDir(self.getTempDirectoryBase(bySlicer))
            tempDirName = qt.QDateTime().currentDateTime().toString("yyyyMMdd_hhmmss_zzz")
            fileInfo = qt.QFileInfo(qt.QDir(tempDir), tempDirName)
            dirPath = fileInfo.absoluteFilePath()
            qt.QDir().mkpath(dirPath)

            # Write inputs
            inputDir = os.path.join(dirPath, 'input')
            qt.QDir().mkpath(inputDir)

            resultTransformDir = os.path.join(dirPath, 'result-transform')
            qt.QDir().mkpath(resultTransformDir)

            resultResampleDir = os.path.join(dirPath, 'result-resample')
            qt.QDir().mkpath(resultResampleDir)


        return dirPath, inputDir, resultTransformDir, resultResampleDir

    def cleanUpTempFiles(self, path):
        if self.deleteTemporaryFiles:
            import shutil
            shutil.rmtree(path)

 
