

class Cslicer():
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
        adaptedSource = self.sourceOriginal  # Initialize with the original source

        if self.targetfile and self.functionalSet and self.compilationSet:
            # Check if targetfile contains statements related to functionalSet or compilationSet
            target_statements = self.targetfile.split("\n")  # Read the contents of targetfile

            # Iterate over the functionalSet and add statements to adaptedSource
            for statement in self.functionalSet:
                for t_statement in target_statements:
                    if statement in t_statement:
                        adaptedSource += f"\n{t_statement}"

            # Iterate over the compilationSet and add statements to adaptedSource
            for statement in self.compilationSet:
                for t_statement in target_statements:
                    if statement in t_statement:
                        adaptedSource += f"\n{t_statement}"

        return adaptedSource

    # def analyzeProgram(self):
        
    #     adaptedSource = None
    #     # Todo- with the help of astdiffsHistory, context, dependencies, metadata, functionalSet, compilationSet, stableLibraris - adapt sourceOriginal for stable version so that it can be close to sourcebackport
    #     # The form of the astdiffsHistory is (commit_a, commit_b, list(diff))
    #     # Context gives the sourceOriginal context code in string form 
    #     # Dependencies is list to give any new dependency chage for sourceOriginal
    #     # FunctionalSet is a set for for the function name covered by the test cases 
    #     # CompilationSet is a set for the function of sourceOriginal referenced by functionalSet 
    #     # Metadat is the - (title, body, tags, comments) of a pull requests 
    #     # StableLibraris is the library information in the form of - {dir_item['name']: {
    #     #     'libraries': list(set(libraries)),
    #     #     'function_names': list(set(function_names)),
    #     #     'function_calls': list(set(function_calls)),
    #     #     'class_names': list(set(class_names)),
    #     #     'class_method_calls': list(set(class_method_calls))
    #     # }}
    #     # targetfile is the string representation of the target source file 

    #     # The ligic should be something like this 
    #     # - targetFile has a staement related to functionalSet add it to sourceOriginal to adapt
    #     # - targetFile has a staement related to compilationSet add it to sourceOriginal to adapt

    #     return adaptedSource        
  
    # def analyzeProgram(self):
    #     slices = []
    #     '''
    #     - To preserve the "behavior" of the functional and compilation set elements, 
    #     the changes needed to be collected in reverse order, starting from the newest 
    #     change set ΔN and going back to the oldest one ΔO. This process will ensure 
    #     that the elements' behavior remains consistent throughout the changes.

    #     - The decision regarding whether to keep or remove entities is based on the 
    #     changes that occurred and their respective change types. Entities will be 
    #     retained if they belong to the functional or compilation set; otherwise, 
    #     they will be removed.


    #     - The sliced history incorporates an atomic change δ if it meets specific criteria. 
    #     These criteria include being an insertion or update to the entities within the functional
    #     set or an insertion to the entities in the compilation set. However, updates to the compilation
    #     set entities are disregarded as they typically do not impact the test results significantly.

    #     '''

    #     # Set (Λ) includes all fields explicitly initialized during declaration and all
    #     #  methods (and constructors) called during runtime.

    #     functinalSet = self.functionalSet
    #     compilationSet = self.compilationSet

    #     # The procedure COMPDEP analyzes refer- ence relations in pk and includes 
    #     # all referenced code entities of Λ into the compilation set Π.
    #     # set of rules for computing Π from [10]


    #     return slices
    

