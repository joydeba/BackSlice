# https://arminnorouzi.github.io/posts/2023/05/blog-post-13/
# https://github.com/microsoft/PyCodeGPT
# https://machinelearningmastery.com/training-the-transformer-model/

# Use this - https://platform.openai.com/docs/guides/fine-tuning/analyzing-your-fine-tuned-model
#  https://platform.openai.com/docs/guides/fine-tuning/upload-a-training-file

from utils.slicerUtile import *

from openai import OpenAI
import json
import os
import re
import keyword
import openai

class BackTransformer():
    def __init__(self, sourceOriginal= None, sourcebackport = None, astdiffsHistory = None, context = None, method_name = None, dependencies = None, metadata = None, functionalSet = None, compilationSet= None, stableLibraris = None, targetfile = None, tfileName = None):
        self.sourceOriginal = sourceOriginal
        self.sourcebackport = sourcebackport
        self.astdiffsHistory = astdiffsHistory
        self.context = context
        self.method_name = method_name
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
                    if key == 'class_method_calls':
                        nested_values[key].update(list(values)[:100])  
                    else:
                        nested_values[key].update(values)

            nested_values_strings = {key: ', '.join(values) for key, values in nested_values.items()}
            return nested_values_strings
        

        # We can try target file directly.
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

        def extract_key_components(source_code):
            identifier_pattern = re.compile(r'\b[A-Za-z_]\w*\b')
            identifiers = identifier_pattern.findall(source_code)
            unique_identifiers = list(dict.fromkeys(identifiers))[:100]  
            key_components = ', '.join(unique_identifiers)
            return key_components
        
        method = extract_method_class_definition(self.targetfile, self.method_name)


        return {
            "All ASTs from commit history" : allast_snippets,
            # "Current context: " + self.context + "\n" +
            "Required dependency" : all_library_names,
            "Original metadata" : metadata ,
            # "Functional set for the hunk" : f_set,
            # "Compilation set for the hunk" : c_set,
            # "Library information from Stable" : nested_values_libraries ,
            # "Function name information from Stable" : nested_values_function_names,
            # "Function call information from Stable" : nested_values_function_calls,
            # "Class name information from Stable" : nested_values_class_names,
            # "Class method call information from Stable" : nested_values_class_method_calls,
            "Target file" : self.targetfile,                           
            "Target method" : method
        }


    
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
             
    def get_string_representation(self, data):
        result = []
        for key, value in data.items():
            result.append(f'"{key}" : {value}')
        return "\n".join(result)
    
    def analyzeProgram(self, fineTuning = False, fineTuningFile = "transInput/Backports.jsonl", ftTraining = False, prompt = False, testingFile = ""):
        """
        Adapt the sourceOriginal to a stable version based on various inputs.

        Returns:
            str: The adapted source code, close to sourcebackport.
        """
        result = ""
        client = OpenAI()

        if fineTuning:
            # self.deleteFiles()
            client.files.create(
            file=open(fineTuningFile, "rb"),
            purpose="fine-tune"
            )        

        if ftTraining:
            client.fine_tuning.jobs.create(
            training_file="file-P44jFVRZVz7Y2dUvfvGXy2nP", 
            model="gpt-3.5-turbo"
            )
        if prompt:
            promptData = self.formatPromptData()
            completion = client.chat.completions.create(
                model="ft:gpt-3.5-turbo-0125:personal::9SXXjzCZ" if ftTraining else "gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Adapt the given code snippet based on the stable information below:\n"
                            + self.get_string_representation(promptData) + "\n" +
                            "Also follow these instructions carefully for precise adaptation.\n" 
                            "- Remove statements in the adapted hunk from the source hunk if their identifiers are not initialized within this target method or class"+ promptData["Target method"] +"\n"
                            "- Replace identifiers in the adapted code with those from library information, function calls, function names, class names, and class method calls of the stable version that are closely similar to the source code.\n"
                            "- Do not remove comments from the original source.\n"
                            "- Maintain the original indentation.\n"                            
                            # "- If the AST differences include statements that can align the adapted hunk with the STABLE version, incorporate them into the adapted code.\n"
                            "- Include required dependencies if they are new and not present in the stable version.\n"
                            "- If metadata mentions adding or removing statements for the stable version, make those changes in the adapted code.\n"
                            # "- Preserve statements related to Compilation and Functional sets in the adapted code.\n"                            
                        )
                    },
                    {
                        "role": "user",
                        "content": "Adapt this - " + self.sourceOriginal
                    }
                ]              
            )
            result = completion.choices[0].message     
   
        return result.content.replace('```python', '').replace('```', '').strip(), "Recom"
        # return "", "Recom"    



