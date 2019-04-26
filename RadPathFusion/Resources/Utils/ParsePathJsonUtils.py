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

    def setPath(self, path):
        self.path=path
    
    def initComponents(self):
        if self.verbose:
            print("initialize components") 
        if self.path:
            self.pathologyVolume.setPath(self.path)
            self.pathologyVolume.initComponents()