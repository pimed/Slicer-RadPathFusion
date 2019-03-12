from __future__ import print_function
import os
from __main__ import vtk, qt, ctk, slicer
#
# ReconstructPathology
#

class ReconstructPathology:
    def __init__(self, parent):
        parent.title = "2. Reconstruct Pathology Specimen"
        parent.categories = ["Radiology-Pathology Fusion"]
        parent.dependencies = []
        parent.contributors = ["Mirabela Rusu (Stanford)"]
        parent.helpText = \
            """
            This modules provides a basic functionality to reconstruct a pathology specimen based on sequential histology images
            <br /><br />
            For detailed information about a specific model please consult the <a href=\"http://pimed.stanford.edu/\">piMed website</a>.
             """

        parent.acknowledgementText = """
        The developers would like to thank the support of the PiMed and Stanford University.
        """
        self.parent = parent

#
# qReconstructPathologyWidget
#

class ReconstructPathologyWidget:
    def __init__(self, parent = None): #constructor 
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
        self.logic = ReconstructPathologyLogic()
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
        # rgb volume selector
        #
        self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
        self.inputVolumeSelector.nodeTypes = ["vtkMRMLVectorVolumeNode"]
        self.inputVolumeSelector.selectNodeUponCreation = True
        self.inputVolumeSelector.addEnabled = False
        self.inputVolumeSelector.removeEnabled = False
        self.inputVolumeSelector.noneEnabled = False
        self.inputVolumeSelector.showHidden = False
        self.inputVolumeSelector.showChildNodeTypes = False
        self.inputVolumeSelector.setMRMLScene( slicer.mrmlScene )
        self.inputFormLayout.addRow("Fixed volume: ", self.inputVolumeSelector)

        ###
        """
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
        """

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

        """
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

        """
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
        print("onApply")

    def onCancel(self):
        print("onApply")

    def onTest(self):
        print("onApply")
#
# parsePath json fusion logic
#
class ReconstructPathologyLogic():
    def __init__(self):
        self.verbose = True

    def run(self):
        print("run")
 

    def test(self):
        print("Starting the test")
        #
        # first, get some data
        #

