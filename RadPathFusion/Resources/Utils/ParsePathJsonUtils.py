"""
Author: Mirabela Rusu
Created: 2018 Aug 16
"""
from __future__ import print_function
from ImageStack import PathologyVolume

class ParsePathJsonUtils():
    def __init__(self):
        self.verbose = True
        self.path = None
        self.pathologyVolume = PathologyVolume()
        self.storeVolume = False
        self.successfulInitialization = None

    def setPath(self, path):
        self.path=path
    
    def initComponents(self):
        suscess = 0
        if self.verbose:
            print("initialize components") 
        if self.path:
            self.pathologyVolume.setPath(self.path)
            success = self.pathologyVolume.initComponents()
            self.successfulInitialization = self.pathologyVolume.successfulInitialization
            
    
        return success