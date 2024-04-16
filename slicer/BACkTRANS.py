# https://arminnorouzi.github.io/posts/2023/05/blog-post-13/
# https://github.com/microsoft/PyCodeGPT
# https://machinelearningmastery.com/training-the-transformer-model/


# Use this - https://platform.openai.com/docs/guides/fine-tuning/analyzing-your-fine-tuned-model
#  https://platform.openai.com/docs/guides/fine-tuning/upload-a-training-file


from utils.slicerUtile import *
class BackTransformer():
    def __init__(self, sourceOriginal= None, sourcebackport = None, astdiffsHistory = None, context = None, dependencies = None, metadata = None, functionalSet = None, compilationSet= None, stableLibraris = None, targetfile = None):
        self.sourceOriginal = sourceOriginal
        self.sourcebackport = sourcebackport
        self.astdiffsHistory = astdiffsHistory
        self.context = context
        self.dependencies = dependencies 
        self.metadata = metadata
        self.functionalSet = functionalSet
        self.compilationSet= compilationSet
        self.stableLibraris = stableLibraris
        self.targetfile = targetfile  

    def analyzeProgram(self):
        """
        Adapt the sourceOriginal to a stable version based on various inputs.

        Returns:
            str: The adapted source code, close to sourcebackport.
        """
        pass                   
