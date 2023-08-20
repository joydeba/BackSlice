import csv
import difflib
import sys
csv.field_size_limit(sys.maxsize)
import os
import sys
sys.path.insert(1, os.getcwd())
from helperZER.pygithub_helper import *
from utils.slicerUtile import *
import git
import subprocess
PIPE = subprocess.PIPE
import ast
from CSLICER import Cslicer


def mainCSLICER(prlist = 'prlist.csv', default_branch='main', dictOfActiveBranches = {}, repoName="repoName", projectName = 'projectName', output1="outputCSLICER.csv"):
    """ 
    This function slices for changesets by CSLICER.
    """
    with open(prlist,"rU") as fp:
        reader = csv.reader(fp, delimiter=",", quotechar='"', dialect=csv.excel_tab)
        data_read = [row for row in reader]
        gLocal = git.Git(projectName)
        process = subprocess.Popen(["gh","auth","login","--with-token"], stdin=open("ghKeysconfig", "r"), cwd=projectName)
        stdoutput, stderroutput = process.communicate()
        numberofSlicingRequired = 0
        numberOfSuccesfulSlicing = 0
        slicedPRs = []                             

        sliced_prs_commits = []        
        for idx, line in enumerate(data_read):
            backport_slices = ""               
            original_slices = "" 
            try:
                repository = line[1].replace('https://github.com/', '')
                user_name, repo_name, pullN, pull_request_id, filesN = repository.split("/")
                repository = user_name.strip() + "/" + repo_name.strip()
            
                print("Working on repo", repo_name)                       


                pull_id_original = line[1].replace("https://github.com/"+repository.strip()+"/pull/", "").split("/")[0].strip()
                pull_id_backport = line[0].replace("https://github.com/"+repository.strip()+"/pull/", "").split("/")[0].strip()

                pull_commitOriginal = gLocal.execute(["gh", "pr", "view", pull_id_original, "--json", "mergeCommit"])
                pull_commitBackports = gLocal.execute(["gh", "pr", "view", pull_id_backport, "--json", "mergeCommit"])
                original_mergeCommits = ast.literal_eval(pull_commitOriginal)['mergeCommit']["oid"]          
                backport_mergeCommits = ast.literal_eval(pull_commitBackports)['mergeCommit']["oid"]   

                commits_diffs_original = gLocal.execute(["git", "show", original_mergeCommits, ":*.py"]).split("\n@@ ")
                commits_diffs_backport = gLocal.execute(["git", "show", backport_mergeCommits, ":*.py"]).split("\n@@ ")

                # Todo
                testCommits_diffs_original = None
                codeCommits_diffs_original = None
                commitStart = None
                commitEnd = None 
                commitStartDate = None
                commitEndDate = None 
                hunkStartLnNo = None 
                hunkEndlnNo = None


                for indexO in range(1, len(commits_diffs_original)):
                    if commits_diffs_original[indexO] is not None:
                        commits_diffs_original_contextHunks = commits_diffs_original[indexO].split("\n \n")
                        # commits_diffs_backport_contextHunks = commits_diffs_backport[indexO].split("\n \n")
                        for indexHunks0 in range(0, len(commits_diffs_original_contextHunks)):
                            commits_diffs_original_context = commits_diffs_original_contextHunks[indexHunks0].split("\n")
                            # commits_diffs_backport_context = commits_diffs_backport_contextHunks[indexHunks0].split("\n")
                            
                            commits_diffs_originalLines = ""
                            # commits_diffs_backportLines = ""

                            leadingSpacesOri = len(commits_diffs_original_context[0].replace("+", "").replace("-", "")) - len(commits_diffs_original_context[0].replace("+", "").replace("-", "").lstrip())
                            # leadingSpacesBac = len(commits_diffs_backport_context[0].replace("+", "").replace("-", "")) - len(commits_diffs_backport_context[0].replace("+", "").replace("-", "").lstrip())
                            for c_line in commits_diffs_original_context:
                                if c_line.startswith(("+")):
                                    c_line = c_line.replace("+", "")
                                    commits_diffs_originalLines = commits_diffs_originalLines + c_line.replace(c_line[:leadingSpacesOri], "") + "\n" 
                            # for c_line in commits_diffs_backport_context:
                            #     if c_line.startswith(("+")):
                            #         c_line = c_line.replace("+", "")
                            #         commits_diffs_backportLines = commits_diffs_backportLines + c_line.replace(c_line[:leadingSpacesBac], "") + "\n"   
                            numberofSlicingRequired = numberofSlicingRequired + 1
                            functionalSetforHunk = get_functional_set(commits_diffs_originalLines, testCases = [])
                            cslicer = Cslicer(sourceOriginal = commits_diffs_originalLines, 
                                              astdiffsHistory = get_ast_diffs(source_commits = original_mergeCommits, startCommit=None, endCommit=None, startDate = None, endDate = None), 
                                              context = get_hunk_context(file_content = indexHunks0, hunk_start = 0, hunk_end = 0, context_lines=3), 
                                              dependencies = get_changeset_dependencies(commits_diffs_original), 
                                              metadata = get_changesets_and_metadata(pull_request = pull_id_original, sourceB = indexHunks0), 
                                              functionalSet = functionalSetforHunk, 
                                              compilationSet= get_compilation_set(sourceCode = commits_diffs_originalLines, functional_set = functionalSetforHunk), 
                                              stableLibraris = get_stable_version_libraries(owner = repoName, repo = projectName, branch = dictOfActiveBranches, github_token=None))
                            slicebyCslicer = cslicer.analyzeProgram()
                            
                            if slicebyCslicer:
                                break                                   
                    
                    if slicebyCslicer:
                        numberOfSuccesfulSlicing = numberOfSuccesfulSlicing + 1                

                    print("Working on pulls ", pull_id_original, pull_id_backport)
                    slicedPRs.append(slicebyCslicer)

            except Exception as e:
                print("Problem in pulls")
                print(e)
                continue

    with open(projectName+"InconICFDiff", 'w') as f:   
        print("Total Labeled Backporting PRs", len(data_read), file=f)
        print("Total Sliced Required", numberofSlicingRequired, file=f)
        print("Total Succesfully Sliced", numberOfSuccesfulSlicing, file=f)


    
    with open(output1, "wt") as fp:
        writer = csv.writer(fp, delimiter=",")
        writer.writerows(slicedPRs)   


# # Updated on 11th April 2023
# ansibleDictOfActiveBranches = {'devel':{}, 'stable-2.9':{}, 'stable-2.12':{}, 'stable-2.14':{}, 'stable-2.13':{}, 'stable-2.15':{}}
# bitcoinDictOfActiveBranches = {'master':{}, '25.x':{}, '24.x':{}, '23.x':{}, '22.x':{}}
# ElasticsearchDictOfActiveBranches = {'main':{}, '8.8':{}, '7.17':{}, '8.7':{}, '8.5':{}, '8.6':{}, '8.0':{}, '8.1':{}, '8.2':{}, '8.3':{},'8.4':{}, '6.5':{}}
# JuliaDictOfActiveBranches = {'master':{}, 'release-1.9':{}, 'release-1.8':{}, 'release-1.6':{}}
# RailsDictOfActiveBranches = {'main':{}, '7-0-stable':{}, '6-1-stable':{}, '6-0-stable':{}}
# KibanaDictOfActiveBranches = {'main':{}, '8.8':{}, '8.7':{}, '8.6':{}, '8.5':{}, '8.4':{}, '7.17':{}, '8.2':{}, '8.3':{}}
cpythonDictOfActiveBranches = {'main':{}, '3.12':{}, '3.11':{}, '3.10':{}, '3.9':{}, '3.8':{}}
# ansibleDefault_branch = 'devel'
# bitcoinDefault_branch = 'master'
# ElasticsearchDefault_branch = 'main'
# JuliaDefault_branch = 'master'
# RailsDefault_branch = 'main'
# KibanaDefault_branch = 'main'
cpythonDefault_branch = 'main'
mainCSLICER('data_cmp_incmpWithTest/Manual_incmp_Cpython_backport_keywordsPRs.csv', 
cpythonDefault_branch,
cpythonDictOfActiveBranches,
'python',
'cpython',
'data_cmp_incmpWithTest/Incmp_CSLICER_Cpython_backport_keywordsPRs.csv')

