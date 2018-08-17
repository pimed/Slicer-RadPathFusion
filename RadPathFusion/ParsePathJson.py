from __future__ import print_function
import os
import json
from __main__ import vtk, qt, ctk, slicer
#
# ParsePathJson
#

class ParsePathJson:
    def __init__(self, parent):
        parent.title = "1. Parse Pathology"
        parent.categories = ["Radiology-Pathology Fusion"]
        parent.dependencies = []
        parent.contributors = ["Mirabela Rusu (Stanford)"]
        parent.helpText = \
            """
            This modules provides a basic functionality to parse and create json file that will be used as interface for the radiology pathology fusion
            <br /><br />
            For detailed information about a specific model please consult the <a href=\"http://pimed.stanford.edu/\">piMed website</a>.
             """

        parent.acknowledgementText = """
        The developers would like to thank the support of the PiMed and Stanford University.
        """
        self.parent = parent

#
# qParsePathJsonWidget
#

class ParsePathJsonWidget:
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
        
        self.logic = ParsePathJsonLogic()
        self.verbose = True
        self.idxMask = None

    def setup(self):
        #
        # Input 
        #
        self.inputCollapsibleButton = ctk.ctkCollapsibleButton()
        self.inputCollapsibleButton.text = "Input"
        self.layout.addWidget(self.inputCollapsibleButton)

        # Layout within the input collapsible button
        self.inputFormLayout = qt.QFormLayout(self.inputCollapsibleButton)
    
        self.inputJsonFn = ctk.ctkPathLineEdit()
        self.inputFormLayout.addRow("Input Json:", self.inputJsonFn)
        #self.inputJsonFn.setCurrentPath('input.json')
        self.inputJsonFn.setCurrentPath('/home/mrusu/Projects/RadPathFusion/prostate/4_histology/1_1627377.json')
        #self.inputJsonFn.setMaximumWidth(425)
 

        #
        #Output
        #
        self.outputCollapsibleButton = ctk.ctkCollapsibleButton()
        self.outputCollapsibleButton.text = "Output"
        self.layout.addWidget(self.outputCollapsibleButton)

        # Layout within the output collapsible button
        self.outputFormLayout = qt.QFormLayout(self.outputCollapsibleButton)

        self.outputJsonFn = ctk.ctkPathLineEdit()
        self.outputFormLayout.addRow("Output Json:", self.outputJsonFn)
        self.outputJsonFn.setCurrentPath('/home/mrusu/Projects/RadPathFusion/prostate/4_histology/1_1627377_test.json')
        #self.outputJsonFn.setMaximumWidth(400)
     

        #
        # output volume selector
        #
        self.outputVolumeSelector = slicer.qMRMLNodeComboBox()
        self.outputVolumeSelector.nodeTypes = ["vtkMRMLVectorVolumeNode"]
        self.outputVolumeSelector.selectNodeUponCreation = True
        self.outputVolumeSelector.addEnabled = True
        self.outputVolumeSelector.renameEnabled = True
        self.outputVolumeSelector.removeEnabled = True
        self.outputVolumeSelector.noneEnabled = True
        self.outputVolumeSelector.showHidden = False
        self.outputVolumeSelector.showChildNodeTypes = False
        self.outputVolumeSelector.setMRMLScene( slicer.mrmlScene )
        self.outputFormLayout.addRow("Output volume: ", self.outputVolumeSelector)
        #self.outputVolumeSelector.setMaximumWidth(400)

        #
        # output mask volume selector
        #
        self.outputMaskVolumeSelector = slicer.qMRMLNodeComboBox()
        self.outputMaskVolumeSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
        self.outputMaskVolumeSelector.selectNodeUponCreation = True
        self.outputMaskVolumeSelector.addEnabled = True
        self.outputMaskVolumeSelector.renameEnabled = True
        self.outputMaskVolumeSelector.removeEnabled = True
        self.outputMaskVolumeSelector.noneEnabled = True
        self.outputMaskVolumeSelector.showHidden = False
        self.outputMaskVolumeSelector.showChildNodeTypes = False
        self.outputMaskVolumeSelector.setMRMLScene( slicer.mrmlScene )
        # maskIDselector
        self.maskIdSelector = qt.QComboBox()
        self.populateMaskId()

        self.outputFormLayout.addRow("Output Mask: ", self.outputMaskVolumeSelector)
        self.outputFormLayout.addRow("Mask ID", self.maskIdSelector)
        #self.outputMaskVolumeSelector.setMaximumWidth(400)


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

        #Load Input
        self.loadJsonButton = qt.QPushButton("Load Json")
        self.loadJsonButton.toolTip = "Load the json file."
        self.loadJsonButton.enabled = True

        # Save Output Json
        self.saveJsonButton = qt.QPushButton("Save Json")
        self.saveJsonButton.toolTip = "Save the json file."
        self.saveJsonButton.enabled = False

        # LoadVolume
        self.loadVolumeButton = qt.QPushButton("Load Volume")
        self.loadVolumeButton.toolTip = "Load Volume."
        self.loadVolumeButton.enabled = True

        # LoadMask
        self.loadMaskVolumeButton = qt.QPushButton("Load Mask")
        self.loadMaskVolumeButton.toolTip = "Load a Mask"
        self.loadMaskVolumeButton.enabled = True


        hlayout = qt.QHBoxLayout()

        hlayout.addWidget(self.loadJsonButton)
        hlayout.addWidget(self.loadVolumeButton)
        hlayout.addWidget(self.loadMaskVolumeButton)
        hlayout.addStretch(1)
        hlayout.addWidget(self.saveJsonButton)
        self.layout.addLayout(hlayout)


        self.loadJsonButton.connect('clicked(bool)', self.onLoadJson)
        self.saveJsonButton.connect('clicked(bool)', self.onSaveJson)
        self.loadVolumeButton.connect('clicked(bool)', self.onLoadVolume)
        self.loadMaskVolumeButton.connect('clicked(bool)', self.onLoadMaskVolume)
        
        self.maskIdSelector.connect('currentIndexChanged(int)', self.onMaskIDSelect)
 
    def onLoadJson(self):
        if self.verbose:
            print("onLoadJson")
        self.saveJsonButton.enabled = True

    def onSaveJson(self):
        if self.verbose:
            print("onSave")

    def onLoadVolume(self):
        if self.verbose:
            print("onLoadVolume")

        self.logic.loadRgbVolume(self.inputJsonFn.currentPath,
            outputVolumeNode = self.outputVolumeSelector.currentNode())

    def onLoadMaskVolume(self):
        if self.verbose:
            print("onMaskLoadVolume")

        self.logic.loadMask(self.inputJsonFn.currentPath, self.idxMask, 
            outputMaskVolumeNode = self.outputMaskVolumeSelector.currentNode())

    def populateMaskId(self):
        for idx in range(11):
            self.maskIdSelector.addItem(str(idx), idx)
        self.idxMask = 0

    def onMaskIDSelect(self, selectorIndex):
        if selectorIndex < 0:
            return       
        self.idxMask = selectorIndex

        print("Selected Mask", self.idxMask)

#
# parsePath json fusion logic
#
class ParsePathJsonLogic():
    def __init__(self):
        self.verbose = True
        self.scriptPath = os.path.dirname(os.path.abspath(__file__))
        self.logic = None

    def loadRgbVolume(self, 
        json_path,
        outputVolumeNode = None):

        if not self.logic:
            import sys
            sys.path.append(os.path.join(self.scriptPath,"Resources","Utils"))

            import ParsePathJsonUtils as ppju
            self.logic = ppju.ParsePathJsonUtils()
            self.logic.setPath(json_path)
            self.logic.initComponents()

        if outputVolumeNode:
            import sitkUtils
            outputVolume = self.logic.pathologyVolume.loadRgbVolume()
            sitkUtils.PushVolumeToSlicer(outputVolume, 
                targetNode=outputVolumeNode)
        

            selectionNode = slicer.app.applicationLogic().GetSelectionNode()
            selectionNode.SetReferenceActiveVolumeID(outputVolumeNode.GetID())
            slicer.app.applicationLogic().PropagateVolumeSelection(0)


   
    def loadMask(self, 
        json_path,
        idxMask = 0,
        outputMaskVolumeNode = None):
        if not self.logic:
            import sys
            sys.path.append(os.path.join(self.scriptPath,"Resources","Utils"))

            import ParsePathJsonUtils as ppju
            self.logic = ppju.ParsePathJsonUtils()
            self.logic.setPath(json_path)
            self.logic.initComponents()


        if idxMask>=0 and outputMaskVolumeNode:
            import sitkUtils
            outputVolume = self.logic.pathologyVolume.loadMask( idxMask )
            sitkUtils.PushVolumeToSlicer(outputVolume, 
                targetNode=outputMaskVolumeNode)
        

            selectionNode = slicer.app.applicationLogic().GetSelectionNode()
            selectionNode.SetReferenceActiveLabelVolumeID(outputMaskVolumeNode.GetID())
            slicer.app.applicationLogic().PropagateVolumeSelection(0)


    def test(self):
        print("Starting the test")
        #
        # first, get some data
        #

