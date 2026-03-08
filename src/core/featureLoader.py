import os
from importlib import import_module

from .constants import Path

def loadableFeature(cls):
    FeatureLoader.getInstance().registerClass(
        cls
    )
    return cls

class FeatureLoader:
    _INST = None
    def __init__(self):
        self.classes = []
        self.tools = []
    @staticmethod
    def getInstance():
        if FeatureLoader._INST is None:
            FeatureLoader._INST = FeatureLoader()
        return FeatureLoader._INST
    def registerClass(self, cls):
        self.classes.append(cls)
    def loadFeatures(self, window):
        path = os.path.split(Path.INTERNAL_CONFIG)[0]
        for file in os.listdir(path):
            if file == "main.py" or not file.endswith(".py"): continue
            import_module(
                file[:-3] # remove .py
            )
        for cls in self.classes:
            self.tools.append(cls(window))
    def getTools(self):
        return self.tools
