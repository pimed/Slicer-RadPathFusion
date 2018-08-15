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
    self.logic = None

  def setup(self):
    # Collapsible button
    self.inputCollapsibleButton = ctk.ctkCollapsibleButton()
    self.inputCollapsibleButton.text = "Inputs"
    self.layout.addWidget(self.inputCollapsibleButton)

    # Layout within the input collapsible button
    self.inputFormLayout = qt.QFormLayout(self.inputCollapsibleButton)

    #
    # the volume selectors
    #
    self.inputFixedFrame = qt.QFrame(self.inputCollapsibleButton)
    self.inputFixedFrame.setLayout(qt.QHBoxLayout())
    self.inputFormLayout.addWidget(self.inputFixedFrame)
    self.inputFixedSelector = qt.QLabel("Fixed Volume: ", self.inputFixedFrame)
    self.inputFixedFrame.layout().addWidget(self.inputFixedSelector)
    self.inputFixedSelector = slicer.qMRMLNodeComboBox(self.inputFixedFrame)
    self.inputFixedSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputFixedSelector.addEnabled = False
    self.inputFixedSelector.removeEnabled = False
    self.inputFixedSelector.setMRMLScene( slicer.mrmlScene )
    self.inputFixedFrame.layout().addWidget(self.inputFixedSelector)

    self.inputMovingFrame = qt.QFrame(self.inputCollapsibleButton)
    self.inputMovingFrame.setLayout(qt.QHBoxLayout())
    self.inputFormLayout.addWidget(self.inputMovingFrame)
    self.inputMovingSelector = qt.QLabel("Moving Volume: ", self.inputMovingFrame)
    self.inputMovingFrame.layout().addWidget(self.inputMovingSelector)
    self.inputMovingSelector = slicer.qMRMLNodeComboBox(self.inputMovingFrame)
    self.inputMovingSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputMovingSelector.addEnabled = False
    self.inputMovingSelector.removeEnabled = False
    self.inputMovingSelector.setMRMLScene( slicer.mrmlScene )
    self.inputMovingFrame.layout().addWidget(self.inputMovingSelector)


    self.outputCollapsibleButton = ctk.ctkCollapsibleButton()
    self.outputCollapsibleButton.text = "Output"
    self.layout.addWidget(self.outputCollapsibleButton)

    # Layout within the output collapsible button
    self.outputFormLayout = qt.QFormLayout(self.outputCollapsibleButton)


    self.outputFrame = qt.QFrame(self.outputCollapsibleButton)
    self.outputFrame.setLayout(qt.QHBoxLayout())
    self.outputFormLayout.addWidget(self.outputFrame)
    self.outputSelector = qt.QLabel("Output Volume: ", self.outputFrame)
    self.outputFrame.layout().addWidget(self.outputSelector)
    self.outputSelector = slicer.qMRMLNodeComboBox(self.outputFrame)
    self.outputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputFrame.layout().addWidget(self.outputSelector)


    # Apply button
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the Radiology-Pathology Fusion."
    self.layout.addWidget(self.applyButton)

    self.applyButton.connect('clicked(bool)', self.onApply)

    # Add vertical spacer
    self.layout.addStretch(1)

  def onApply(self):
    print('onApply')
    #FIXME: make logic globab
    self.logic = RadPathFusionLogic()
    #self.logic.testElastixLogic()

    self.logic.run(self.inputFixedSelector.currentNode(), 
        self.inputMovingSelector.currentNode(),
        outputVolumeNode = self.outputSelector.currentNode(),
        #outputTransformNode = self.outputTransformSelector.currentNode(),
        #fixedVolumeMaskNode = self.fixedVolumeMaskSelector.currentNode(),
        #movingVolumeMaskNode = self.movingVolumeMaskSelector.currentNode()
        )


        #print('onApply')
        #self.logic = DeepInferLogic()
        # try:
        #self.currentStatusLabel.text = "Starting"
        #self.modelParameters.prerun()
        #self.logic.run(self.modelParameters)


#
# Rad-path fusion logic
#
class RadPathFusionLogic():
    def __init__(self):
        self.TBD = None

    def run(self, fixedVolume, movingVolume, outputVolumeNode = None):
        import sys
        sys.path.append(' /home/mrusu/.config/NA-MIC/Extensions-26899/SlicerElastix/lib/Slicer-4.9/qt-scripted-modules/Resources/')
        from Elastix import ElastixLogic
       
        logic = ElastixLogic()
        parameterFilenames = ["Similarity2.txt", "Similarity.txt"]
        print(parameterFilenames)
        logic.registerVolumes(fixedVolume, movingVolume, 
            parameterFilenames = parameterFilenames, 
            outputVolumeNode = outputVolumeNode)

        selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        selectionNode.SetReferenceActiveVolumeID(outputVolumeNode.GetID())
        slicer.app.applicationLogic().PropagateVolumeSelection(0)

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
        sys.path.append('/home/mrusu/.config/NA-MIC/Extensions-26899/SlicerElastix/lib/Slicer-4.9/qt-scripted-modules/Resources/')
        from Elastix import ElastixLogic, RegistrationPresets_ParameterFilenames


        logic = ElastixLogic()
        parameterFilenames = logic.getRegistrationPresets()[0][RegistrationPresets_ParameterFilenames]
        print(parameterFilenames)
        logic.registerVolumes(tumor1, tumor2, parameterFilenames = parameterFilenames, outputVolumeNode = outputVolume)

        selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        selectionNode.SetReferenceActiveVolumeID(outputVolume.GetID())
        slicer.app.applicationLogic().PropagateVolumeSelection(0)

