from __future__ import print_function
import os
import json
from time import sleep
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
        
        self.advancedOptions = None

    def setup(self):
        #
        # Input 
        #
        self.inputCollapsibleButton = ctk.ctkCollapsibleButton()
        self.inputCollapsibleButton.text = "Input"
        self.layout.addWidget(self.inputCollapsibleButton)

        # Layout within the input collapsible button
        self.inputFormLayout = qt.QFormLayout(self.inputCollapsibleButton)
    
        import platform
        self.inputJsonFn = ctk.ctkPathLineEdit()
        self.inputFormLayout.addRow("Input Json:", self.inputJsonFn)
        #self.inputJsonFn.setCurrentPath('input.json')
        if platform.system() == 'Linux':
            self.inputJsonFn.setCurrentPath('/home/mrusu/Projects/RadPathFusion/prostate/4_histology/')
        if platform.system() == 'Windows':
            self.inputJsonFn.setCurrentPath('C:/Projects/rad-path-fusion/prostate_RP/3_histology/')
        #self.inputJsonFn.setMaximumWidth(425)
        self.inputJsonFn.addCurrentPathToHistory();

        #
        # input fixed volume selector
        #
        self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
        self.inputVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.inputVolumeSelector.selectNodeUponCreation = True
        self.inputVolumeSelector.addEnabled = False
        self.inputVolumeSelector.renameEnabled = True
        self.inputVolumeSelector.removeEnabled = True
        self.inputVolumeSelector.noneEnabled = True
        self.inputVolumeSelector.showHidden = False
        self.inputVolumeSelector.showChildNodeTypes = False
        self.inputVolumeSelector.setMRMLScene( slicer.mrmlScene )
        self.inputFormLayout.addRow("Fixed Volume: ", self.inputVolumeSelector)

        #
        # input fixed volume selector
        #
        self.inputMaskSelector = slicer.qMRMLNodeComboBox()
        self.inputMaskSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
        self.inputMaskSelector.selectNodeUponCreation = True
        self.inputMaskSelector.addEnabled = False
        self.inputMaskSelector.renameEnabled = True
        self.inputMaskSelector.removeEnabled = True
        self.inputMaskSelector.noneEnabled = True
        self.inputMaskSelector.showHidden = False
        self.inputMaskSelector.showChildNodeTypes = False
        self.inputMaskSelector.setMRMLScene( slicer.mrmlScene )
        self.inputFormLayout.addRow("Fixed Mask: ", self.inputMaskSelector)
        
        #
        #Output
        #
        self.outputCollapsibleButton = ctk.ctkCollapsibleButton()
        self.outputCollapsibleButton.text = "Output"
        self.layout.addWidget(self.outputCollapsibleButton)

        # Layout within the output collapsible button
        self.outputFormLayout = qt.QFormLayout(self.outputCollapsibleButton)

        """
        self.outputJsonFn = ctk.ctkPathLineEdit()
        self.outputFormLayout.addRow("Output Json:", self.outputJsonFn)
        if platform.system() == 'Linux':
            self.outputJsonFn.setCurrentPath('/home/mrusu/Projects/RadPathFusion/prostate/4_histology/')
        if platform.system() == 'Windows':
            self.outputJsonFn.setCurrentPath( 'C:/Projects/rad-path-fusion/prostate_RP/3_histology/')
            
        #self.outputJsonFn.setMaximumWidth(400)
        """
     

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
        self.outputFormLayout.addRow("Output Volume: ", self.outputVolumeSelector)
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
        self.progress.setRange(0, 0)
        #self.progress.setValue(0)
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

        # ReconstructVolume
        self.refineVolumeButton = qt.QPushButton("Refine Volume")
        self.refineVolumeButton.toolTip = "Refine."
        self.refineVolumeButton.enabled = True

        # RegisterVolume
        self.registerVolumeButton = qt.QPushButton("Register")
        self.registerVolumeButton.toolTip = "Register"
        self.registerVolumeButton.enabled = True
        
        # LoadVolume
        self.loadVolumeButton = qt.QPushButton("Load Volume")
        self.loadVolumeButton.toolTip = "Load Volume."
        self.loadVolumeButton.enabled = True

        # LoadMask
        self.loadMaskVolumeButton = qt.QPushButton("Load Mask")
        self.loadMaskVolumeButton.toolTip = "Load a Mask"
        self.loadMaskVolumeButton.enabled = True

        # Clear
        self.clearAllVolumeButton = qt.QPushButton("Clear ALL")
        self.clearAllVolumeButton.toolTip = "Clear"
        self.clearAllVolumeButton.enabled = False

        hlayout = qt.QHBoxLayout()

        hlayout.addWidget(self.loadJsonButton)
        hlayout.addWidget(self.refineVolumeButton)
        hlayout.addWidget(self.registerVolumeButton)
        hlayout.addWidget(self.loadVolumeButton)
        hlayout.addWidget(self.loadMaskVolumeButton)
        hlayout.addWidget(self.clearAllVolumeButton)
        hlayout.addStretch(1)
        hlayout.addWidget(self.saveJsonButton)
        self.layout.addLayout(hlayout)


        self.loadJsonButton.connect('clicked(bool)', self.onLoadJson)
        self.saveJsonButton.connect('clicked(bool)', 
            self.onSaveJson)
        self.refineVolumeButton.connect('clicked(bool)', self.onRefineVolume)
        self.registerVolumeButton.connect('clicked(bool)', self.onRegisterVolume)
        self.loadVolumeButton.connect('clicked(bool)', self.onLoadVolume)
        self.loadMaskVolumeButton.connect('clicked(bool)', 
            self.onLoadMaskVolume)
        self.clearAllVolumeButton.connect('clicked(bool)', 
            self.onClearAll)
            
        self.maskIdSelector.connect('currentIndexChanged(int)', 
            self.onMaskIDSelect)
            
                #
        # advanced 
        #
        self.advancedCollapsibleButton = ctk.ctkCollapsibleButton()
        self.advancedCollapsibleButton.text = "Advanced"
        self.layout.addWidget(self.advancedCollapsibleButton)
        self.advancedCollapsibleButton.enabled = False
        
        self.advancedFormLayout = qt.QFormLayout(self.advancedCollapsibleButton)

        

        # Add vertical spacer
        self.layout.addStretch(1)
 
    def onLoadJson(self):
        if self.verbose:
            print("onLoadJson")
        self.saveJsonButton.enabled = True
        self.advancedCollapsibleButton.enabled = True
        self.populate_advanced_tab();
        self.loadJsonButton.enabled = False

        
    def populate_advanced_tab(self):
        jsonUIInfo = self.logic.getJsonInfo4UI(self.inputJsonFn.currentPath)
       
        
        self.advancedOptions = []
        for el in jsonUIInfo:
            #print(el)
            
            self.idxSlide = ctk.ctkDoubleSpinBox()
            self.advancedFormLayout.addRow("Idx:", self.idxSlide)
            self.idxSlide.setValue(int(el[1]))
            self.idxSlide.setEnabled(False);
            
            self.rgbPath = ctk.ctkPathLineEdit()
            self.advancedFormLayout.addRow("    Rgb Image:", self.rgbPath)
            self.rgbPath.setCurrentPath(el[2])

            
            
            self.doFlip = ctk.ctkCheckBox()
            self.advancedFormLayout.addRow("    Flip:", self.doFlip)
            if (not el[4]==None) and el[4]==1:
                self.doFlip.setChecked(True)
            else:
                self.doFlip.setChecked(False)
                
            self.doRotate = ctk.ctkDoubleSpinBox()
            self.advancedFormLayout.addRow("    Rotation angle:", self.doRotate)
            self.doRotate.minimum = 0.0
            self.doRotate.maximum = 360.0
            self.doRotate.singleStep = 90.0
            if el[5]:
                self.doRotate.setValue(int(el[5]))
                
            for maskEl in el[3]:
                print(maskEl)
                self.idxMask2 = ctk.ctkDoubleSpinBox()
                self.advancedFormLayout.addRow("        Mask Idx:", 
                    self.idxMask2)
                self.idxMask2.setValue(int(maskEl[0]))
                self.idxMask2.setEnabled(False)
                
                self.maskPath = ctk.ctkPathLineEdit()
                self.advancedFormLayout.addRow("        Mask Image:", self.maskPath)
                self.maskPath.setCurrentPath(maskEl[1])
                
                self.idxMask2.connect('valueChanged(double)',  lambda value, idxSlice = el[0], idxMask = int(maskEl[0]): self.onMaskIdxChange(value, idxSlice, idxMask))
                
                self.maskPath.connect('currentPathChanged(QString)', lambda value,  idxSlice = el[0], idxMask = int(maskEl[0]): self.onMaskFileChange(value, idxSlice, idxMask))
                
                
            Separador = qt.QFrame()
            Separador.setFrameShape(qt.QFrame.HLine)
            Separador.setLineWidth(1)
            self.advancedFormLayout.addRow(Separador)
            

            self.idxSlide.connect('valueChanged(double)',  lambda value, idx = el[0]: self.onSliceIdxChange(value, idx))
            
            self.rgbPath.connect('currentPathChanged(QString)', lambda value, idx = el[0]:self.onSliceJsonFileChange(value, idx))
            
            self.doFlip.connect('stateChanged(int)', lambda value, idx = el[0]:self.onSliceFlipChange(value, idx))
            
 
            self.doRotate.connect('valueChanged(double)',  lambda value, idx = el[0]: self.onSliceDoRotateChange(value, idx))
                
            advancedUIEl = [el[0], self.idxSlide, self.rgbPath, self.doRotate, self.doRotate]
            self.advancedOptions.append(advancedUIEl)


    def clear_advanced_tab(self):
        self.advancedFormLayout.removeRow(layout)
            
    def onSliceIdxChange(self, value, idx):
        if self.verbose:
            print(value,"-",idx)
            
        self.logic.setIdxToSlice(idx, value)
                
    def onSliceJsonFileChange(self, path, idx):
        if self.verbose:
            print(str(path),"-",idx)
        
        self.logic.setRgbPathToSlice(idx, str(path))        

    def onSliceFlipChange(self, checked, idx):
        if self.verbose:
            print(checked,"-",idx)
            
        #checked seem to either be 0 or 2 (where 2 is checked)
        self.logic.setFlipToSlice(idx, int(checked/2.0))
            
    def onSliceDoRotateChange(self, slice_doRotate_value, idx):
        if self.verbose:
            print(slice_doRotate_value,"--", idx)
        
        self.logic.setRotateToSlice(idx, slice_doRotate_value)
    
    def onMaskIdxChange(self,  newIdx, idxSlice, idxMask):
        if self.verbose:
            print(newIdx, idxSlice, idxMask)
            
        self.logic.setMaskIdx(idxSlice, idxMask, newIdx)
    
    def onMaskFileChange(self, path, idxSlice, idxMask):
        if self.verbose:
            print("OnMaskFileChange" , path, idxSlice, idxMask)
            
        self.logic.setMaskFilename(idxSlice, idxMask, path)
            
    def onOpenDialogSaveJson(self):
        if self.verbose:
            print("onSave")
            print("Current path", self.inputJsonFn.currentPath)
        
        fileDialog = ctk.ctkFileDialog(slicer.util.mainWindow())
        fileDialog.setDirectory(self.inputJsonFn.currentPath)
        fileDialog.setWindowModality(1)
        fileDialog.setWindowTitle("Select Json File")
        fileDialog.setFileMode(3) # prompt for files
        fileDialog.connect('fileSelected(QString)', self.onSaveJson)
        fileDialog.open()
        
        ctk.ctkFileDialog.get
        
    def onSaveJson(self, path_out_json):
        
        path_out_json = ctk.ctkFileDialog.getSaveFileName(
            slicer.util.mainWindow(), "Select Json File", 
            self.inputJsonFn.currentPath)
        try:
            self.logic.saveJson(path_out_json)
        except Exception as e:
            print("Coudn't save")

    def onRefineVolume(self):
        if self.verbose:
            print("onRefine")

        self.logic.refineVolume(self.inputJsonFn.currentPath,
            outputVolumeNode = self.outputVolumeSelector.currentNode())

    def onRegisterVolume(self):
        if self.verbose:
            print("onRegister")

        self.logic.registerVolume(self.inputJsonFn.currentPath, 
            self.inputVolumeSelector.currentNode(), 
            self.inputMaskSelector.currentNode(), 
            outputVolumeNode = self.outputVolumeSelector.currentNode())

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

    def onLogicEventStart(self):
        self.currentStatusLabel.text = "Running"
        #self.progress.setValue(0)
        self.progress.show()
        #print("Showing and starting")

    def onLogicEventEnd(self):
        self.currentStatusLabel.text = "Completed"
        self.progress.setValue(10)
        self.progress.hide()
        
    def onLogicEventProgress(self, progress):
        self.currentStatusLabel.text = "Running ({0:6.5f})".format(progress)
        self.progress.setValue(progress * 1000)
        
    def onClearAll(self):
        self.clear_advanced_tab()
        qt.QMessageBox.critical(slicer.util.mainWindow(), "Error","Not implemented!")
        
                
#
# parsePath json fusion logic
#
class ParsePathJsonLogic():
    def __init__(self):
        self.verbose = True
        self.scriptPath = os.path.dirname(os.path.abspath(__file__))
        self.logic = None
        
    def yieldPythonGIL(self, seconds=0):
        sleep(seconds)

    def cmdStartEvent(self):
        if hasattr(slicer.modules, 'ParsePathJsonWidget'):
            widget = slicer.modules.ParsePathJsonWidget
            widget.onLogicEventStart()
        self.yieldPythonGIL()

    def cmdProgressEvent(self, progress):
        if hasattr(slicer.modules, 'ParsePathJsonWidget'):
            widget = slicer.modules.ParsePathJsonWidget
            widget.onLogicEventProgress(progress)
        self.yieldPythonGIL()

    def cmdEndEvent(self):
        if hasattr(slicer.modules, 'ParsePathJsonWidget'):
            widget = slicer.modules.ParsePathJsonWidget
            widget.onLogicEventEnd()
        self.yieldPythonGIL()
        
    def loadRgbVolume(self, 
        json_path,
        outputVolumeNode = None):
        
        modules = slicer.modules
        if hasattr(modules, 'ParsePathJsonWidget'):
            widgetPresent = True
        else:
            widgetPresent = False

        if widgetPresent:
            self.cmdStartEvent()
            slicer.app.processEvents()

        if not self.logic:
            import sys
            sys.path.append(os.path.join(self.scriptPath,"Resources","Utils"))

            import ParsePathJsonUtils as ppju
            self.logic = ppju.ParsePathJsonUtils()
            self.logic.setPath(json_path)
            #success = self.logic.initComponents()
            #if not success:
            #    qt.QMessageBox.critical(slicer.util.mainWindow(), "Error","Failure to load json. Check path!")
            #    return

        if not str(self.logic.path)==str(json_path):
            self.logic.setPath(json_path)
        
        if not self.logic.successfulInitialization:
            success = self.logic.initComponents()
            if not success:
                if widgetPresent:
                    self.cmdEndEvent()  
                qt.QMessageBox.critical(slicer.util.mainWindow(), "Error","Failure to load json. Check path!")
                return

        if outputVolumeNode:
            slicer.app.processEvents()    
            import sitkUtils
            outputVolume = self.logic.pathologyVolume.loadRgbVolume()
            sitkUtils.PushVolumeToSlicer(outputVolume, 
                targetNode=outputVolumeNode)

            selectionNode = slicer.app.applicationLogic().GetSelectionNode()
            selectionNode.SetReferenceActiveVolumeID(outputVolumeNode.GetID())
            slicer.app.applicationLogic().PropagateVolumeSelection(0)
        else:
            qt.QMessageBox.critical(slicer.util.mainWindow(), "No Output","Output Volume was not set!")

        if widgetPresent:
            self.cmdEndEvent()         

            
    def refineVolume(self, 
        json_path,
        outputVolumeNode = None):
        
        modules = slicer.modules
        if hasattr(modules, 'ParsePathJsonWidget'):
            widgetPresent = True
        else:
            widgetPresent = False

        if widgetPresent:
            self.cmdStartEvent()
            slicer.app.processEvents()
            
        if not self.logic:
            import sys
            sys.path.append(os.path.join(self.scriptPath,"Resources","Utils"))

            import ParsePathJsonUtils as ppju
            self.logic = ppju.ParsePathJsonUtils()
            self.logic.setPath(json_path)
            #success = self.logic.initComponents()
            #if not success:
            #    qt.QMessageBox.critical(slicer.util.mainWindow(), "Error","Failure to load json. Check path!")
            #    return

        if not str(self.logic.path)==str(json_path):
            self.logic.setPath(json_path)
        
        if not self.logic.successfulInitialization:
            success = self.logic.initComponents()
            if not success:
                if widgetPresent:
                    self.cmdEndEvent()  
                qt.QMessageBox.critical(slicer.util.mainWindow(), "Error","Failure to load json. Check path!")
                return

        if outputVolumeNode:
            slicer.app.processEvents()
            import sitkUtils
            self.logic.pathologyVolume.registerSlices(False)
            outputVolume = self.logic.pathologyVolume.loadRgbVolume()
            sitkUtils.PushVolumeToSlicer(outputVolume, 
                targetNode=outputVolumeNode)
        

            selectionNode = slicer.app.applicationLogic().GetSelectionNode()
            selectionNode.SetReferenceActiveVolumeID(outputVolumeNode.GetID())
            slicer.app.applicationLogic().PropagateVolumeSelection(0)
        else:
            qt.QMessageBox.critical(slicer.util.mainWindow(), "No Output","Output Volume was not set!")

        if widgetPresent:
            self.cmdEndEvent()       

            
    def registerVolume(self, 
        json_path,
        fixedNode,
        fixedMaskNode,
        outputVolumeNode = None):
        
        modules = slicer.modules        
        if hasattr(modules, 'ParsePathJsonWidget'):
            widgetPresent = True
        else:
            widgetPresent = False

        if widgetPresent:
            self.cmdStartEvent()
            slicer.app.processEvents()
            
        if not self.logic:
            import sys
            sys.path.append(os.path.join(self.scriptPath,"Resources","Utils"))

            import ParsePathJsonUtils as ppju
            self.logic = ppju.ParsePathJsonUtils()
            self.logic.setPath(json_path)
            
            if not self.logic.successfulInitialization:
                success = self.logic.initComponents()
                if not success:
                    qt.QMessageBox.critical(slicer.util.mainWindow(), "Error","Failure to load json. Check path!")
                    return

        if not str(self.logic.path)==str(json_path):
            self.logic.setPath(json_path)
            if not self.logic.successfulInitialization:
                success = self.logic.initComponents()
                if not success:
                    qt.QMessageBox.critical(slicer.util.mainWindow(), "Error","Failure to load json. Check path!")
                    return

        if outputVolumeNode:
            import sitkUtils
            slicer.app.processEvents()
            
            self.logic.pathologyVolume.imagingContraint = sitkUtils.PullVolumeFromSlicer(fixedNode)
            self.logic.pathologyVolume.imagingContraintMask = sitkUtils.PullVolumeFromSlicer(fixedMaskNode)
            self.logic.pathologyVolume.registerSlices(True)
            
            outputVolume = self.logic.pathologyVolume.loadRgbVolume()
            sitkUtils.PushVolumeToSlicer(outputVolume, 
                targetNode=outputVolumeNode)
        

            selectionNode = slicer.app.applicationLogic().GetSelectionNode()
            selectionNode.SetReferenceActiveVolumeID(outputVolumeNode.GetID())
            slicer.app.applicationLogic().PropagateVolumeSelection(0)            
        else:
            qt.QMessageBox.critical(slicer.util.mainWindow(), "No Output","Output Volume was not set!")

        if widgetPresent:
            self.cmdEndEvent()  


           
    def loadMask(self, 
        json_path,
        idxMask = 0,
        outputMaskVolumeNode = None):
        
        modules = slicer.modules
        if hasattr(modules, 'ParsePathJsonWidget'):
            widgetPresent = True
        else:
            widgetPresent = False

        if widgetPresent:
            self.cmdStartEvent()
            slicer.app.processEvents()
            
        if not self.logic:
            import sys
            sys.path.append(os.path.join(self.scriptPath,"Resources","Utils"))

            import ParsePathJsonUtils as ppju
            self.logic = ppju.ParsePathJsonUtils()
            self.logic.setPath(json_path)
            if not self.logic.successfulInitialization:
                success = self.logic.initComponents()
                if not success:
                    qt.QMessageBox.critical(slicer.util.mainWindow(), "Error","Failure to load json. Check path!")
                    return

        if not str(self.logic.path)==str(json_path):
            self.logic.setPath(json_path)
            if not self.logic.successfulInitialization:
                success = self.logic.initComponents()
                if not success:
                    qt.QMessageBox.critical(slicer.util.mainWindow(), "Error","Failure to load json. Check path!")
                    return


        if idxMask>=0 and outputMaskVolumeNode:
            slicer.app.processEvents()
            import sitkUtils
            outputVolume = self.logic.pathologyVolume.loadMask( idxMask )
            sitkUtils.PushVolumeToSlicer(outputVolume, 
                targetNode=outputMaskVolumeNode)
        

            selectionNode = slicer.app.applicationLogic().GetSelectionNode()
            selectionNode.SetReferenceActiveLabelVolumeID(outputMaskVolumeNode.GetID())
            slicer.app.applicationLogic().PropagateVolumeSelection(0)
        else:
            qt.QMessageBox.critical(slicer.util.mainWindow(), "No Output Mask","Output Mask was not set!")

        if widgetPresent:
            self.cmdEndEvent()     
            
    def getJsonInfo4UI(self, json_path):
        if self.verbose:
           print("Reading json", json_path)
           
        if not self.logic:
            import sys
            sys.path.append(os.path.join(self.scriptPath,"Resources","Utils"))

            import ParsePathJsonUtils as ppju
            self.logic = ppju.ParsePathJsonUtils()
            
        self.logic.setPath(json_path)
        self.logic.initComponents()
        
        data = self.logic.pathologyVolume.getInfo4UI()
        
        return data
    
    def setIdxToSlice(self, idx, newSliceIdx):       
        if not self.logic:
            print("Logic doesn't exit")
            return
            
        #internally idx starts at 0, but in the UI it starts at 1
        self.logic.pathologyVolume.updateSlice(idx, 
            'slice_number', 
            int(newSliceIdx)-1)
            
            
    def setRgbPathToSlice(self, idx, newPath):       
        if not self.logic:
            print("Logic doesn't exit")
            return
            
        self.logic.pathologyVolume.updateSlice(idx, 'filename',  newPath)
            
    def setFlipToSlice(self, idx, newFlip):       
        if not self.logic:
            print("Logic doesn't exit")
            return
            
        self.logic.pathologyVolume.updateSlice(idx,
            'flip', 
            int(newFlip) )
        
    def setRotateToSlice(self, idx, newRotate):       
        if not self.logic:
            print("Logic doesn't exit")
            return
            
        self.logic.pathologyVolume.updateSlice(idx, 'rotation_angle', 
            int(newRotate) )

    def setMaskIdx(self, idxSlice, idxMask, newIdx):
        if not self.logic:
            print("Logic doesn't exit")
            return
            
        self.logic.pathologyVolume.updateSliceMask(idxSlice, idxMask, 
            'key', newIdx)

            
    def setMaskFilename(self, idxSlice, idxMask, value):
        if not self.logic:
            print("Logic doesn't exit")
            return
            
        self.logic.pathologyVolume.updateSliceMask(idxSlice, idxMask, 
            'filename', value)
    
    def saveJson(self, path):
        if not self.logic:
            print("Can't save Logic doesn't exit")
            return

        self.logic.pathologyVolume.saveJson(path)
        

    def deleteData(self):
        print("Deleting Volume from logic")
        self.logic.PathologyVolume.deleteData()
        self.logic = None
            
    def test(self):
        print("Starting the test")
        #
        # first, get some data
        #

