from time import sleep

from __main__ import vtk, qt, ctk, slicer
#
# RadPathFusion
#

class RadPathFusion:
  def __init__(self, parent):
    parent.title = "Radiology-Pathology Fusion"
    parent.categories = ["Radiology-Pathology Fusion"]
    parent.dependencies = []
    parent.contributors = ["Mirabela Rusu (Stanford)"]
    parent.helpText = \
        """
        This modules provides a basic interface for radiology pathology fusion
        <br /><br />
        For detailed information about a specific model please consult the <a href=\"http://pimed.stanford.edu/\">piMed website</a>.
         """

    parent.acknowledgementText = """
    The developers would like to thank the support of the PiMed and Stanford University.
    """
    self.parent = parent

#
# qRadPathFusionWidget
#

class RadPathFusionWidget:
    def __init__(self, parent = None): #constructor 
        #self.logic = RadPathFusionLogic()
        if not parent:
          self.parent = slicer.qMRMLWidget()
          self.parent.setLayout(qt.QVBoxLayout())
          self.parent.setMRMLScene(slicer.mrmlScene)
        else:
          self.parent = parent
        self.layout = self.parent.layout()
        if not parent:
          self.setup()
          self.parent.show()
        self.logic = RadPathFusionLogic()
        self.slicerElastixPath = None
        self.verbose = True

    def setup(self):
        #
        # Configuration
        #
        self.configCollapsibleButton = ctk.ctkCollapsibleButton()
        self.configCollapsibleButton.text = "Configuration"
        self.layout.addWidget(self.configCollapsibleButton)

        # Layout within the configuration collapsible button
        self.configFormLayout = qt.QFormLayout(self.configCollapsibleButton)
     

        import platform
        self.elastixPath = ctk.ctkPathLineEdit()
        self.elastixPath.filters = ctk.ctkPathLineEdit.Dirs
        self.configFormLayout.addRow("Elastix Executable Path:", self.elastixPath)
        
        if platform.system() == 'Linux':
            self.elastixPath.setCurrentPath('/home/mrusu/Programs/elastix-4.9.0-linux/bin/')
        if platform.system() == 'Windows':
            self.elastixPath.setCurrentPath("C:/Programs/elastix-4.9.0-win64/")

        self.slicerElastixPath = ctk.ctkPathLineEdit()
        self.slicerElastixPath.filters = ctk.ctkPathLineEdit.Dirs
        self.configFormLayout.addRow("Slicer Elastix Path:", self.slicerElastixPath)

        if platform.system() == 'Linux':
            self.slicerElastixPath.setCurrentPath('/home/mrusu/Programs/SlicerElastix/Elastix')
        if platform.system() == 'Windows':
            self.slicerElastixPath.setCurrentPath("C:/Programs/SlicerElastix/Elastix/")

     
        #
        # Input 
        #
        self.inputCollapsibleButton = ctk.ctkCollapsibleButton()
        self.inputCollapsibleButton.text = "Input"
        self.layout.addWidget(self.inputCollapsibleButton)

        # Layout within the input collapsible button
        self.inputFormLayout = qt.QFormLayout(self.inputCollapsibleButton)

        #
        # fixed volume selector
        #
        self.fixedVolumeSelector = slicer.qMRMLNodeComboBox()
        self.fixedVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.fixedVolumeSelector.selectNodeUponCreation = True
        self.fixedVolumeSelector.addEnabled = False
        self.fixedVolumeSelector.removeEnabled = False
        self.fixedVolumeSelector.noneEnabled = False
        self.fixedVolumeSelector.showHidden = False
        self.fixedVolumeSelector.showChildNodeTypes = False
        self.fixedVolumeSelector.setMRMLScene( slicer.mrmlScene )
        self.inputFormLayout.addRow("Fixed volume: ", self.fixedVolumeSelector)

        
        self.fixedVolumeMaskSelector = slicer.qMRMLNodeComboBox()
        self.fixedVolumeMaskSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
        self.fixedVolumeMaskSelector.addEnabled = False
        self.fixedVolumeMaskSelector.removeEnabled = False
        self.fixedVolumeMaskSelector.noneEnabled = True
        self.fixedVolumeMaskSelector.showHidden = False
        self.fixedVolumeMaskSelector.showChildNodeTypes = False
        self.fixedVolumeMaskSelector.setMRMLScene( slicer.mrmlScene )
        self.inputFormLayout.addRow("Fixed volume mask: ", self.fixedVolumeMaskSelector)

        self.movingVolumeSelector = slicer.qMRMLNodeComboBox()
        self.movingVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.movingVolumeSelector.selectNodeUponCreation = True
        self.movingVolumeSelector.addEnabled = False
        self.movingVolumeSelector.removeEnabled = False
        self.movingVolumeSelector.noneEnabled = False
        self.movingVolumeSelector.showHidden = False
        self.movingVolumeSelector.showChildNodeTypes = False
        self.movingVolumeSelector.setMRMLScene( slicer.mrmlScene )
        self.inputFormLayout.addRow("Moving volume: ", self.movingVolumeSelector)


        #
        # moving volume mask selector
        #
        self.movingVolumeMaskSelector = slicer.qMRMLNodeComboBox()
        self.movingVolumeMaskSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
        self.movingVolumeMaskSelector.selectNodeUponCreation = True
        self.movingVolumeMaskSelector.addEnabled = False
        self.movingVolumeMaskSelector.removeEnabled = False
        self.movingVolumeMaskSelector.noneEnabled = True
        self.movingVolumeMaskSelector.showHidden = False
        self.movingVolumeMaskSelector.showChildNodeTypes = False
        self.movingVolumeMaskSelector.setMRMLScene( slicer.mrmlScene )
        self.movingVolumeMaskSelector.setToolTip("Moving volume mask")
        self.inputFormLayout.addRow("Moving volume mask: ", self.movingVolumeMaskSelector)


        #
        #Output
        #
        self.outputCollapsibleButton = ctk.ctkCollapsibleButton()
        self.outputCollapsibleButton.text = "Output"
        self.layout.addWidget(self.outputCollapsibleButton)

        # Layout within the output collapsible button
        self.outputFormLayout = qt.QFormLayout(self.outputCollapsibleButton)

        #
        # output volume selector
        #
        self.outputVolumeSelector = slicer.qMRMLNodeComboBox()
        self.outputVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.outputVolumeSelector.selectNodeUponCreation = True
        self.outputVolumeSelector.addEnabled = True
        self.outputVolumeSelector.renameEnabled = True
        self.outputVolumeSelector.removeEnabled = True
        self.outputVolumeSelector.noneEnabled = True
        self.outputVolumeSelector.showHidden = False
        self.outputVolumeSelector.showChildNodeTypes = False
        self.outputVolumeSelector.setMRMLScene( slicer.mrmlScene )
        self.outputFormLayout.addRow("Output volume: ", self.outputVolumeSelector)

        #
        # output transform selector
        #
        self.outputTransformSelector = slicer.qMRMLNodeComboBox()
        self.outputTransformSelector.nodeTypes = ["vtkMRMLTransformNode"]
        self.outputTransformSelector.selectNodeUponCreation = True
        self.outputTransformSelector.addEnabled = True
        self.outputTransformSelector.renameEnabled = True
        self.outputTransformSelector.removeEnabled = True
        self.outputTransformSelector.noneEnabled = True
        self.outputTransformSelector.showHidden = False
        self.outputTransformSelector.showChildNodeTypes = False
        self.outputTransformSelector.setMRMLScene( slicer.mrmlScene )
        self.outputFormLayout.addRow("Output transform: ", self.outputTransformSelector)

       # Add vertical spacer
        self.layout.addStretch(1)


        #
        # Status and Progress
        #
        statusLabel = qt.QLabel("Status: ")
        self.currentStatusLabel = qt.QLabel("Idle")
        hlayout = qt.QHBoxLayout()
        hlayout.addStretch(1)
        hlayout.addWidget(statusLabel)
        hlayout.addWidget(self.currentStatusLabel)
        self.layout.addLayout(hlayout)

        self.progress = qt.QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.layout.addWidget(self.progress)
        self.progress.hide()

        #Cancel
        self.cancelButton = qt.QPushButton("Cancel")
        self.cancelButton.toolTip = "Abort the algorithm."
        self.cancelButton.enabled = False

        # Apply button
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run the Radiology-Pathology Fusion."
        self.applyButton.enabled = True

        # Test button
        self.testButton = qt.QPushButton("Test")
        self.testButton.toolTip = "Text elastix."
        self.testButton.enabled = True

        hlayout = qt.QHBoxLayout()

        hlayout.addWidget(self.testButton)
        hlayout.addStretch(1)
        hlayout.addWidget(self.cancelButton)
        hlayout.addWidget(self.applyButton)
        self.layout.addLayout(hlayout)


        self.cancelButton.connect('clicked(bool)', self.onCancel)
        self.applyButton.connect('clicked(bool)', self.onApply)
        self.testButton.connect('clicked(bool)', self.onTest)

    def onApply(self):
        if self.verbose:
            print('onApply')

        self.logic.SetSlicerElastixPath(self.slicerElastixPath.currentPath)
        self.logic.SetElastixPath(self.elastixPath.currentPath)

        self.logic.run(self.fixedVolumeSelector.currentNode(), 
            self.movingVolumeSelector.currentNode(),
            outputVolumeNode = self.outputVolumeSelector.currentNode(),
            outputTransformNode = self.outputTransformSelector.currentNode(),
            fixedVolumeMaskNode = self.fixedVolumeMaskSelector.currentNode(),
            movingVolumeMaskNode = self.movingVolumeMaskSelector.currentNode()
            )
    def onCancel(self):
        if self.verbose:
            print('onCancel')

    def onTest(self):
        if self.verbose:
            print('onTest')

        self.logic.SetSlicerElastixPath(self.slicerElastixPath.currentPath)
        self.logic.SetElastixPath(self.elastixPath.currentPath)

        self.logic.testElastixLogic()

    def onLogicEventStart(self):
        self.currentStatusLabel.text = "Running"
        self.cancelButton.setDisabled(False)
        self.progress.setValue(0)
        self.progress.show()

    def onLogicEventEnd(self):
        self.currentStatusLabel.text = "Completed"
        self.progress.setValue(1000)

    def onLogicEventAbort(self):
        self.currentStatusLabel.text = "Aborted"

    def onLogicEventProgress(self, progress):
        self.currentStatusLabel.text = "Running ({0:6.5f})".format(progress)
        self.progress.setValue(progress * 1000)


#
# Rad-path fusion logic
#
class RadPathFusionLogic():
    def __init__(self):
        import os
        self.slicerElastixPath = None
        self.elastixPath = None
        self.scriptPath = os.path.dirname(os.path.abspath(__file__))
        self.registrationParameterFilesDir = os.path.abspath(os.path.join(self.scriptPath, 
            'Resources', 
            'RegistrationParameters'))

        self.verbose = True

    def run(self, fixedVolume, movingVolume, 
        outputVolumeNode     = None,
        outputTransformNode  = None,
        fixedVolumeMaskNode  = None,
        movingVolumeMaskNode = None):

        modules = slicer.modules
        if hasattr(modules, 'RadPathFusionWidget'):
            widgetPresent = True
        else:
            widgetPresent = False

        if widgetPresent:
            self.cmdStartEvent()
    
        if self.verbose:
            print("SlicerElastixPath:",self.slicerElastixPath)
            print("ElastixPath:",self.elastixPath)
    
        import sys
        if self.slicerElastixPath:
            sys.path.append(self.slicerElastixPath)
        else:
            print("Please set the path to Elastics")
            return 0

        if self.verbose:
            print("path append was succesful", self.slicerElastixPath)

        try:
            from Elastix import ElastixLogic
        except Exception as e:
            print("Coudn't load ElastixLogic from ", self.SetSlicerElastixPath)
            print(e)
            return 0
       
        logic = ElastixLogic()
        parameterFilenames = ["QuickCenteringRigid.txt", 
            "Similarity.txt"]#, 
            #"Affine.txt", 
            #"Deformable.txt"]
        logic.registrationParameterFilesDir =  self.registrationParameterFilesDir
        logic.setCustomElastixBinDir(self.elastixPath)

        logic.registerVolumes(fixedVolume, movingVolume, 
            parameterFilenames   = parameterFilenames, 
            outputVolumeNode     = outputVolumeNode,
            outputTransformNode  = outputTransformNode,
            fixedVolumeMaskNode  = fixedVolumeMaskNode,
            movingVolumeMaskNode = movingVolumeMaskNode)

        if widgetPresent:
            self.cmdEndEvent()


    def testElastixLogic(self):
        print("Starting the test")
        #
        # first, get some data
        #
        slicer.mrmlScene.Clear(0)

        import SampleData
        sampleDataLogic = SampleData.SampleDataLogic()
        tumor1 = sampleDataLogic.downloadMRBrainTumor1()
        tumor2 = sampleDataLogic.downloadMRBrainTumor2()

        outputVolume = slicer.vtkMRMLScalarVolumeNode()
        slicer.mrmlScene.AddNode(outputVolume)
        outputVolume.CreateDefaultDisplayNodes()

        import sys
        if self.slicerElastixPath:
            sys.path.append(self.slicerElastixPath)
        else:
            print("Please set the path to Elastics")
            return 0

        try:
            from Elastix import ElastixLogic, RegistrationPresets_ParameterFilenames
        except Exception as e:
            print("Coudn't load ElastixLogic from ", self.SetSlicerElastixPath)
            print(e)
            return 0


        logic = ElastixLogic()
        parameterFilenames = logic.getRegistrationPresets()[0][
            RegistrationPresets_ParameterFilenames]
        logic.registerVolumes(tumor1, 
            tumor2, 
            parameterFilenames = parameterFilenames, 
            outputVolumeNode = outputVolume)

        selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        selectionNode.SetReferenceActiveVolumeID(outputVolume.GetID())
        slicer.app.applicationLogic().PropagateVolumeSelection(0)

    def SetSlicerElastixPath(self, path):
        self.slicerElastixPath = path

    def SetElastixPath(self, path):
        self.elastixPath = path

    def yieldPythonGIL(self, seconds=0):
        sleep(seconds)

    def cmdCheckAbort(self, p):
        if self.abort:
            p.kill()
            self.cmdAbortEvent()

    def cmdStartEvent(self):
        if hasattr(slicer.modules, 'RadPathFusionWidget'):
            widget = slicer.modules.RadPathFusionWidget
            widget.onLogicEventStart()
        self.yieldPythonGIL()

    def cmdProgressEvent(self, progress):
        if hasattr(slicer.modules, 'RadPathFusionWidget'):
            widget = slicer.modules.RadPathFusionWidget
            widget.onLogicEventProgress(progress)
        self.yieldPythonGIL()

    def cmdAbortEvent(self):
        if hasattr(slicer.modules, 'RadPathFusionWidget'):
            widget = slicer.modules.RadPathFusionWidget
            widget.onLogicEventAbort()
        self.yieldPythonGIL()

    def cmdEndEvent(self):
        if hasattr(slicer.modules, 'RadPathFusionWidget'):
            widget = slicer.modules.RadPathFusionWidget
            widget.onLogicEventEnd()
        self.yieldPythonGIL()


