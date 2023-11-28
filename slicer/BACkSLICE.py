# https://pypi.org/project/cve-bin-tool/ [forFuture]
# https://pypi.org/project/nvdlib/
import nvdlib  
import json
import re
import Levenshtein


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
        # Assuming the CVE dataset is stored in a JSON file
        self.cve_dataset_file_path = 'path/to/cve_dataset.json'
        self.cve_dataset = self.load_cve_dataset()                


    def analyzeProgram(self):
        """
        Adapt the sourceOriginal to a stable version based on various inputs.

        Returns:
            str: The adapted source code, close to sourcebackport.
        """
        adaptedSource = self.sourceOriginal  # Initialize with the original source

        # Check and update dependencies
        if self.dependencies:
            # Convert dependencies list to a set for efficient matching
            existing_dependencies = set(self.dependencies)
            # Iterate over lines in the adaptedSource to check for existing dependencies
            source_lines = adaptedSource.split('\n')
            for i, line in enumerate(source_lines):
                if any(dep in line for dep in existing_dependencies):
                    # If any existing dependency is found, replace it with the new dependencies
                    source_lines[i] = ', '.join(self.dependencies)
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
                # Replace information about method names
                for method_name in lib_info['function_names']:
                    adaptedSource = self.replace_semantically_related(adaptedSource, method_name, method_name)

                # Replace information about method calls
                for method_call in lib_info['function_calls']:
                    adaptedSource = self.replace_semantically_related(adaptedSource, method_call, method_call)


        # Extract keywords from pull request metadata
        keywords = self.extract_keywords_from_metadata()

        # Use the extracted keywords to guide the adaptation process
        for keyword in keywords:
            adaptedSource = self.adapt_code_based_on_keyword(adaptedSource, keyword)

        return adaptedSource



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
        words = source.split()
        updated_words = [new_value if Levenshtein.distance(word, old_value) < 3 else word for word in words]
        return ' '.join(updated_words)

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

    def adapt_code_based_on_keyword(self, source, keyword):
        """
        Adapt the code based on a specific keyword, with a focus on CVE-related keywords.

        Parameters:
            source (str): The source code to be modified.
            keyword (str): The keyword to guide the adaptation process.

        Returns:
            str: The modified source code.
        """
        # # Example: Handle CVE-related keywords
        # if keyword.lower() == 'cve':
        #     cve_id = self.extract_cve_id_from_metadata()
        #     if cve_id:
        cve_info = self.get_cve_info_from_dataset(keyword)
        if cve_info:
            # Modify the code to remove the identified vulnerability
            adapted_source = self.remove_vulnerability(source, cve_info)
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

    def extract_cve_id_from_metadata(self):
        """
        Extract CVE ID from metadata.

        Returns:
            str: CVE ID or None if not found.
        """
        # Example: Extract CVE ID from title or body (adjust based on your metadata structure)
        cve_id_candidates = [word for word in (self.metadata['title'] + ' ' + self.metadata['body']).split() if word.startswith('CVE-')]
        return cve_id_candidates[0] if cve_id_candidates else None         

    def get_cve_info_from_dataset(self, cve_id):
        """
        Retrieve CVE information from the CVE Bin Tool.

        Parameters:
            cve_id (str): CVE ID.

        Returns:
            dict: CVE information or None if not found.
        """
        try:
            cve_info = nvdlib.searchCVE(keywordSearch = cve_id)
            return cve_info
        except Exception as e:
            print(f"Error: Unable to retrieve CVE information for {cve_id}. Error: {str(e)}")
            return None

    def load_cve_dataset(self):
        """
        Load the CVE dataset from a JSON file.

        Returns:
            dict: CVE dataset.
        """
        try:
            with open(self.cve_dataset_file_path, 'r') as file:
                cve_dataset = json.load(file)
            return cve_dataset
        except FileNotFoundError:
            print(f"Error: CVE dataset file not found at {self.cve_dataset_file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Unable to decode JSON in CVE dataset file at {self.cve_dataset_file_path}")
            return {}            