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
from github import Github
from sklearn.metrics import confusion_matrix, cohen_kappa_score
import numpy as np


def mainCSLICER(prlist = 'prlist.csv', default_branch='main', dictOfActiveBranches = {}, repoName="repoName", projectName = 'projectName', output1="outputCSLICER.csv"):
    """ 
    This function slices for changesets by CSLICER.
    """
    with open(prlist,"r") as fp:
        reader = csv.reader(fp, delimiter=",", quotechar='"', dialect=csv.excel_tab)
        data_read = [row for row in reader]
        g, backup_keys, no_bused_key, accesskey = initialize_G()
        repo = g.get_repo(repoName+"/"+projectName)        
        gLocal = git.Git(projectName)
        process = subprocess.Popen(["gh","auth","login","--with-token"], stdin=open("ghKeysconfig", "r"), cwd=projectName)
        stdoutput, stderroutput = process.communicate()
        numberofSlicingRequired = 0
        numberOfSuccesfulSlicing = 0
        numberofDifferences = 0
        has_test_and_code = 0
        slicedPRs = []
        branches = gLocal.branch()
        with open("ghKeysconfig", "r") as fpkey:
            ghkey = fpkey.read().rstrip() # Todo - We may need the secondary keys too 
        
                             
        sliced_prs_commits = []        
        for idx, line in enumerate(data_read):
            backport_slices = ""               
            original_slices = "" 
            slicesfromCSLICER = []
            fullFileTarget = None
            if line[2].strip() != '0':
                try:
                    repository = line[1].replace('https://github.com/', '')
                    user_name, repo_name, pullN, pull_request_id, filesN = repository.split("/")
                    repository = user_name.strip() + "/" + repo_name.strip()
                
                    print("Working on repo", repo_name)                       


                    pull_id_original = line[1].replace("https://github.com/"+repository.strip()+"/pull/", "").split("/")[0].strip()
                    pull_id_backport = line[0].replace("https://github.com/"+repository.strip()+"/pull/", "").split("/")[0].strip()

                    pullOriginal = repo.get_pull(int(pull_id_original))
                    pullBackport = repo.get_pull(int(pull_id_backport))

                    original_filesContents = []
                    backport_filesContents = []

                    for fileO in pullOriginal.get_files():
                        original_filesContents.append({fileO.filename:repo.get_contents(fileO.filename, ref=pullOriginal.head.sha).decoded_content.decode('utf-8')})
                    for fileB in pullBackport.get_files():
                        backport_filesContents.append({fileB.filename:repo.get_contents(fileB.filename, ref=pullBackport.head.sha).decoded_content.decode('utf-8')})


                    pull_commitsSubmitted = ast.literal_eval(gLocal.execute(["gh", "pr", "view", pull_id_original, "--json", "commits"]))['commits']
                    pull_original = gLocal.execute(["gh", "pr", "view", pull_id_original])
                    pull_backport = gLocal.execute(["gh", "pr", "view", pull_id_backport])
                    pull_commitOriginal = gLocal.execute(["gh", "pr", "view", pull_id_original, "--json", "mergeCommit"])
                    pull_commitBackports = gLocal.execute(["gh", "pr", "view", pull_id_backport, "--json", "mergeCommit"])
                    # targetStableBranch = ast.literal_eval(gLocal.execute(["gh", "pr", "view", pull_id_backport, "--json", "baseRefName"]))['baseRefName']
                    if pull_commitOriginal == '{"mergeCommit":null}' or pull_commitBackports == '{"mergeCommit":null}':
                        continue 
                    targetStableBranch = line[3].strip()
                    branch_exists = any(branch.strip() == targetStableBranch for branch in branches.split('\n'))
                    
                    
                    if not branch_exists:
                            gLocal.branch(targetStableBranch)

                    else:
                            creationStableBranch = gLocal.execute(["git", "log", "--reverse", "--pretty=format:'%h %ad %s'", "--date=iso", targetStableBranch]).split('\n')[1]
                            # git log --reverse  <branch-name> | tail -1


                    original_mergeCommits = ast.literal_eval(pull_commitOriginal)['mergeCommit']["oid"] if "null" not in pull_commitOriginal else None        
                    backport_mergeCommits = ast.literal_eval(pull_commitBackports)['mergeCommit']["oid"] if "null" not in pull_commitBackports else None  

                    commits_diffs_original = gLocal.execute(["git", "show", original_mergeCommits, ":*.py"]).split("\ndiff ") if original_mergeCommits else print("Merge commit missing")
                    commits_diffs_backport = gLocal.execute(["git", "show", backport_mergeCommits, ":*.py"]).split("\ndiff ") if backport_mergeCommits else print("Merge commit missing")

                    # Todo
                    testhunks_original = []
                    codehunks_original = []
                    codehunks_backport = []
                    codehunks_original_withContext = []
                    codehunks_backport_withContext = []
                    # codeFiles = []
                    
                    commitStartDate = commits_diffs_original[0].split("\n")[2].split("Date:   ")[1] if commits_diffs_original[0]!='' else print("Commit has no py files")
                    commitEndDate = creationStableBranch.split(" ")[1]

                    if len(commits_diffs_backport) == len(commits_diffs_original):
                        for indexO in range(1, len(commits_diffs_original)):
                            # Check the odd index for test cases [Todo]
                            is_test_code = False
                            is_test_codeB = False
                            if commits_diffs_original[indexO] is not None:
                                filepath = commits_diffs_original[indexO].split("\n")[0]
                                filepathBackport = commits_diffs_backport[indexO].split("\n")[0]                            
                            if has_test_files([filepath]):
                                is_test_code = True
                            if has_test_files([filepathBackport]):
                                is_test_codeB = True                                                    
                            commits_diffs_original_contextHunks = commits_diffs_original[indexO].split("\n@@ ")
                            commits_diffs_backport_contextHunks = commits_diffs_backport[indexO].split("\n@@ ")
                            for indexHunks0 in range(1, len(commits_diffs_original_contextHunks)):

                                commits_hunkline_original_context = commits_diffs_original_contextHunks[indexHunks0].split("\n")
                                commits_hunkline_backport_context = commits_diffs_backport_contextHunks[indexHunks0].split("\n")
                                hunkStartLnNo = commits_hunkline_original_context[0].split(" ")[0][1:].split(",")
                                hunkEndlnNo = commits_hunkline_original_context[0].split(" ")[1][1:].split(",")

                                commits_hunk_originalLines = ""
                                commits_hunk_backportLines = ""                            
                                commits_hunkTest_originalLines = ""
                                commits_hunkTest_backportLines = ""
                                # commits_diffs_backportLines = ""

                                # Todo check first hunk line 
                                # leadingSpacesBac = len(commits_diffs_backport_context[0].replace("+", "").replace("-", "")) - len(commits_diffs_backport_context[0].replace("+", "").replace("-", "").lstrip())
                                leadingSpacesOri = 0
                                for c_line in commits_hunkline_original_context:
                                    if c_line.startswith(("+")):
                                        c_line = c_line.replace("+", "")
                                        if leadingSpacesOri == 0:
                                            leadingSpacesOri = len(c_line) - len(c_line.lstrip())
                                        if is_test_code:
                                            commits_hunkTest_originalLines = commits_hunkTest_originalLines + c_line.replace(c_line[:leadingSpacesOri], "") + "\n"
                                        else:
                                            commits_hunk_originalLines = commits_hunk_originalLines + c_line.replace(c_line[:leadingSpacesOri], "") + "\n"

                                leadingSpacesBackport = 0
                                for c_lineB in commits_hunkline_backport_context:
                                    if c_lineB.startswith(("+")):
                                        c_lineB = c_lineB.replace("+", "")
                                        if leadingSpacesBackport == 0:
                                            leadingSpacesBackport = len(c_lineB) - len(c_lineB.lstrip())
                                        if is_test_codeB:
                                            commits_hunkTest_backportLines = commits_hunkTest_backportLines + c_lineB.replace(c_lineB[:leadingSpacesBackport], "") + "\n"
                                        else:
                                            commits_hunk_backportLines = commits_hunk_backportLines + c_lineB.replace(c_lineB[:leadingSpacesBackport], "") + "\n"


                                # If you need to know the current full file on the target stable version.  
                                # host = "https://github.com/"
                                # repo_url = host + repository.strip() + "/blob/" + targetStableBranch + "/"
                                # repo_url = host + repository.strip() 
                                # file_path = filepath.split(" ")[1] 
                                # fullFileTarget = repo.get_contents(file_path[2:], ref=targetStableBranch).decoded_content.decode("utf-8")

                                file_path = filepath.split(" ")[2]
                                for itemFcontent in original_filesContents:
                                    temp_itemFcontent = itemFcontent.copy()
                                    filepathFull, fullFilecontentOriginal = temp_itemFcontent.popitem()
                                if filepathFull == file_path[2:]:    
                                    fullFileTarget = fullFilecontentOriginal    
                                
                                if commits_hunkTest_originalLines:            
                                    testhunks_original.append(commits_hunkTest_originalLines) 

                                if commits_hunk_originalLines:    
                                    codehunks_original.append(commits_hunk_originalLines)
                                    codehunks_original_withContext.append(commits_diffs_original_contextHunks[indexHunks0])
                                    # codeFiles.append(None)

                                if commits_hunk_backportLines:    
                                    codehunks_backport.append(commits_hunk_backportLines)
                                    codehunks_backport_withContext.append(commits_diffs_backport_contextHunks[indexHunks0])
                                    # codeFiles.append(None)

                                numberofSlicingRequired = numberofSlicingRequired + 1

                    if testhunks_original and codehunks_original and codehunks_backport:
                        has_test_and_code = has_test_and_code + 1

                    slicebyCslicer = None
                    if codehunks_original and codehunks_backport:
                        context_index = 0 
                        for codeHunk, codeHunkBackport  in zip(codehunks_original, codehunks_backport):
                            output_parcent = int(difflib.SequenceMatcher(None, codeHunk, codeHunkBackport).ratio()*100)
                            diff_parcent = 100-output_parcent
                            if diff_parcent == 0:
                                continue
                            else:
                                numberofDifferences = numberofDifferences + 1

                            functionalSetforHunk = get_functional_set(codeHunk, testCases = testhunks_original)
                            astdiffshistory = get_ast_diffs(source_commits = pull_commitsSubmitted, startCommit=None, endCommit=None, startDate = commitStartDate, endDate = commitEndDate, repoName=repoName, projectName =projectName) 
                            # cslicer = Cslicer(sourceOriginal = codeHunk,
                            #                     sourcebackport = codeHunkBackport, 
                            #                     astdiffsHistory = astdiffshistory, 
                            #                     context = get_hunk_context(file_content = codehunks_original_withContext[context_index], hunk_start = hunkStartLnNo, hunk_end = hunkEndlnNo, context_lines=3), 
                            #                     dependencies = get_changeset_dependencies(codeHunk), 
                            #                     metadata = get_changesets_and_metadata(pull_request = pull_backport, sourceO = codeHunkBackport), 
                            #                     functionalSet = functionalSetforHunk, 
                            #                     compilationSet= get_compilation_set(sourceCode = codeHunk, functional_set = functionalSetforHunk), 
                            #                     stableLibraris = get_stable_version_libraries(owner = repoName, repo = projectName, branch = targetStableBranch, github_token=ghkey), 
                            #                     targetfile = fullFileTarget)
                            cslicer = BackSlicer(sourceOriginal = codeHunk,
                                                sourcebackport = codeHunkBackport, 
                                                astdiffsHistory = astdiffshistory, 
                                                context = get_hunk_context(file_content = codehunks_original_withContext[context_index], hunk_start = hunkStartLnNo, hunk_end = hunkEndlnNo, context_lines=3), 
                                                dependencies = get_changeset_dependencies(codeHunk), 
                                                metadata = get_changesets_and_metadata(pull_request = pull_backport, sourceO = codeHunkBackport), 
                                                functionalSet = functionalSetforHunk, 
                                                compilationSet= get_compilation_set(sourceCode = codeHunk, functional_set = functionalSetforHunk), 
                                                stableLibraris = get_stable_version_libraries(owner = repoName, repo = projectName, branch = targetStableBranch, github_token=ghkey), 
                                                targetfile = fullFileTarget)                        
                            context_index = context_index +1                    
                            slicebyCslicer, recommendation = cslicer.analyzeProgram()
                            recommendation = recommendation + "\n PRs: "+ pull_id_original  + ", "  + pull_id_backport
                            if slicebyCslicer:
                                numberOfSuccesfulSlicing = numberOfSuccesfulSlicing + 1                
                                slicesfromCSLICER.append((codeHunk ,slicebyCslicer, codeHunkBackport, recommendation))                                 

                    print("Working on pulls ", pull_id_original, pull_id_backport)
                    if slicesfromCSLICER:
                        slicedPRs.append(slicesfromCSLICER)

                except Exception as e:
                    print("Problem in pulls")
                    print(e)
                    continue
        

    with open(projectName+"InconICFDiffBackSliceSample", 'w') as f:   
        print("Total Labeled Backporting PRs", len(data_read), file=f)
        print("Total Sliced Required", numberofSlicingRequired, file=f)
        print("Total Number of Hunk Differences", numberofDifferences, file=f)
        print("Total Hunks Have Test and Code", has_test_and_code, file=f)
        print("Total Succesfully Sliced", numberOfSuccesfulSlicing, file=f)
        if slicedPRs:
            average_bleu_score, bleu_scores = calculate_average_bleu_score(slicedPRs)
            average_meteor_score, meteor_scores = calculate_average_meteor_score(slicedPRs)
            average_code_bleu, code_bleu_scores = calculate_average_code_bleu_score(slicedPRs)  
            average_rouge_l_score, rouge_l_scores = calculate_average_rouge_l(slicedPRs)  
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

    

# # Updated on 11th April 2023
ansibleDictOfActiveBranches = {'devel':{}, 'stable-2.9':{}, 'stable-2.12':{}, 'stable-2.14':{}, 'stable-2.13':{}, 'stable-2.15':{}}
# bitcoinDictOfActiveBranches = {'master':{}, '25.x':{}, '24.x':{}, '23.x':{}, '22.x':{}}
# ElasticsearchDictOfActiveBranches = {'main':{}, '8.8':{}, '7.17':{}, '8.7':{}, '8.5':{}, '8.6':{}, '8.0':{}, '8.1':{}, '8.2':{}, '8.3':{},'8.4':{}, '6.5':{}}
# JuliaDictOfActiveBranches = {'master':{}, 'release-1.9':{}, 'release-1.8':{}, 'release-1.6':{}}
# RailsDictOfActiveBranches = {'main':{}, '7-0-stable':{}, '6-1-stable':{}, '6-0-stable':{}}
# KibanaDictOfActiveBranches = {'main':{}, '8.8':{}, '8.7':{}, '8.6':{}, '8.5':{}, '8.4':{}, '7.17':{}, '8.2':{}, '8.3':{}}
# cpythonDictOfActiveBranches = {'main':{}, '3.12':{}, '3.11':{}, '3.10':{}, '3.9':{}, '3.8':{}}
ansibleDefault_branch = 'devel'
# bitcoinDefault_branch = 'master'
# ElasticsearchDefault_branch = 'main'
# JuliaDefault_branch = 'master'
# RailsDefault_branch = 'main'
# KibanaDefault_branch = 'main'
# cpythonDefault_branch = 'main'
mainCSLICER('data_cmp_incmpWithTest/Manual_incmp_Ansible_backport_keywordsPRsSample.csv', 
ansibleDefault_branch,
ansibleDictOfActiveBranches,
'ansible',
'ansible',
'data_cmp_incmpWithTest/Incmp_BackSliceSample_Ansible_backport_keywordsPRs.csv')