# https://arminnorouzi.github.io/posts/2023/05/blog-post-13/
# https://github.com/microsoft/PyCodeGPT
# https://machinelearningmastery.com/training-the-transformer-model/

# Use this - https://platform.openai.com/docs/guides/fine-tuning/analyzing-your-fine-tuned-model
#  https://platform.openai.com/docs/guides/fine-tuning/upload-a-training-file

# from utils.slicerUtile import *

from openai import OpenAI
import json

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

    def prepareFinetuneData(self):
        """
        Prepare data for fine-tuning the transformer
        """
        data = []
        for i in range(len(self.sourceOriginal)):
            adaptation_data = {
                "tool": "Backporting",
                "task": "Provides adapted semantic slices by analyzing changesets in backporting.",
                "data-from": "original",
                "script": self.sourceOriginal[i]
            }

            # Assuming all other attributes are single items
            adaptation_data["context"] = self.context
            adaptation_data["dependencies"] = self.dependencies
            adaptation_data["metadata"] = self.metadata
            adaptation_data["functionalSet"] = self.functionalSet
            adaptation_data["compilationSet"] = self.compilationSet
            adaptation_data["stableLibraris"] = self.stableLibraris
            adaptation_data["targetfile"] = self.targetfile

            data.append(adaptation_data)

        return data

    def saveData(self, data, filename):
        with open(filename, 'a') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')



    def analyzeProgram(self):
        """
        Adapt the sourceOriginal to a stable version based on various inputs.

        Returns:
            str: The adapted source code, close to sourcebackport.
        """
        client = OpenAI()
        # client.files.create(
        # file=open("transInput/Backports.jsonl", "rb"),
        # purpose="fine-tune"
        # )        


        client.fine_tuning.jobs.create(
        training_file="file-RbPMFc923v9HCt0u3G1gHs4d", 
        model="gpt-3.5-turbo"
        )

        # completion = client.chat.completions.create(
        # model="ft:gpt-3.5-turbo:my-org:custom_suffix:id",
        # messages=[
        #     {"role": "system", "content": "You are a helpful assistant."},
        #     {"role": "user", "content": "Hello!"}
        # ]
        # )
        # print(completion.choices[0].message)        


        # completion = client.chat.completions.create(
        # model="babbage-002",
        # messages=[
        #     {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
        #     {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
        # ]
        # )
        # print(completion.choices[0].message)     

# bT = BackTransformer()
# bT.analyzeProgram()                  


# Example usage:
sourceOriginal = ["What's the capital of France?"]
sourcebackport = "Backporting"
astdiffsHistory = "Some history"
context = "Some context"
dependencies = "Some dependencies"
metadata = "Some metadata"
functionalSet = "Some functional set"
compilationSet = "Some compilation set"
stableLibraris = "Some stable libraries"
targetfile = "Some target file"


processor = BackTransformer(sourceOriginal, sourcebackport, astdiffsHistory, context, dependencies, metadata, functionalSet, compilationSet, stableLibraris, targetfile)
data = processor.prepareFinetuneData()
processor.saveData(data, 'finetune_data.json')