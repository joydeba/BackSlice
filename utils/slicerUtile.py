import ast, astunparse
import difflib
import re
import tokenize
import io
import git
from helperZER.pygithub_helper import *

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
    test_patterns = [
        # r'^test.*\.py$',  
        # r'^.*test\.py$',
        r".*test.*" 
        
    ]

    for file in files:
        for pattern in test_patterns:
            if re.match(pattern, file):
                return True
    return False

def get_ast_diffs(source_commits, startCommit=None, endCommit=None, startDate = None, endDate = None, repoName=None, projectName = None):
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
                if file.filename.endswith('.py'):
                    source_hunks = file.patch.split("@@ ")
                    for indexhunk in range(1, len(source_hunks)):
                        cleanhunk = source_hunks[indexhunk].split("@@\n")[1]
                        cleanhunk = cleanhunk.split("\n")
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
        except SyntaxError as e:
            print(f"SyntaxError in {commit['oid']}: {e}")
            asts.append((commit['oid'], None))  # Append None for invalid ASTs
            continue
    # Compare ASTs and generate differences
    diff_results = []

    for i in range(len(asts) - 1):
        commit_a, ast_a = asts[i]
        commit_b, ast_b = asts[i + 1]

        if ast_a is None or ast_b is None:
            diff_results.append((commit_a, commit_b, ["Invalid AST"]))
            continue

        stmts_a = [node for node in ast.walk(ast_a) if isinstance(node, ast.stmt)]
        stmts_b = [node for node in ast.walk(ast_b) if isinstance(node, ast.stmt)]

        stmts_a_str = [ast.dump(stmt) for stmt in stmts_a]
        stmts_b_str = [ast.dump(stmt) for stmt in stmts_b]

        diff = difflib.ndiff(stmts_a_str, stmts_b_str)
        diff_results.append((commit_a, commit_b, list(diff)))

    return diff_results

# # Example usage
# source_commits = ["commit1.py", "commit2.py", "commit3.py"]
# ast_diffs = get_ast_diffs(source_commits)

# for commit_a, commit_b, diff in ast_diffs:
#     print(f"Differences between {commit_a} and {commit_b}:")
#     for line in diff:
#         print(line)
#     print()

def get_hunk_context(file_content, hunk_start, hunk_end, context_lines=3):
    lines = file_content.split('\n')
    hunk_range = range(hunk_start, hunk_end)
    context = []

    for lineno in hunk_range:
        if lineno < 1 or lineno > len(lines):
            continue

        line = lines[lineno - 1]
        context.append(line)

    # Add surrounding lines as context
    for i in range(context_lines):
        before = hunk_start - i - 2
        after = hunk_end + i - 1

        if before >= 0:
            context.insert(0, lines[before])

        if after < len(lines):
            context.append(lines[after])

    return '\n'.join(context)

# # Example usage
# file_content = """
# def foo():
#     print("Hello")
    
# def bar():
#     print("World")
# """

# hunk_start = 2
# hunk_end = 4

# context = get_hunk_context(file_content, hunk_start, hunk_end)
# print(context)

def get_changeset_dependencies(source_code):
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

# # Example usage:
# source_code = """
# import os
# from math import sqrt
# import numpy as np
# from datetime import datetime
# """
# dependencies = get_changeset_dependencies(source_code)
# print(dependencies)

def get_changesets_and_metadata(pull_request, sourceB):
    """
    Extracts pull request title, body, tags, and comments from submitted source code.

    Args:
        pull_request (dict): Dictionary containing pull request details.
        sourceB (str): Source code submitted in the pull request.

    Returns:
        tuple: A tuple containing pull request title (str), body (str), tags (list of str), and comments (list of str).
    """
    title = pull_request.get('title', '')
    body = pull_request.get('body', '')
    tags = pull_request.get('tags', [])
    
    # Extract comments from the source code
    comments = []
    lines = sourceB.split('\n')
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

# # Example usage
# pull_request_data = {
#     'title': 'Add new feature',
#     'body': 'This pull request adds a new feature to the project.',
#     'tags': ['feature', 'enhancement'],
# }

# source_code = """
# # This is a single-line comment.
# def add(a, b):
#     """
#     This is a multi-line comment.
#     It explains the function purpose and usage.
#     """
#     return a + b
# """

# title, body, tags, comments = get_commentDoc_and_metadata(pull_request_data, source_code)

# print("Title:", title)
# print("Body:", body)
# print("Tags:", tags)
# print("Comments:", comments)


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

    for testCase in testCases:
        testCase = remove_comments_docstrings_fromString(testCase)
        sourceCode = remove_comments_docstrings_fromString(sourceCode)
        for line in testCase.split("\n"):
            entity = find_source_code_entity(sourceCode, line)
            if entity:
                functional_set.add(entity)

    return functional_set

# # Example usage
# source_code = "class MathUtils:\n    def add(self, a, b):\n        return a + b\n\ndef square(x):\n    return x * x\n\nresult = MathUtils().add(3, 5)\nsquared_result = square(result)"

# test_cases = [
#     ['result = MathUtils().add(3, 5)'],
#     ['squared_result = square(result)']
# ]

# functional_set = get_functional_set(source_code, test_cases[0])
# print(functional_set)



def get_compilation_set(sourceCode, functional_set):
    '''
    keep the element Elements that are referenced by the functional set.

    Following the test execution, all code entities referenced within the functional set are 
    ensured to be defined, regardless of whether they were traversed during the tests. 
    '''

    # Parse the source code into an abstract syntax tree (AST)
    tree = ast.parse(sourceCode)

    # Create a set to store referenced code entities
    referenced_entities = set()

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
            if isinstance(node, ast.FunctionDef) and node.name == func_entity:
                visit(node)

    return referenced_entities

# # Example usage
# source_code = '''
# def add(a, b):
#     return a + b

# def subtract(a, b):
#     return a - b

# def multiply(a, b):
#     return a * b

# def divide(a, b):
#     return a / b
# '''

# functional_entities = ['add', 'multiply']

# compilation_set = get_compilation_set(source_code, functional_entities)
# print(compilation_set)

# def adapttoSCM(self, sourceB = None):
#     '''
#     - Mapped back to the original commits/reverting unwanted changes
#     - Hunk dependencies
#     '''
#     dependencies = get_hunk_sets()
    

# def get_origin(fun_set=None, com_set= None):
#     commits = []
#     return commits

# def get_hunk_sets(commit=None):
#     dependencies = []
#     # Gether context 
#     return dependencies

def get_stable_version_libraries(owner, repo, branch, github_token=None):
    '''
    This function uses the GitHub API to retrieve the contents of the repository's branch, searches for Python files (.py extension), and parses the code using the ast module. It identifies import and from ... import statements to extract library usage, function definitions, and function calls.

    Replace github_username, repository_name, and your_github_personal_access_token with appropriate values. Also, remember to handle pagination if the repository has a large number of files.

    Keep in mind that this approach has limitations and may not catch all forms of function calls or more complex code patterns. You might need to enhance this function or use additional parsing techniques if your repository's codebase is intricate.
    '''
    base_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    headers = {}

    if github_token:
        headers['Authorization'] = f"Bearer {github_token}"

    response = requests.get(f"{base_url}?ref={branch}", headers=headers)

    library_info = {}

    if response.status_code == 200:
        contents = response.json()

        for item in contents:
            if item['type'] == 'file' and item['name'].endswith('.py'):
                file_url = item['download_url']
                file_content = requests.get(file_url, headers=headers).text

                try:
                    tree = ast.parse(file_content)
                except SyntaxError:
                    print(f"Error parsing {item['name']}. Skipping.")
                    continue

                libraries = []
                function_names = []
                function_calls = []

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

                library_info[item['name']] = {
                    'libraries': list(set(libraries)),
                    'function_names': list(set(function_names)),
                    'function_calls': list(set(function_calls))
                }

        return library_info

    else:
        print(f"Failed to fetch repository contents: {response.status_code}")
        return None

# # Example usage
# owner = "github_username"
# repo = "repository_name"
# branch = "main"
# github_token = "your_github_personal_access_token"

# library_info = get_stable_version_libraries(owner, repo, branch, github_token)
# print(library_info)
