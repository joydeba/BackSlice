import csv
import difflib
import sys
csv.field_size_limit(sys.maxsize)
import os
import sys
sys.path.insert(1, os.getcwd())
from helperZER.pygithub_helper import *
from utils.slicerUtile import *
from utils.metricUtile import *
import git
import subprocess
PIPE = subprocess.PIPE
import ast
from CSLICER import Cslicer
from BACkSLICE import BackSlicer
from BACkTRANS import BackTransformer
from github import Github
from sklearn.metrics import confusion_matrix, cohen_kappa_score
import numpy as np

def dataloading(prlist):
    with open(prlist,"r") as fp:
        reader = csv.reader(fp, delimiter=",", quotechar='"', dialect=csv.excel_tab)
        data_read = [row for row in reader]
    return data_read  

def accessKeyloading(repoName,projectName):
    g, backup_keys, no_bused_key, accesskey = initialize_G()
    repo = g.get_repo(repoName+"/"+projectName)        
    gLocal = git.Git(projectName)
    process = subprocess.Popen(["gh","auth","login","--with-token"], stdin=open("ghKeysconfig", "r"), cwd=projectName)
    stdoutput, stderroutput = process.communicate()  
    with open("ghKeysconfig", "r") as fpkey:
        ghkey = fpkey.read().rstrip() # Todo - We may need the secondary keys too     
    return gLocal, ghkey, repo  

def get_file_and_file_content(pull_id_original, pull_id_backport, line, repo, gLocal):
    branches = gLocal.branch()               

    pull_commitsSubmitted = ast.literal_eval(gLocal.execute(["gh", "pr", "view", pull_id_original, "--json", "commits"]))['commits']
    # pull_original = gLocal.execute(["gh", "pr", "view", pull_id_original])
    pull_backport = gLocal.execute(["gh", "pr", "view", pull_id_backport])
    pull_commitOriginal = gLocal.execute(["gh", "pr", "view", pull_id_original, "--json", "mergeCommit"])
    pull_commitBackports = gLocal.execute(["gh", "pr", "view", pull_id_backport, "--json", "mergeCommit"])
    targetStableBranch = ast.literal_eval(gLocal.execute(["gh", "pr", "view", pull_id_backport, "--json", "baseRefName"]))['baseRefName']
    if pull_commitOriginal == '{"mergeCommit":null}' or pull_commitBackports == '{"mergeCommit":null}':
        return None, None, None, None 
    targetStableBranch = line[3].strip()
    branch_exists = any(branch.strip() == targetStableBranch for branch in branches.split('\n'))

    creationStableBranch = None
    if not branch_exists:
        try:
            gLocal.branch(targetStableBranch)
        except Exception as e:               
            print(e)
            return None, None, None, None

    else:
        creationStableBranch = gLocal.execute(["git", "log", "--reverse", "--pretty=format:'%h %ad %s'", "--date=iso", targetStableBranch]).split('\n')[1]
        # git log --reverse  <branch-name> | tail -1
        
    # commitStartDate = commits_diffs_original[0].split("\n")[2].split("Date:   ")[1] if commits_diffs_original[0]!='' else print("Commit has no py files")
    # commitEndDate = creationStableBranch.split(" ")[1]        


    original_mergeCommits = ast.literal_eval(pull_commitOriginal)['mergeCommit']["oid"] if "null" not in pull_commitOriginal else None        
    backport_mergeCommits = ast.literal_eval(pull_commitBackports)['mergeCommit']["oid"] if "null" not in pull_commitBackports else None  

    original_parents_count = int(gLocal.execute(["git", "rev-list", "--parents", "-n", "1", original_mergeCommits]).count(" "))
    backport_parents_count = int(gLocal.execute(["git", "rev-list", "--parents", "-n", "1", backport_mergeCommits]).count(" "))       

    if original_parents_count == 2:
        commits_diffs_original = gLocal.execute(["git", "show", gLocal.execute(["git", "rev-list", "--parents", "-n", "1", original_mergeCommits]).split(" ")[-1], ":*.cc", ":*.py", ":*.c"]).split("\ndiff ") if original_mergeCommits else print("Merge commit missing")
    else:    
        commits_diffs_original = gLocal.execute(["git", "show", original_mergeCommits, ":*.cc", ":*.py", ":*.c"]).split("\ndiff ") if original_mergeCommits else print("Merge commit missing")
    if backport_parents_count == 2:
        commits_diffs_backport = gLocal.execute(["git", "show", gLocal.execute(["git", "rev-list", "--parents", "-n", "1", backport_mergeCommits]).split(" ")[-1], ":*.cc", ":*.py", ":*.c"]).split("\ndiff ") if backport_mergeCommits else print("Merge commit missing")                         
    else:          
        commits_diffs_backport = gLocal.execute(["git", "show", backport_mergeCommits, ":*.cc", ":*.py", ":*.c"]).split("\ndiff ") if backport_mergeCommits else print("Merge commit missing")    

    return commits_diffs_original, commits_diffs_backport, pull_commitsSubmitted, pull_backport


def getsimilarHunks(commits_diffs_original_contextHunks, commits_diffs_backport_contextHunks, indexHunks0, min_hunks_count):

    commits_hunkline_original_context = commits_diffs_original_contextHunks.split("\n")
    commits_hunkline_backport_context = commits_diffs_backport_contextHunks.split("\n")
    similarity_score = difflib.SequenceMatcher(None, commits_hunkline_original_context[0], commits_hunkline_backport_context[0]).ratio()
    if similarity_score > 0.60 or indexHunks0 == min_hunks_count - 1:
        pass
    else:
        for indexH in range(1, min_hunks_count):
            commits_hunkline_backport_context = commits_diffs_backport_contextHunks[indexH].split("\n")
            similarity_score = difflib.SequenceMatcher(None, commits_hunkline_original_context[0], commits_hunkline_backport_context[0]).ratio()
            if similarity_score > 0.60:
                break
            else:
                commits_hunkline_backport_context = commits_diffs_backport_contextHunks[indexHunks0].split("\n")
    return  commits_hunkline_original_context, commits_hunkline_backport_context                  

def get_padded_addedLines(commits_hunkline_context):
    leadingSpaces = 0
    commits_hunk_Lines = "" 
    for c_line in commits_hunkline_context:
        if c_line.startswith(("+")):
            c_line = c_line.replace("+", "")
            if leadingSpaces == 0:
                leadingSpaces = len(c_line) - len(c_line.lstrip())
            commits_hunk_Lines = commits_hunk_Lines + c_line[leadingSpaces:] + "\n"   

def get_hunk_details(commits_diffs_original, commits_diffs_backport):
    testhunks_original = []
    codehunks_original = []
    codehunks_backport = []
    codehunks_original_withContext = []
    codehunks_backport_withContext = []    
    if len(commits_diffs_backport) == len(commits_diffs_original):
        for indexO in range(1, len(commits_diffs_original)):
            if commits_diffs_original[indexO] is not None:
                filepath = commits_diffs_original[indexO].split("\n")[0]
                filepathBackport = commits_diffs_backport[indexO].split("\n")[0]   

                commits_diffs_original_contextHunks = commits_diffs_original[indexO].split("\n@@ ")
                commits_diffs_backport_contextHunks = commits_diffs_backport[indexO].split("\n@@ ")  

                original_hunks_count = len(commits_diffs_original_contextHunks)
                backport_hunks_count = len(commits_diffs_backport_contextHunks)

                min_hunks_count = min(original_hunks_count, backport_hunks_count)

                for indexHunks0 in range(1, min_hunks_count):                                                                          

                    commits_hunkline_original_context, commits_hunkline_backport_context = getsimilarHunks(commits_diffs_original_contextHunks[indexHunks0], commits_diffs_backport_contextHunks[indexHunks0], indexHunks0, min_hunks_count)

                    # hunkStartLnNo = commits_hunkline_original_context[0].split(" ")[0][1:].split(",")
                    # hunkEndlnNo = commits_hunkline_original_context[0].split(" ")[1][1:].split(",")

                    commits_hunk_originalLines = get_padded_addedLines(commits_hunkline_original_context)    
                    commits_hunk_backportLines = get_padded_addedLines(commits_hunkline_backport_context)                                  



                    if commits_hunk_originalLines:    
                        codehunks_original.append(commits_hunk_originalLines)
                        codehunks_original_withContext.append(commits_diffs_original_contextHunks[indexHunks0])

                    if commits_hunk_backportLines:    
                        codehunks_backport.append(commits_hunk_backportLines)
                        codehunks_backport_withContext.append(commits_diffs_backport_contextHunks[indexHunks0])


    return  codehunks_original, codehunks_backport, testhunks_original, codehunks_original_withContext, filepathBackport

def get_targetfile(repo, pull_id_original, pull_id_backport, filepathBackport):
    previousBackportfullFileTarget = None
    pullOriginal = repo.get_pull(int(pull_id_original))
    pullBackport = repo.get_pull(int(pull_id_backport))
    backport_filesContents = []
    previous_backport_filesContents = []     
    for fileB in pullBackport.get_files():
        try:
            previous_backport_filesContents.append({fileB.filename: repo.get_contents(fileB.filename, ref=pullBackport.base.sha).decoded_content.decode('utf-8')})
        except Exception as e:
            print("Error occurred in retrieving previous backport files:", e)
            try:
                backport_filesContents.append({fileB.filename: repo.get_contents(fileB.filename, ref=pullBackport.head.sha).decoded_content.decode('utf-8')})
            except Exception as e:
                print("Error occurred in retrieving backport files:", e)
                continue                
    try:
        file_path = filepathBackport.split(" ")[2]
    except: 
        file_path = filepathBackport.split(" ")[0]      

    if previous_backport_filesContents:
        for itemBcontent in previous_backport_filesContents:
            temp_itemBcontent = itemBcontent.copy()
            filepathBackport, fullFilecontentBackport = temp_itemBcontent.popitem()
            if filepathBackport == file_path[2:]:    
                previousBackportfullFileTarget = fullFilecontentBackport  

    backport_fullFileTarget = None
    if backport_filesContents:
        for itemBcontent in backport_filesContents:
            temp_itemBcontent = itemBcontent.copy()
            filepathBackport, fullFilecontentBackport = temp_itemBcontent.popitem()
            if filepathBackport == file_path[2:]:
                backport_fullFileTarget = fullFilecontentBackport  

    if previousBackportfullFileTarget is None:
        previousBackportfullFileTarget = backport_fullFileTarget    

    return filepathBackport, previousBackportfullFileTarget                                                                                                   
                                
def saveMetricResults(slicedPRs, projectName, data_read, numberofSlicingRequired, numberofDifferences, has_test_and_code, numberOfSuccesfulSlicing):
    with open("slicerOutput/"+projectName+"InconICFDiffzBackTransNoNeedTest.txt", 'w') as f:   
        print("Total Labeled Backporting PRs", len(data_read), file=f)
        print("Total Sliced Required", numberofSlicingRequired, file=f)
        print("Total Number of Hunk Differences", numberofDifferences, file=f)
        print("Total Hunks Have Test and Code", has_test_and_code, file=f)
        print("Total Succesfully Sliced", numberOfSuccesfulSlicing, file=f)
        if slicedPRs:
            average_bleu_score, bleu_scores = calculate_average_bleu_score(slicedPRs)
            average_meteor_score, meteor_scores = calculate_average_meteor_score(slicedPRs)
            average_code_bleu, code_bleu_scores = calculate_average_code_bleu_score(slicedPRs)  
            average_rouge_l_score, rouge_l_scores = calculate_average_rouge_l_score(slicedPRs)  
            average_chrf_score, chrf_scores = calculate_average_chrf_score(slicedPRs) 
            print(f"Average BLEU Score: {average_bleu_score}", file=f)
            print(f"Average METEOR Score: {average_meteor_score}", file=f) 
            print(f"Average CodeBLEU Score: {average_code_bleu}", file=f)       
            print(f"Average ROUGE-L Score: {average_rouge_l_score}", file=f)
            print(f"Average CHRF Score: {average_chrf_score}", file=f)            
            threshold = 0.5
            binary_bleu = np.array([1 if score >= threshold else 0 for score in bleu_scores])
            binary_meteor = np.array([1 if score >= threshold else 0 for score in meteor_scores])
            binary_code_bleu = np.array([1 if score >= threshold else 0 for score in code_bleu_scores])
            binary_rouge_l = np.array([1 if score >= threshold else 0 for score in rouge_l_scores])
            binary_chrf = np.array([1 if score >= threshold else 0 for score in chrf_scores])

            conf_matrix_bleu_meteor = confusion_matrix(binary_bleu, binary_meteor)
            conf_matrix_bleu_code_bleu = confusion_matrix(binary_bleu, binary_code_bleu)
            conf_matrix_bleu_rouge_l = confusion_matrix(binary_bleu, binary_rouge_l)
            conf_matrix_bleu_chrf = confusion_matrix(binary_bleu, binary_chrf)

            kappa_bleu_meteor = cohen_kappa_score(binary_bleu, binary_meteor)
            kappa_bleu_code_bleu = cohen_kappa_score(binary_bleu, binary_code_bleu)
            kappa_bleu_rouge_l = cohen_kappa_score(binary_bleu, binary_rouge_l)
            kappa_bleu_chrf = cohen_kappa_score(binary_bleu, binary_chrf)

            print(f"Cohen's Kappa between BLEU and Meteor: {kappa_bleu_meteor}", file=f)
            print("Confusion Matrix BLEU vs Meteor:", file=f)
            print(conf_matrix_bleu_meteor, file=f)

            print(f"Cohen's Kappa between BLEU and CodeBLEU: {kappa_bleu_code_bleu}", file=f)
            print("Confusion Matrix BLEU vs CodeBLEU:", file=f)
            print(conf_matrix_bleu_code_bleu, file=f)

            print(f"Cohen's Kappa between BLEU and ROUGE-L: {kappa_bleu_rouge_l}", file=f)
            print("Confusion Matrix BLEU vs ROUGE-L:", file=f)
            print(conf_matrix_bleu_rouge_l, file=f)

            print(f"Cohen's Kappa between BLEU and CHRF: {kappa_bleu_chrf}", file=f)
            print("Confusion Matrix BLEU vs CHRF:", file=f)
            print(conf_matrix_bleu_chrf, file=f)    

def saveChanges(output1, slicedPRs):
    with open(output1, "wt") as fp:
        writer = csv.writer(fp, delimiter=",")
        flattened_data = [item for sublist in slicedPRs for item in sublist]
        for pair in flattened_data:
            writer.writerow([pair[0]])
            writer.writerow(["-------------------------------------------------------------------------"])
            writer.writerow([pair[1]])
            writer.writerow(["-------------------------------------------------------------------------"])
            writer.writerow([pair[2]])
            writer.writerow(["-------------------------------------------------------------------------"])
            writer.writerow([pair[3]])
            writer.writerow(["-------------------------------------------------------------------------"])
            writer.writerow(["========================================================================="])


def mainCSLICER(prlist = 'prlist.csv', default_branch='main', dictOfActiveBranches = {}, repoName="repoName", projectName = 'projectName', output1="outputCSLICER.csv", stableBranch = "mainCSLICER"):
    """ 
    This function slices for changesets by CSLICER.
    """
    data_read = dataloading(prlist)
    gLocal, ghkey, repo = accessKeyloading(repoName, projectName)


    numberofSlicingRequired = 0
    numberOfSuccesfulSlicing = 0
    numberofDifferences = 0
    has_test_and_code = 0
    slicedPRs = []

    for idx, line in enumerate(data_read):

        # g, no_bused_key, load_object = changeG(g, accesskey, backup_keys, no_bused_key, load_object) 
        # if load_object:
        #     repo = g.get_repo(repository)
        #     print("New G loaded")
        #     load_object = 0

        backport_slices = ""               
        original_slices = "" 
        slicesfromCSLICER = []
        fullFileTarget = None

    
        try:
            repository = line[1].replace('https://github.com/', '')
            user_name, repo_name, pullN, pull_request_id, filesN = repository.split("/")
            repository = user_name.strip() + "/" + repo_name.strip()
        
            print("Working on repo", repo_name)                       

            pull_id_original = line[1].replace("https://github.com/"+repository.strip()+"/pull/", "").split("/")[0].strip()
            pull_id_backport = line[0].replace("https://github.com/"+repository.strip()+"/pull/", "").split("/")[0].strip()




            commits_diffs_original, commits_diffs_backport, pull_commitsSubmitted, pull_backport = get_file_and_file_content(pull_id_original, pull_id_backport, line, repo, gLocal)

            if commits_diffs_original is None or commits_diffs_backport is None or pull_commitsSubmitted is None or pull_backport is None:
             continue
            codehunks_original, codehunks_backport, testhunks_original, codehunks_original_withContext, filepathBackport = get_hunk_details(commits_diffs_original, commits_diffs_backport)

            filepathBackport, previousBackportfullFileTarget = get_targetfile(repo, pull_id_original, pull_id_backport, filepathBackport)

            numberofSlicingRequired = numberofSlicingRequired + 1

            if testhunks_original and codehunks_original and codehunks_backport:
                has_test_and_code = has_test_and_code + 1

            slicebyCslicer = None
            if codehunks_original and codehunks_backport:
                context_index = 0 
                for codeHunk, codeHunkBackport  in zip(codehunks_original, codehunks_backport): 
                                                
                        functionalSetforHunk = get_functional_set(codeHunk, testCases = testhunks_original)
                        astdiffshistory = get_ast_diffs(source_commits = pull_commitsSubmitted, startCommit=None, endCommit=None, startDate = None, endDate = None, repoName=repoName, projectName =projectName) 
                        # slicer = Cslicer(sourceOriginal = codeHunk,
                        #                     sourcebackport = codeHunkBackport, 
                        #                     astdiffsHistory = astdiffshistory, 
                        #                     context = get_hunk_context(file_content = codehunks_original_withContext[context_index], hunk_start = hunkStartLnNo, hunk_end = hunkEndlnNo, context_lines=3), 
                        #                     dependencies = get_changeset_dependencies(previousBackportfullFileTarget), 
                        #                     metadata = get_changesets_and_metadata(pull_request = pull_backport, sourceO = codeHunkBackport), 
                        #                     functionalSet = functionalSetforHunk, 
                        #                     compilationSet= get_compilation_set(sourceCode = codeHunk, functional_set = functionalSetforHunk), 
                        #                     stableLibraris = get_stable_version_libraries(owner = repoName, repo = projectName, branch = targetStableBranch, github_token=ghkey, cache_file= projectName+"StableLibraryCsche"), 
                        #                     targetfile = previousBackportfullFileTarget)
                        # slicer = BackSlicer(sourceOriginal = codeHunk,
                        #                     sourcebackport = codeHunkBackport, 
                        #                     astdiffsHistory = astdiffshistory, 
                        #                     context = get_hunk_context(file_content = codehunks_original_withContext[context_index]), 
                        #                     dependencies = get_changeset_dependencies(previousBackportfullFileTarget), 
                        #                     metadata = get_changesets_and_metadata(pull_request = pull_backport, sourceO = codeHunkBackport), 
                        #                     functionalSet = functionalSetforHunk, 
                        #                     compilationSet= get_compilation_set(sourceCode = codeHunk, functional_set = functionalSetforHunk), 
                        #                     stableLibraris = get_stable_version_libraries(owner = repoName, repo = projectName, branch = stableBranch, github_token=ghkey, cache_file= projectName+"StableLibraryCsche"), 
                        #                     targetfile = previousBackportfullFileTarget)   
                        slicer = BackTransformer(sourceOriginal = codeHunk,
                                            sourcebackport = codeHunkBackport, 
                                            astdiffsHistory = astdiffshistory, 
                                            context = get_hunk_context(file_content = codehunks_original_withContext[context_index]), 
                                            dependencies = get_changeset_dependencies(previousBackportfullFileTarget), 
                                            metadata = get_changesets_and_metadata(pull_request = pull_backport, sourceO = codeHunk), 
                                            functionalSet = functionalSetforHunk, 
                                            compilationSet= get_compilation_set(sourceCode = codeHunk, functional_set = functionalSetforHunk), 
                                            stableLibraris = get_stable_version_libraries(owner = repoName, repo = projectName, branch = stableBranch, github_token=ghkey, cache_file= projectName+"StableLibraryCsche"), 
                                            targetfile = previousBackportfullFileTarget,
                                            tfileName=filepathBackport)                                                    
                        context_index = context_index +1 

                        file_pathJsonl = 'transInput/' + projectName + 'Backports.jsonl'

                        # if sample_count < 15:                            
                        data = slicer.prepareFinetuneData()
                        slicer.saveData(data, 'transInput/'+projectName+'Backports.jsonl')
                        # sample_count = sample_count + 1     

                        slicebyCslicer, recommendation = slicer.analyzeProgram(fineTuning = True, fineTuningFile = file_pathJsonl, ftTraining = False, prompt = False)
                        recommendation = recommendation + "\nPRs: "+ pull_id_original  + ", "  + pull_id_backport
                        if slicebyCslicer:
                            numberOfSuccesfulSlicing = numberOfSuccesfulSlicing + 1                
                            slicesfromCSLICER.append((codeHunk ,slicebyCslicer, codeHunkBackport, recommendation))                                 

                print("Working on pulls ", pull_id_original, pull_id_backport)
                if slicesfromCSLICER:
                    slicedPRs.append(slicesfromCSLICER)

        except Exception as e:
            print("Problem in pulls ", pull_id_original, pull_id_backport)
            if slicesfromCSLICER:
                slicedPRs.append(slicesfromCSLICER)                    
            print(e)
            continue
    
    saveMetricResults(slicedPRs, projectName, data_read, numberofSlicingRequired, numberofDifferences, has_test_and_code, numberOfSuccesfulSlicing)
    saveChanges(output1, slicedPRs)


# # Updated on 11th April 2023
# ansibleDictOfActiveBranches = {'devel':{}, 'stable-2.9':{}, 'stable-2.12':{}, 'stable-2.14':{}, 'stable-2.13':{}, 'stable-2.15':{}, 'stable-2.16':{}}
# ansibleDictOfActiveBranches = {"stable-2.3": 2, "stable-2.4": 1, "stable-2.5": 2, "stable-2.6": 49, "stable-2.7": 458, "stable-2.8": 603, "stable-2.9": 706, "stable-2.10": 294, "stable-2.11": 0, "temporary-2.9.1-branch-releng-only": 27}
# bitcoinDictOfActiveBranches = {'master':{}, '25.x':{}, '24.x':{}, '23.x':{}, '22.x':{}, '27.x':{}, '26.x':{}}
# bitcoinDictOfActiveBranches = { '0.19': {}, '0.20': {}, '0.21': {}, '0.18': {}, '0.17': {}, '0.16': {}, '0.15': {}, '0.14': {}, '0.13': {}, '0.12': {}, '0.11': {}, '0.10': {},'0.9.3': {}}
# ElasticsearchDictOfActiveBranches = {'main':{}, '8.8':{}, '7.17':{}, '8.7':{}, '8.5':{}, '8.6':{}, '8.0':{}, '8.1':{}, '8.2':{}, '8.3':{},'8.4':{}, '6.5':{}}
# JuliaDictOfActiveBranches = {'master':{}, 'release-1.9':{}, 'release-1.8':{}, 'release-1.6':{}}
# RailsDictOfActiveBranches = {'main':{}, '7-0-stable':{}, '6-1-stable':{}, '6-0-stable':{}}
# KibanaDictOfActiveBranches = {'main':{}, '8.8':{}, '8.7':{}, '8.6':{}, '8.5':{}, '8.4':{}, '7.17':{}, '8.2':{}, '8.3':{}}
# cpythonDictOfActiveBranches = {'main':{}, '3.12':{}, '3.11':{}, '3.10':{}, '3.9':{}, '3.8':{}, '3.0.x':{}}
# cmsswDictOfActiveBranches = {'master':{}, 'CMSSW_14_1_DEVEL_X':{}, 'CMSSW_14_1_X':{}, 'CMSSW_14_0_X':{}, 'CMSSW_13_0_HeavyIon_X':{}, 'CMSSW_10_6_X':{}, 'CMSSW_13_2_X':{}, 'CMSSW_13_3_X':{}, 'CMSSW_12_4_X':{}, 'CMSSW_13_0_X':{}, 'CMSSW_12_6_X':{}, 'CMSSW_13_1_X':{}, 'CMSSW_14_0_DEVEL_X':{}, 'CMSSW_7_1_X':{}, 'CMSSW_12_5_X':{}}
saltDictOfActiveBranches = {'master':{}, '3006.x':{}, '3007.x':{}, '3005.x':{}, '2018.3':{}, '2019.2':{}, 'freeze':{} }
# ansibleDefault_branch = 'devel' # Python 87.8% ---------
# bitcoinDefault_branch = 'master' # Python 20.1% ---------
# ElasticsearchDefault_branch = 'main' # Python 0.0%
# JuliaDefault_branch = 'master' # Python 0.0%
# RailsDefault_branch = 'main' # Python 0.0%
# KibanaDefault_branch = 'main' # Python 0.0%
# cpythonDefault_branch = 'main' # Python 62.8% --------- X
# cmsswDefault_branch = 'master' # Python 28.6% ---------
# bootstrapDefault_branch = "main" # Python 0.0%
# electronDefault = "main" # Python 1.9%
# magento2Default = "2.4-develop" # Python 0.0%
# nextcloudDefault = "maser" # Python 0.0%
# nixpkgsDefault = "master" #  Python 1.2%
# owncloudDefault  = "maser" # Python 0.0%
saltDefault_branch  = "maser" # Python 97.8% --------- X

# file_regex = ":*.cpp", ":*.py", ":*.c"
mainCSLICER('data_cmp_incmpWithTest/Manual_incmp_Salt_backport_keywordsPRsNoTestNeeded.csv', 
saltDefault_branch,
saltDictOfActiveBranches,
'saltstack',
'salt',
'slicerOutput/Incmp_BackTrans_Salt_backport_keywordsPRsNoNeedTest.csv',
'Stable-V'
)
