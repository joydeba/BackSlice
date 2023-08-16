from utils.slicerUtile import *

class Cslicer():
    def __init__(self, startCommit=None, endCommit=None, startDate = None, endDate = None):
        self.startCommit = startCommit
        self.endCommit = endCommit
        self.startDate = startDate
        self.endDate = endDate
  
    def analyzeProgram(self, sourceBbase= None, originalHistory = None, testCases = None):
        slices = []
        '''
        - To preserve the "behavior" of the functional and compilation set elements, 
        the changes needed to be collected in reverse order, starting from the newest 
        change set ΔN and going back to the oldest one ΔO. This process will ensure 
        that the elements' behavior remains consistent throughout the changes.

        - The decision regarding whether to keep or remove entities is based on the 
        changes that occurred and their respective change types. Entities will be 
        retained if they belong to the functional or compilation set; otherwise, 
        they will be removed.


        - The sliced history incorporates an atomic change δ if it meets specific criteria. 
        These criteria include being an insertion or update to the entities within the functional
        set or an insertion to the entities in the compilation set. However, updates to the compilation
        set entities are disregarded as they typically do not impact the test results significantly.

        '''

        # Set (Λ) includes all fields explicitly initialized during declaration and all
        #  methods (and constructors) called during runtime.

        functinalSet = get_functional_set()
        compilationSet = get_compilation_set()

        # The procedure COMPDEP analyzes refer- ence relations in pk and includes 
        # all referenced code entities of Λ into the compilation set Π.
        # set of rules for computing Π from [10]


        return slices
    

