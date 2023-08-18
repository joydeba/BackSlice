import ast
import difflib

def get_ast_diffs(source_commits):
    asts = []  # List to store parsed ASTs for each commit

    # Parse source code and generate AST for each commit
    for commit in source_commits:
        with open(commit, 'r') as f:
            source_code = f.read()
            try:
                parsed_ast = ast.parse(source_code)
                asts.append((commit, parsed_ast))
            except SyntaxError as e:
                print(f"SyntaxError in {commit}: {e}")
                asts.append((commit, None))  # Append None for invalid ASTs

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

def get_hunk_dependencies(sourceB):
    pass

def get_changeset_dependencies(sourceB):
    pass

def get_changesets_and_metadata(sourceB):
    pass

def get_contexts(sourceB):
    pass

def get_functional_set(sourceB):
    '''
    The set of elements directly involved in a test case.

    During the execution of a test, the set of source code entities 
    (such as methods or classes) that include the statements being 
    traversed is referred to as the functional set, symbolized as Λ. 
    In the present example, the functional set comprises {Boo.boo2, Bar.bar1}.
    '''
    pass

def get_compilation_set(sourceB):
    '''
    Elements that are referenced by the functional set.

    Following the test execution, all code entities referenced within the functional set are 
    ensured to be defined, regardless of whether they were traversed during the tests. 
    The entities included in the compilation set are {Boo, Boo.b, Bar}.
    '''
    pass

def adapttoSCM(self, sourceB = None):
    '''
    - mapped back to the original commits/reverting unwanted changes
    - hunk dependencies

    '''
    dependencies = get_hunk_sets()
    pass

def get_origin(fun_set=None, com_set= None):
    commits = []
    return commits

def get_hunk_sets(commit=None):
    dependencies = []
    # Gether context 
    return dependencies

def get_stable_version_libraries(sVersion, sourceB):
    pass
