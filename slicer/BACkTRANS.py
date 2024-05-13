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
        # allast_snippets = ""
        # for ast_snippets in self.astdiffsHistory:
        #     for ast_snippet in ast_snippets[2]:
        #         allast_snippets = allast_snippets + ast_snippet + "\n"

        # all_library_names = ""
        # for dependency in self.dependencies:
        #      all_library_names = all_library_names + dependency + ", "

        # metadata = ""

        # for data in self.metadata[:-1]: 
        #      metadata = metadata + data + "\n"
        # for comment in self.metadata[-1]:
        #      metadata = metadata + comment + "\n" 


        # f_set = ""
        # c_set = ""

        # for functional in self.functionalSet:
        #     f_set = f_set + functional + ", "
        
        # for compilation in self.compilationSet:
        #     c_set = c_set + compilation + ", "
             

        # def get_nested_values(data):
        #     nested_values = []

        #     def extract_nested_values(obj):
        #         if isinstance(obj, dict):
        #             for value in obj.values():
        #                 extract_nested_values(value)
        #         elif isinstance(obj, list):
        #             for item in obj:
        #                 extract_nested_values(item)
        #         else:
        #             nested_values.append(str(obj))

        #     extract_nested_values(data)
        #     return ', '.join(nested_values)

        # nested_values_string = get_nested_values(self.stableLibraris)

        # data = {
        #     "adaptation": [
        #         {
        #             "data-from": "Backporting activities",
        #             "script": "Adapted semantic slices by analyzing changesets in backporting."
        #         },
        #         {
        #             "data-from": "original",
        #             "script": self.sourceOriginal,
        #             "weight": 0
        #         },
        #         {
        #             "data-from": "backport",
        #             "script": self.sourcebackport,
        #             "weight": 1
        #         },
        #         {
        #             "data-from": "astdiffs-history",
        #             "script": allast_snippets,
        #             "weight": 0
        #         },
        #         {
        #             "data-from": "context",
        #             "script": self.context,
        #             "weight": 0
        #         },
        #         {
        #             "data-from": "dependencies",
        #             "script": all_library_names,
        #             "weight": 0
        #         },
        #         {
        #             "data-from": "metadata",
        #             "script": metadata,
        #             "weight": 0
        #         },
        #         {
        #             "data-from": "functional-set",
        #             "script": f_set,
        #             "weight": 0
        #         },
        #         {
        #             "data-from": "compilation-set",
        #             "script": c_set,
        #             "weight": 0
        #         },
        #         {
        #             "data-from": "stable-libraries",
        #             "script": nested_values_string,
        #             "weight": 1
        #         },
        #         {
        #             "data-from": "target-file",
        #             "script": self.targetfile,
        #             "weight": 1
        #         }
        #     ]
        # }
        data = {
            "adaptation": [
                {
                    "data-from": "Backporting activities",
                    "script": "Adapted semantic slices by analyzing changesets in backporting."
                },
                {
                    "data-from": "original",
                    "script": self.sourceOriginal,
                    "weight": 0
                },
                {
                    "data-from": "backport",
                    "script": self.sourcebackport,
                    "weight": 1
                }
            ]
        }        
        return data

    def saveData(self, data, filename):
        with open(filename, 'a') as f:
                f.write(json.dumps(data) + '\n')



    def analyzeProgram(self):
        """
        Adapt the sourceOriginal to a stable version based on various inputs.

        Returns:
            str: The adapted source code, close to sourcebackport.
        """
        return self.sourcebackport, "Recom"

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
# sourceOriginal = "What's the capital of France?"
# sourcebackport = "Backporting"
# astdiffsHistory = "Some history"
# context = "Some context"
# dependencies = "Some dependencies"
# metadata = "Some metadata"
# functionalSet = "Some functional set"
# compilationSet = "Some compilation set"
# stableLibraris = "Some stable libraries"
# targetfile = "Some target file"


# processor = BackTransformer(sourceOriginal, sourcebackport, astdiffsHistory, context, dependencies, metadata, functionalSet, compilationSet, stableLibraris, targetfile)
# data = processor.prepareFinetuneData()
# processor.saveData(data, 'transInput/Backports.jsonl')