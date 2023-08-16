def get_ast_diffs(sourceO, sourceB):
    pass

def get_hunk_dependencies(hunksB):
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
