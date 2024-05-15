# https://arminnorouzi.github.io/posts/2023/05/blog-post-13/
# https://github.com/microsoft/PyCodeGPT
# https://machinelearningmastery.com/training-the-transformer-model/

# Use this - https://platform.openai.com/docs/guides/fine-tuning/analyzing-your-fine-tuned-model
#  https://platform.openai.com/docs/guides/fine-tuning/upload-a-training-file

# from utils.slicerUtile import *

from openai import OpenAI
import json
import os

class BackTransformer():
    def __init__(self, sourceOriginal= None, sourcebackport = None, astdiffsHistory = None, context = None, dependencies = None, metadata = None, functionalSet = None, compilationSet= None, stableLibraris = None, targetfile = None, tfileName = None):
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
        self.tfileName = tfileName

    def formatPromptData(self):
        targetfileName = os.path.basename(self.tfileName)

        allast_snippets = ""
        for ast_snippets in self.astdiffsHistory:
            for ast_snippet in ast_snippets[2]:
                allast_snippets = allast_snippets + ast_snippet + "\n"

        all_library_names = ""
        for dependency in self.dependencies:
             all_library_names = all_library_names + dependency + ", "

        metadata = ""

        for data in self.metadata[:-1]: 
             metadata = metadata + data + "\n"
        for comment in self.metadata[-1]:
             metadata = metadata + comment + "\n" 


        f_set = ""
        c_set = ""

        for functional in self.functionalSet:
            f_set = f_set + functional + ", "
        
        for compilation in self.compilationSet:
            c_set = c_set + compilation + ", "
             

        def get_nested_values(data, targetfileName):
            if data is None or targetfileName not in data:
                return {}

            nested_values = {
                'libraries': set(),
                'function_names': set(),
                'function_calls': set(),
                'class_names': set(),
                'class_method_calls': set()
            }

            script_data = data.get(targetfileName)
            if isinstance(script_data, dict):
                for key, values in script_data.items():
                    nested_values[key].update(values)

            nested_values_strings = {key: ', '.join(values) for key, values in nested_values.items()}
            return nested_values_strings
        
        nested_values = get_nested_values(self.stableLibraris, targetfileName)

        nested_values_libraries = nested_values.get('libraries', '')
        nested_values_function_names = nested_values.get('function_names', '')
        nested_values_function_calls = nested_values.get('function_calls', '')
        nested_values_class_names = nested_values.get('class_names', '')
        nested_values_class_method_calls = nested_values.get('class_method_calls', '')


        # def get_nested_values(data, keywords, min_chars=3):
        #     nested_values = []

        #     def count_matching_chars(str1, str2):
        #         return sum(1 for char in str1 if char in str2)

        #     def extract_nested_values(obj):
        #         if isinstance(obj, dict):
        #             for value in obj.values():
        #                 extract_nested_values(value)
        #         elif isinstance(obj, list):
        #             for item in obj:
        #                 extract_nested_values(item)
        #         else:
        #             for keyword in keywords:
        #                 if count_matching_chars(str(keyword), str(obj)) >= min_chars:
        #                     nested_values.append(str(obj))
        #                     break

        #     extract_nested_values(data)
        #     return ', '.join(nested_values)

        # nested_values_string = get_nested_values(self.stableLibraris, self.sourceOriginal)        

        return (
            "All ASTs from commit history: " + allast_snippets + "\n" +
            "Current context: " + self.context + "\n" +
            "Required dependency: " + all_library_names + "\n" +
            "Original metadata: " + metadata + "\n" +
            "Functional set for the hunk: " + f_set + "\n" +
            "Compilation set for the hunk: " + c_set + "\n" +
            "Library information from Stable: " + nested_values_libraries + "\n" +
            "Function name information from Stable: " + nested_values_function_names + "\n" +
            "Function call information from Stable: " + nested_values_function_calls + "\n" +
            "Class name information from Stable: " + nested_values_class_names + "\n" + 
            "Class method call information from Stable: " + nested_values_class_method_calls + "\n" +                                   
            "Target file: " + self.targetfile
        )


    def prepareFinetuneData(self):
        """
        Prepare data for fine-tuning the transformer
        """
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
            "messages": [
                {
                    "role": "system",
                    "content": "You're BackTrans, an automated code propagation tool engineered to seamlessly adapt a user's original code snippet for compatibility with older, stable versions."
                },
                {
                    "role": "user",
                    "content": self.sourceOriginal
                },
                {
                    "role": "assistant",
                    "content": self.sourcebackport
                }
            ]
        }        
        return data

    def saveData(self, data, filename):
        with open(filename, 'a') as f:
                f.write(json.dumps(data) + '\n')



    def analyzeProgram(self, fineTuning = False, fineTuningFile = "transInput/Backports.jsonl", ftTraining = False, prompt = False):
        """
        Adapt the sourceOriginal to a stable version based on various inputs.

        Returns:
            str: The adapted source code, close to sourcebackport.
        """
        result = ""
        client = OpenAI()

        if fineTuning:
            client.files.create(
            file=open(fineTuningFile, "rb"),
            purpose="fine-tune"
            )        

        if ftTraining:
            client.fine_tuning.jobs.create(
            training_file="file-ItN6SgBPXzvlWbHmTEqdDfBA", 
            model="gpt-3.5-turbo"
            )

        if prompt:
            promptData = self.formatPromptData()
            completion = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0125:personal::9OZSElOU" if ftTraining else "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Adapt the given code snippet based on the information below - "+ promptData},
                {"role": "user", "content": "Adapt this - " + self.sourceOriginal + "No need to provide extra information."}
            ]
            )
            result = completion.choices[0].message        
   
        return result.content, "Recom"
