class backSlicer():
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

        if self.metadata:
            adaptedSource += f"\n{str(self.metadata)}"

        if self.stableLibraris:
            adaptedSource += f"\n{str(self.stableLibraris)}"

        if self.targetfile:
            adaptedSource += f"\n{self.targetfile}"    

        return adaptedSource
