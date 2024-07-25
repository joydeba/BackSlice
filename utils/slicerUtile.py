import ast, astunparse
import difflib
import re
import tokenize
import io
import git
from helperZER.pygithub_helper import *
import requests
import os
import json
import mypy.api
import io
import keyword


def remove_comments_docstrings_fromString(fsring):
    '''
    Strips comments and docstrings from a python file.
    '''
    stripped_code = ""

    lines = astunparse.unparse(ast.parse(fsring)).split('\n')
    for line in lines:
        if line.lstrip()[:1] not in ("'", '"'):
            if line != '':
                stripped_code = stripped_code + line + '\n'

    return stripped_code


def has_test_files(files):
    # test_patterns = [
    #     # r'^test.*\.py$',  
    #     # r'^.*test\.py$',
    #     r".*test.*" 
        
    # ]

    # for file in files:
    #     for pattern in test_patterns:
    #         if re.match(pattern, file):
    #             return True
    # return False
    return True


def get_ast_diffs(source_commits, startCommit=None, endCommit=None, startDate = None, endDate = None, repoName=None, projectName = None, fileInfo = None):
    asts = []  # List to store parsed ASTs for each commit
    g, backup_keys, no_bused_key, accesskey = initialize_G()
    repo = g.get_repo(repoName+"/"+projectName)
    # gLocal = git.Git(projectName)
    # Parse source code and generate AST for each commit
    for commit in source_commits:
        try:
            source_code = ""
            source_commit = repo.get_commit(commit['oid'])
            for file in source_commit.files:
                if os.path.basename(file.filename) in fileInfo and file.filename.endswith('.py'):
                    cleanhunk = file.patch.split("\n")
                    leadingSpacesOri = 0
                    cleanhunkLines = ""
                    for c_line in cleanhunk:
                        if c_line.startswith(("+")):
                            c_line = c_line.replace("+", "")
                            if leadingSpacesOri == 0:
                                leadingSpacesOri = len(c_line) - len(c_line.lstrip())
                            cleanhunkLines = cleanhunkLines + c_line.replace(c_line[:leadingSpacesOri], "") + "\n"
                                
                    source_code = remove_comments_docstrings_fromString(cleanhunkLines)
                    parsed_ast = ast.parse(source_code)
                    asts.append((commit['oid'], parsed_ast))
        except Exception as e:
            # We have to ignore this since the error is mostly for incomplete code
            print(f"Ignore for some - SyntaxError in {commit['oid']}: {e}")
            asts.append((commit['oid'], None))  # Append None for invalid ASTs
            continue
    # Compare ASTs and generate differences
    diff_results = []

    for i in range(len(asts) - 1):
        commit_a, ast_a = asts[i]
        commit_b, ast_b = asts[i + 1]

        if ast_a is None or ast_b is None:
            # diff_results.append((commit_a, commit_b, ["Invalid AST"]))
            continue

        stmts_a = [node for node in ast.walk(ast_a) if isinstance(node, ast.stmt)]
        stmts_b = [node for node in ast.walk(ast_b) if isinstance(node, ast.stmt)]

        stmts_a_str = [ast.dump(stmt) for stmt in stmts_a]
        stmts_b_str = [ast.dump(stmt) for stmt in stmts_b]

        diff = difflib.ndiff(stmts_a_str, stmts_b_str)
        diff_results.append((commit_a, commit_b, list(diff)))

    return diff_results


def get_hunk_context(file_content, hunk_start = None, hunk_end = None, context_lines=3): 
    file_content = file_content.split("@@ ")[1] if '@@ ' in file_content else file_content.split("@@")[1] 
    lines = file_content.split('\n')
    context = []

    for i in range(len(lines)):
        if lines[i].startswith('+') or lines[i].startswith('-'):    
            continue
        else:
            context.append(lines[i])   

    return '\n'.join(context)

def get_method_or_class_name(file_content):
    start_index = file_content.find('def')
    if start_index == -1:
        start_index = file_content.find('class')

    if start_index != -1:
        file_content = file_content[start_index:]

    pattern = r'^\s*(def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(\([^)]*\))?\s*'
    match = re.search(pattern, file_content, re.MULTILINE)
    
    if match:
        method_or_class_name = match.group(2)
    else:
        method_or_class_name = None
    return method_or_class_name

def get_changeset_dependencies(source_code):
    if source_code is None:
        return None
    dependencies = set()

    def visit_Import(node):
        for alias in node.names:
            dependencies.add(alias.name)

    def visit_ImportFrom(node):
        module_name = node.module
        if module_name is not None:
            dependencies.add(module_name)
    
    tree = ast.parse(source_code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            visit_Import(node)
        elif isinstance(node, ast.ImportFrom):
            visit_ImportFrom(node)
    
    return list(dependencies)


def get_changesets_and_metadata(pull_request, sourceO):
    """
    Extracts pull request title, body, tags, and comments from submitted source code.

    Args:
        pull_request (dict): Dictionary containing pull request details.
        sourceB (str): Source code submitted in the pull request.

    Returns:
        tuple: A tuple containing pull request title (str), body (str), tags (list of str), and comments (list of str).
    """

    title = ""
    body = ""
    tags = ""

    pull_lines = pull_request.split("\n")
    for index in range(len(pull_lines)):
        if index <= 11:
            key, value = pull_lines[index].split("\t")
            if key == "title:":
                title = value
            if key == 'labels:':
                 tags = value
        else: 
            body = body + pull_lines[index]        
    
    # Extract comments from the source code
    comments = []
    lines = sourceO.split('\n')
    is_comment_block = False
    comment_block = []

    for line in lines:
        stripped_line = line.strip()
        
        if stripped_line.startswith('#') or stripped_line.startswith('//'):
            # Single-line comment
            comments.append(stripped_line.lstrip('#').lstrip('//').strip())
        elif stripped_line.startswith('"""') or stripped_line.startswith("'''"):
            # Multi-line comment start
            is_comment_block = True
            comment_block.append(stripped_line.lstrip('"""').lstrip("'''").strip())
        elif is_comment_block and (stripped_line.endswith('"""') or stripped_line.endswith("'''")):
            # Multi-line comment end
            is_comment_block = False
            comment_block.append(stripped_line.rstrip('"""').rstrip("'''").strip())
            comments.append('\n'.join(comment_block))
            comment_block = []
        elif is_comment_block:
            # Inside multi-line comment
            comment_block.append(stripped_line)

    return title, body, tags, comments


def find_source_code_entity(source_code_toTest, test_case_line):
    parsed_source_code_tree = ast.parse(source_code_toTest)

    class EntityVisitor(ast.NodeVisitor):
        def __init__(self, test_case_line):
            self.test_case_line = test_case_line
            self.found_entity = None

        def visit_FunctionDef(self, node):
            if self._matches_test_case(node.name):
                self.found_entity = node.name

        def visit_ClassDef(self, node):
            if self._matches_test_case(node.name):
                self.found_entity = node.name

        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name) and self._matches_test_case(target.id):
                    self.found_entity = target.id

        def visit_Import(self, node):
            for alias in node.names:
                if self._matches_test_case(alias.name):
                    self.found_entity = alias.name

        def visit_ImportFrom(self, node):
            for alias in node.names:
                if self._matches_test_case(alias.name):
                    self.found_entity = alias.name
        """
        User-defined and built-in entities only - excluded common keywords while, for, if, try, and except
        """
        # def visit_While(self, node):
        #     if self._matches_test_case("while"):
        #         self.found_entity = "while"

        # def visit_For(self, node):
        #     if self._matches_test_case("for"):
        #         self.found_entity = "for"

        # def visit_If(self, node):
        #     if self._matches_test_case("if"):
        #         self.found_entity = "if"

        # def visit_Try(self, node):
        #     if self._matches_test_case("try"):
        #         self.found_entity = "try"

        # def visit_Except(self, node):
        #     if self._matches_test_case("except"):
        #         self.found_entity = "except"

        def visit_Module(self, node):
            # Traverse module-level entities
            for item in node.body:
                self.visit(item)

        def _matches_test_case(self, entity_name):
            if entity_name:
                return True
                # if entity_name in self.test_case_line:
                #     return True
                # else:
                #     return False
            else:
                return False    

    visitor = EntityVisitor(test_case_line)
    visitor.visit(parsed_source_code_tree)

    return visitor.found_entity


def get_functional_set(sourceCode, testCases):
    '''
    The set of elements of the sourceCode directly involved in a test case.

    During the execution of testCases, the set of source code entities
    (such as methods or classes) of sourceCode that include the statements being
    traversed by testCases is referred to as the functional set, symbolized as Λ.

    Args:
        sourceCode (str): The source code to analyze.
        testCases (list): List of test cases.

    Returns:
        set: The functional set of source code entities involved in the test cases.
    '''

    '''
    This code uses the ast module to traverse the abstract syntax tree of the Python source code. The EntityVisitor class defines methods to visit function and class definitions and checks if the target line from the test cases falls within their range. If a match is found, the entity name is stored in the found_entity attribute. The get_functional_set function then calls find_source_code_entity for each test case line and builds the functional set based on the found entities.
    '''

    functional_set = set()

    try:
        for testCase in testCases:
            testCase = remove_comments_docstrings_fromString(testCase)
            sourceCode = remove_comments_docstrings_fromString(sourceCode)
            for line in testCase.split("\n"):
                entity = find_source_code_entity(sourceCode, line)
                if entity:
                    functional_set.add(entity)
    except:
        return list(functional_set)                

    return list(functional_set)


def get_compilation_set(sourceCode, functional_set):
    '''
    keep the element Elements that are referenced by the functional set.

    Following the test execution, all code entities referenced within the functional set are 
    ensured to be defined, regardless of whether they were traversed during the tests. 
    '''

    # Create a set to store referenced code entities
    referenced_entities = set()

    try:
    # Parse the source code into an abstract syntax tree (AST)
        tree = ast.parse(sourceCode)
    except:
        return list(referenced_entities)     


    # Helper function to recursively traverse the AST and find references
    def visit(node):
        if isinstance(node, ast.Name):
            referenced_entities.add(node.id)
        for child in ast.iter_child_nodes(node):
            visit(child)

    # Traverse the AST and find references in the functional set
    for func_entity in functional_set:
        # Search for the entity in the AST and add its references
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef) or isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                if node.name == func_entity:
                    visit(node)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == func_entity:
                        visit(node)                  

    return list(referenced_entities)


def get_stable_version_libraries(owner, repo, branch, github_token=None, cache_file="StableCacheLibrary.txt"): 
    # Check if a cache file exists and load information from it if available.
    file_count = 0
    if cache_file and os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)

    base_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    headers = {}

    if github_token:
        headers['Authorization'] = f"Bearer {github_token}"

    response = requests.get(f"{base_url}?ref={branch}", headers=headers)

    library_info = {}

    def process_directory(url, headers, library_info):
        print("Processing a directory------------------------------------------------")
        dir_response = requests.get(url, headers=headers)
        if dir_response.status_code == 200:
            dir_contents = dir_response.json()
            for item in dir_contents:
                if item['type'] == 'file' and item['name'].endswith('.py'):
                    file_info = process_file(item['download_url'])
                    library_info[item['name']] = file_info                 
                elif item['type'] == 'dir':
                    process_directory(item['url'], headers, library_info)

    def process_file(file_url):         
        print("Processing a file------------------------------------------------")    
        file_content = requests.get(file_url, headers=headers).text

        try:
            tree = ast.parse(file_content)
        except Exception:
            print(f"Error parsing {file_url}. Skipping.")
            return

        libraries = []
        function_names = []
        function_calls = []
        class_names = []
        class_method_calls = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    libraries.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if node.module:
                        libraries.append(f"{node.module}.{alias.name}")
            elif isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    function_calls.append(node.func.id)
            elif isinstance(node, ast.ClassDef):
                class_names.append(node.name)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    class_method_calls.append(f"{node.value.id}.{node.attr}")
        print("Returning file info -----------------------------------------------")
        return {
            'libraries': list(set(libraries)),
            'function_names': list(set(function_names)),
            'function_calls': list(set(function_calls)),
            'class_names': list(set(class_names)),
            'class_method_calls': list(set(class_method_calls))
        }

    if response.status_code == 200:
        contents = response.json()
        for item in contents:
            try:
                if file_count>50:
                    break
                if item['type'] == 'file' and item['name'].endswith('.py'):
                    file_info = process_file(item['download_url'])
                    library_info[item['name']] = file_info
                    file_count = file_count + 1
                elif item['type'] == 'dir':
                    process_directory(item['url'], headers, library_info)
            except Exception as e:
                print(e)
                continue                

        # Save the retrieved information to the cache file.
        if cache_file:
            with open(cache_file, 'w') as f:
                json.dump(library_info, f)
        print("Returning library info ---------------------------------")
        return library_info

    else:
        print(f"Failed to fetch repository contents: {response.status_code}")
        return None


def find_missing_imports(code: str) -> list:

    try: 
        # Parse the code into an Abstract Syntax Tree (AST)
        tree = ast.parse(code)

        # Collect all import names from the AST
        import_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_names.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                import_names.add(node.module)

        # Collect all module names used in the code
        module_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                module_names.add(node.id)

        # Identify missing imports
        missing_imports = [module for module in module_names if module not in import_names]
    except:
        return ""    

    return ", ".join(missing_imports)



def extract_method_class_definition(file_content, name):
    tree = ast.parse(file_content)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            start_lineno = node.lineno
            end_lineno = node.body[-1].end_lineno
            lines = file_content.splitlines()[start_lineno-1:end_lineno]
            method_definition = '\n'.join(lines).strip()
            return method_definition
        elif isinstance(node, ast.ClassDef) and node.name == name:
            start_lineno = node.lineno
            end_lineno = node.body[-1].end_lineno
            lines = file_content.splitlines()[start_lineno-1:end_lineno]
            class_definition = '\n'.join(lines).strip()
            return class_definition
    return ""