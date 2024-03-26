
# Dependencies
# https://pypi.org/project/cve-bin-tool/ [forFuture]
# https://pypi.org/project/nvdlib/
# https://bandit.readthedocs.io/en/latest/
# https://pyre-check.org
# https://github.com/pyupio/safety

import json
import re
import Levenshtein
import bandit
from bandit.core import config
from bandit.core import manager as b_manager
import subprocess
import json
import os
from utils.slicerUtile import *

class BackSlicer():
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
        adaptedSource = self.sourceOriginal  # Initialize with the original source

        if self.dependencies:
            # Convert dependencies list to a set for efficient matching
            existing_dependencies = set(self.dependencies)
            # Iterate over lines in the adaptedSource to check for existing dependencies
            source_lines = adaptedSource.split('\n')
            for i, line in enumerate(source_lines):
                for dep in existing_dependencies:
                    if dep in line:
                        # If any existing dependency is found, replace it with the new dependencies
                        source_lines[i] = line.replace(dep, ', '.join(existing_dependencies))
                        break
                else:
                    continue
                break
            else:
                # If no existing dependency is found, add new dependencies at the top
                source_lines.insert(0, ', '.join(self.dependencies))
            # Update adaptedSource with modified lines
            adaptedSource = '\n'.join(source_lines)


        if self.astdiffsHistory and self.functionalSet and self.compilationSet:
            # Iterate over astdiffsHistory to check for statements related to functionalSet or compilationSet
            for commit_a, commit_b, diff in self.astdiffsHistory:
                for change in diff:
                    for statement in (self.functionalSet | self.compilationSet):
                        if statement in change and statement not in adaptedSource:
                            # If a statement from functionalSet or compilationSet is not already in adaptedSource, add it
                            adaptedSource += f"\n{change}"

        # Add the adaptedSource in the middle of the context for further adaptation
        # adaptedSource = self.context.replace('{{INSERT_HERE}}', adaptedSource)

        # Check and update stableLibraris
        if self.stableLibraris:
            for lib_name, lib_info in self.stableLibraris.items():
                if lib_info:
                # Replace information about method names
                    if lib_info['function_names']:
                        for method_name in lib_info['function_names']:
                                adaptedSource = self.replace_semantically_related(adaptedSource, method_name, method_name)

                    # Replace information about method calls
                    if lib_info['function_calls']:    
                        for method_call in lib_info['function_calls']:
                                adaptedSource = self.replace_semantically_related(adaptedSource, method_call, method_call)


        # Extract keywords from pull request metadata
        keywords = self.extract_keywords_from_metadata()

        # Use metadata information to guide code adaptation
        adaptedSource, recommendation = self.adapt_code_based_on_metadata(adaptedSource, keywords)

        # Security check to guide the adaptation process
        
        adaptedSource = self.adapt_code_based_on_SecurityCheck(adaptedSource)

        if self.targetfile:
            adaptedSource, method_info = self.adapt_and_extract_method_info(adaptedSource, self.targetfile)

        missing_dependenciesAST = find_missing_imports(adaptedSource)
        missing_dependenciesAST = missing_dependenciesAST.split(", ")
        # missing_dependenciesMyPy = check_imports_from_string(adaptedSource)    

        recommendation_to_add = "\nMake sure statements concerning these methods are incorporated into the stable script - "
        recommendation_to_remove = "\nEnsure statements related to these methods are omitted from the stable script, or provide definitions for them if necessary -"

        if self.stableLibraris and missing_dependenciesAST:
            added_methods = set()  

            for method_name in missing_dependenciesAST:
                found = False
                for library_name, library_info in self.stableLibraris.items():
                    if library_info:
                        for name in library_info['function_names'] + library_info['function_calls'] + library_info['class_method_calls'] + library_info['libraries']:
                            if method_name in name:
                                recommendation_to_add += f"\n{method_name}"  
                                added_methods.add(method_name)
                                found = True
                                break
                    if found:
                        break

            for method_name in missing_dependenciesAST:
                if method_name not in added_methods:
                    recommendation_to_remove += f"\n{method_name}"

        recommendation = recommendation_to_add + "\n" + recommendation_to_remove                                                                                                               

        return adaptedSource, recommendation


    def adapt_and_extract_method_info(self, adapted_source, targetfile):
        """
        Adapt method calls in the source code to include parameters based on the presence of targetfile
        and extract method names and parameters from Python source code.

        Args:
            adapted_source (str): The source code to be adapted.
            targetfile (str): The name of the parameter to be included.

        Returns:
            tuple: A tuple containing the adapted source code and a dictionary with method information.
        """
        method_info = {}
        adapted_source_result = adapted_source

        # Regular expression pattern to match method definitions
        method_pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\):"

        # Find all method definitions in the adapted source code
        matches = re.findall(method_pattern, adapted_source, re.MULTILINE | re.DOTALL)

        # Iterate over matches and extract method names and parameters
        for match in matches:
            method_name = match[0]
            parameters = match[1].split(',') if match[1] else []
            parameters = [param.strip() for param in parameters]
            method_info[method_name] = parameters

        # If targetfile is present, adapt method calls to include parameters
        if targetfile in adapted_source:
            # Construct method call pattern
            method_call_pattern = re.compile(rf"{method_name}\((.*?)\)")

            # Check if method call exists and if there are parameters to include
            if method_call_pattern.search(adapted_source):
                # Construct parameter assignments
                parameters = ", ".join([f"{param}={param}" for param in method_info[method_name]])

                # Replace method call with method call including parameters
                adapted_source_result = method_call_pattern.sub(f"{method_name}({parameters})", adapted_source)

        return adapted_source_result, method_info


    def adapt_code_based_on_metadata(self, source, keywords):
        """
        Adapt the source code based on pull request metadata.

        Parameters:
            source (str): The source code to be modified.
            keywords (list): List of keywords extracted from pull request metadata.

        Returns:
            str: The modified source code.
        """
        recommendation = ""
        # Example: Modify the code based on the presence of specific keywords
        for keyword in keywords:
            if keyword.lower() == 'fix':
                # Add a fix comment in the code
                recommendation += '\n# This code includes a fix for the reported issue.'
            
            elif keyword.lower() == 'feature':
                # Add feature-specific code or comments
                recommendation += '\n# New feature added based on the pull request.'

            elif keyword.lower() == 'test':
                # Include additional testing-related code or comments
                recommendation += '\n# Test cases might require backporting as well.'

            # Add more conditions based on other specific keywords
            # elif keyword.lower() == 'keyword':
            #     # Corresponding modification for the specific keyword
            #     source += '\n# Code modification related to the keyword.'

        return source, recommendation


    def replace_semantically_related(self, source, old_value, new_value):
        """
        Replace semantically related portions in the source code using Levenshtein distance.

        Parameters:
            source (str): The source code to be modified.
            old_value (str): The old value to be replaced.
            new_value (str): The new value to replace the old one.

        Returns:
            str: The modified source code.
        """
        # Calculate Levenshtein distance for each word in the source and replace if below a certain threshold
        if source is None:
            return None

        lines = source.split('\n')
        updated_lines = []

        for line in lines:
            words_and_spaces = line.split(' ')
            updated_words_and_spaces = []

            for item in words_and_spaces:
                lev_dis = Levenshtein.distance(item, old_value)
                if len(old_value) > 4 and lev_dis > 0 and lev_dis < 2 and item[-1] != "(" and item[-1] != "," and item[-1] != ":":
                    updated_words_and_spaces.append(old_value)
                else:
                    updated_words_and_spaces.append(item)

            updated_line = ' '.join(updated_words_and_spaces)
            updated_lines.append(updated_line)

        return '\n'.join(updated_lines)

    def extract_keywords_from_metadata(self):
        """
        Extract keywords from pull request metadata.

        Returns:
            list: List of keywords.
        """
        title_keywords = self.extract_keywords_from_text(self.metadata[0])
        body_keywords = self.extract_keywords_from_text(self.metadata[1])
        tag_keywords = self.extract_keywords_from_tags(self.metadata[2].split(","))
        comment_keywords = self.extract_keywords_from_comments(self.metadata[3])

        # Combine keywords from different sources
        all_keywords = title_keywords + body_keywords + tag_keywords + comment_keywords

        # Remove duplicates and return the final list
        return list(set(all_keywords))

    def extract_keywords_from_text(self, text):
        """
        Extract keywords from text.

        Parameters:
            text (str): Input text.

        Returns:
            list: List of keywords.
        """
        # Tokenize the text based on word boundaries and filter based on length
        words = re.findall(r'\b\w+\b', text)
        keywords = [word.lower() for word in words if len(word) > 2]  # Adjust the length criteria as needed
        return keywords

    def extract_keywords_from_tags(self, tags):
        """
        Extract keywords from tags.

        Parameters:
            tags (list): List of tags.

        Returns:
            list: List of keywords.
        """
        # Assuming tags are simple strings, extract keywords similarly to text
        tag_keywords = [tag.lower().strip() for tag in tags]
        return tag_keywords

    def extract_keywords_from_comments(self, comments):
        """
        Extract keywords from comments.

        Parameters:
            comments (list): List of comments.

        Returns:
            list: List of keywords.
        """
        # Assuming comments are simple strings, extract keywords similarly to text
        comment_keywords = [self.extract_keywords_from_text(comment) for comment in comments]
        return [keyword for sublist in comment_keywords for keyword in sublist]  # Flatten the list

    def adapt_code_based_on_SecurityCheck(self, source):
        security_info = self.get_security_issuesBandit(source)
        if security_info:
            # Modify the code to remove the identified vulnerability
            adapted_source = self.remove_vulnerability(source, security_info)
            return adapted_source

        # If the keyword is not recognized or not CVE-related, return the original source
        return source

    def remove_vulnerability(self, source, cve_info):
        """
        Remove the identified vulnerability from the source code.

        Parameters:
            source (str): The source code containing the vulnerability.
            cve_info (dict): Information about the CVE.

        Returns:
            str: The modified source code with the vulnerability removed.
        """
        # Example: Replace the vulnerable code with a safe alternative or remove it entirely
        vulnerable_code = cve_info.get('vulnerable_code', '')
        safe_alternative = cve_info.get('safe_alternative', '')

        adapted_source = source.replace(vulnerable_code, safe_alternative)
        return adapted_source
       
        
    def get_security_issuesBandit(self, source_code):
        try:
            # Write the source code to a temporary file
            with open('temp_file.py', 'w') as file:
                file.write(source_code)

            # Run Bandit scan on the temporary file
            bandit_command = ['bandit', '--format', 'json', 'temp_file.py']
            bandit_output = subprocess.check_output(bandit_command, text=True)

            # Parse Bandit output and extract information about identified issues
            issue_info = []
            try:
                bandit_data = json.loads(bandit_output)
                for issue in bandit_data['results']:
                    issue_info.append({
                        'filename': issue['filename'],
                        'line_number': issue['line'],
                        'issue_text': issue['test_id'],
                        'severity': issue['issue_severity'],
                    })
            except json.JSONDecodeError as json_error:
                print(f"Error decoding Bandit output: {json_error}")

            return issue_info
        except subprocess.CalledProcessError as e:
            # Handle exceptions if any
            print(f"An error occurred while running Bandit: {e}")
            return None
        finally:
            # Clean up temporary file
            try:
                subprocess.run(['rm', 'temp_file.py'])
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary file: {cleanup_error}")


    def get_security_issuesPyre(self, source_code):
        # Does not work properly for me : works with directory and so many dependencies
        try:
            # Create a temporary directory
            temp_dir = 'temp_dir'
            os.makedirs(temp_dir, exist_ok=True)

            # Write the source code to a temporary file in the temporary directory
            temp_file_path = os.path.join(temp_dir, 'temp_file.py')
            with open(temp_file_path, 'w') as file:
                file.write(source_code)

            # Run Pyre for static analysis on the temporary directory
            pyre_command = ['pyre', 'analyze', '--source-directory', temp_dir]
            pyre_output = subprocess.check_output(pyre_command, text=True)

            # Parse Pyre output and extract information about identified issues
            issue_info = []
            try:
                pyre_data = json.loads(pyre_output)
                for issue in pyre_data.get('errors', []):
                    if issue['path'] == temp_file_path:
                        issue_info.append({
                            'filename': issue.get('path'),
                            'line_number': issue.get('line'),
                            'issue_text': issue.get('message'),
                            'severity': 'Pyre does not provide explicit severity levels, so set it accordingly',
                        })
            except json.JSONDecodeError as json_error:
                print(f"Error decoding Pyre output: {json_error}")

            return issue_info
        except subprocess.CalledProcessError as e:
            # Handle exceptions if any
            print(f"An error occurred while running Pyre: {e}")
            return None
        finally:
            # Clean up temporary directory
            try:
                subprocess.run(['rm', '-r', temp_dir])
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary directory: {cleanup_error}")


    def get_security_issuesSafty(self, source_code):
        try:
            # Write the source code to a temporary file
            with open('temp_file.py', 'w') as file:
                file.write(source_code)

            # Run safety check on the temporary file
            safety_output = subprocess.check_output(['safety', 'check', '--file', 'temp_file.py'])

            # Parse safety output and extract information about identified issues
            issue_info = []
            try:
                safety_data = json.loads(safety_output)
                for vulnerability in safety_data.get('results', []):
                    issue_info.append({
                        'vulnerability_id': vulnerability.get('vulnerability_id'),
                        'package': vulnerability.get('name'),
                        'version': vulnerability.get('installed_version'),
                        'description': vulnerability.get('advisory'),
                        'severity': vulnerability.get('severity'),
                    })
            except json.JSONDecodeError as json_error:
                print(f"Error decoding safety output: {json_error}")

            return issue_info
        except subprocess.CalledProcessError as e:
            # Handle exceptions if any
            print(f"An error occurred while running safety check: {e}")
            return None
        finally:
            # Clean up temporary file
            try:
                subprocess.run(['rm', 'temp_file.py'])
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary file: {cleanup_error}")
