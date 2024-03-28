import csv
import re
import difflib
import sys
csv.field_size_limit(sys.maxsize)
import os
import sys
sys.path.insert(1, os.getcwd())
from helperZER.pygithub_helper import *
import ast
import git
import subprocess
PIPE = subprocess.PIPE
import git
from utils.slicerUtile import *

def checking_compatibility_and_incompability_withTests_among_PRs(prlist = 'prlist.csv', output1='incmp.csv', output2='cmp.csv', output3='manual.csv'):
    g, backup_keys, no_bused_key, accesskey = initialize_G()
    no_of_compatiblewithTest = 0
    compatible_listwithTest = []
    no_of_incompatiblewithTest = 0
    incompatible_listwithTest = []
    no_of_referenced_found = 1
    chnaged_parcent = 0
    manual_listwithTest = []
    has_test_code  = False     

    with open(prlist,"r") as fp:
        reader = csv.reader(fp, delimiter=",", quotechar='"', dialect=csv.excel_tab)
        data_read = [row for row in reader]
        load_object = 0

        for idx, line in enumerate(data_read):
            has_test_code  = False
            backport_code = ""               
            main_code = "" 
            new_line = [] 
            diff_parcent = 0
            try:
                repository = line[0].replace('https://api.github.com/repos/', '')
                user_name, repo_name = repository.split("/")
                repo = g.get_repo(repository)
                print("Working on repo", repo_name)            

                g, no_bused_key, load_object = changeG(g, accesskey, backup_keys, no_bused_key, load_object)        
            
                if load_object:
                    repo = g.get_repo(repository)
                    print("New G loaded")
                    load_object = 0

                pull_id = line[1]
                head, base = line[2].split("::")
                head = head.lower()
                base = base.lower()

                if base == 'master' or base == 'main' or base == 'devel' or base == '2.4-develop' or base == '5.x':
                    continue
                pull = repo.get_pull(int(pull_id))
                new_line.append(pull.html_url+"/files")
                for bfile in pull.get_files():
                    if bfile.patch is not None:
                        backport_code = backport_code + bfile.patch 
            
                pr_body = pull.body
                reference_pattern = r'#[\d]+'
                references = []
                if pr_body:
                    references = re.findall(reference_pattern, pr_body)
                if references:
                    main_pull_id = references[0].replace("#", "")
                    main_pull = repo.get_pull(int(main_pull_id))
                    new_line.append(" "+main_pull.html_url+"/files")
                    for cfile in main_pull.get_files(): 
                        if cfile.patch is not None: 
                            main_code = main_code + cfile.patch

                pull_request_files = [f.filename for f in pull.get_files()]

                if has_test_files(pull_request_files):
                    print("Pull request contains test files.")
                    has_test_code = True
                else:
                    print("Pull request does not contain test files.")
                    continue

            except Exception as e:
                print("Problem in pulls")
                print(e)
                continue  

            if backport_code != "" and main_code != "" and has_test_code:      
                no_of_referenced_found = no_of_referenced_found + 1
                output_parcent = int(difflib.SequenceMatcher(None, main_code, backport_code).ratio()*100)
                diff_parcent = 100-output_parcent
                chnaged_parcent = chnaged_parcent + diff_parcent
                new_line.append(" "+str(diff_parcent))
                new_line.append(" "+str(base))
                manual_listwithTest.append(new_line) 

                if diff_parcent > 0:
                    no_of_incompatiblewithTest = no_of_incompatiblewithTest + 1
                    incompatible_listwithTest.append(line)
                else:
                    no_of_compatiblewithTest = no_of_compatiblewithTest + 1
                    compatible_listwithTest.append(line)

                           
    # with open(output1, "w") as fp:
    #     writer = csv.writer(fp, delimiter=",")
    #     writer.writerows(incompatible_listwithTest)

    # with open(output2, "w") as fp:
    #     writer = csv.writer(fp, delimiter=",")
    #     writer.writerows(compatible_listwithTest)    

    with open(output3, "w") as fp:
        writer = csv.writer(fp, delimiter=",")
        writer.writerows(manual_listwithTest)


                                
    print("Total Labeled Backporting PRs", len(data_read))
    print("No_of_referenced_found:", no_of_referenced_found)
    print("No_of_compatible:", no_of_compatiblewithTest)
    print("No_of_incompatible:", no_of_incompatiblewithTest)
    print("Avearge chnaged_parcent:", chnaged_parcent/no_of_referenced_found)


checking_compatibility_and_incompability_withTests_among_PRs('projectWise_data_from_github/Cmssw_backport_keywordsPRs.csv', 
'data_cmp_incmpWithTest/Incmp_Cmssw_backport_keywordsPRs.csv', 
'data_cmp_incmpWithTest/Cmp_Cmssw_backport_keywordsPRs.csv',
'data_cmp_incmpWithTest/Manual_incmp_Cmssw_backport_keywordsPRs.csv')