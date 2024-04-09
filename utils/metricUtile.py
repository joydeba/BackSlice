import csv
import subprocess
import nltk
# nltk.download('perluniprops')
# nltk.download('codebleu')
# nltk.download('perluniprops')
nltk.download('punkt')
nltk.download('wordnet')
from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge
import csv
import sacrebleu
from codebleu import calc_codebleu

def calculate_bleu_score(reference, candidate):
    reference_tokens = nltk.word_tokenize(reference)
    candidate_tokens = nltk.word_tokenize(candidate)
    bleu_score = sentence_bleu([reference_tokens], candidate_tokens, weights=(0.25, 0.25, 0.25, 0.25))
    return bleu_score

def calculate_average_bleu_score(paired_list):
    total_bleu_score = 0
    total_s_count = 0
    all_bleu_scores = []

    for pull_request in paired_list:
        references, candidates, targets, recommendation = zip(*pull_request)
        for reference, candidate, target in zip(references, candidates, targets):
            bleu_score = calculate_bleu_score(target, candidate)
            total_bleu_score += bleu_score
            total_s_count += 1
            all_bleu_scores.append(bleu_score)

    average_bleu_score = total_bleu_score / total_s_count
    return average_bleu_score, all_bleu_scores


# Function to calculate METEOR score using the METEOR jar file
def calculate_meteor_score(reference, candidate):

    reference_tokens = nltk.word_tokenize(reference)
    candidate_tokens = nltk.word_tokenize(candidate)

    reference_tokens = [token.lower() for token in reference_tokens]
    candidate_tokens = [token.lower() for token in candidate_tokens]

    meteor_score = nltk.translate.meteor_score.meteor_score([reference_tokens], candidate_tokens)
    return meteor_score
    

def calculate_average_meteor_score(paired_list):
    total_meteor_score = 0
    total_s_count = 0
    all_meteor_scores = []

    for pull_request in paired_list:
        references, candidates, targets, recommendation = zip(*pull_request)
        for reference, candidate, target in zip(references, candidates, targets):
            meteor_score = calculate_meteor_score(target, candidate)
            if meteor_score is not None:
                total_meteor_score += meteor_score
                total_s_count += 1
            all_meteor_scores.append(meteor_score)                

    average_meteor_score = total_meteor_score / total_s_count
    return average_meteor_score, all_meteor_scores


def calculate_code_bleu_score(reference, candidate):
    code_bleu_score = calc_codebleu([reference], [candidate], lang="python", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None)
    return code_bleu_score['codebleu']

def calculate_average_code_bleu_score(paired_list):
    total_code_bleu_score = 0
    total_s_count = 0
    all_code_bleu_scores = []

    for pull_request in paired_list:
        references, candidates, targets, recommendation = zip(*pull_request)
        for reference, candidate, target in zip(references, candidates, targets):
            code_bleu_score = calculate_code_bleu_score(target, candidate)
            total_code_bleu_score += code_bleu_score
            total_s_count += 1
            all_code_bleu_scores.append(code_bleu_score)            

    average_code_bleu_score = total_code_bleu_score / total_s_count
    return average_code_bleu_score, all_code_bleu_scores


# def calculate_rouge_l_score(reference, candidate):
#     rouge = Rouge()
#     scores = rouge.get_scores(candidate, reference, avg=True)
#     return scores['rouge-l']['f']

def calculate_rouge_l_score(reference, candidate):
    rouge = Rouge()
    scores = rouge.get_scores(candidate, reference)
    rouge_l_f_scores = [score['rouge-l']['f'] for score in scores]
    if rouge_l_f_scores == []:
        return 0
    else:
        avg_rouge_l_f_score = sum(rouge_l_f_scores) / len(rouge_l_f_scores)
        return avg_rouge_l_f_score

def calculate_average_rouge_l(paired_list):
    total_rouge_l_score = 0
    total_s_count = 0
    all_rouge_l_scores = []

    for pull_request in paired_list:
        references, candidates, targets, recommendation = zip(*pull_request)
        for reference, candidate, target in zip(references, candidates, targets):
            rouge_l_score = calculate_rouge_l_score(target, candidate)
            total_rouge_l_score += rouge_l_score
            total_s_count += 1
            all_rouge_l_scores.append(rouge_l_score)

    average_rouge_l_score = total_rouge_l_score / total_s_count
    return average_rouge_l_score, all_rouge_l_scores


def calculate_chrf_score(reference, candidate):
    chrf_score = sacrebleu.corpus_chrf([reference], [candidate])
    return chrf_score.score

def calculate_average_chrf_score(paired_list):
    total_chrf_score = 0
    total_s_count = 0
    all_chrf_scores = []

    for pull_request in paired_list:
        references, candidates, targets, recommendation = zip(*pull_request)
        for reference, candidate, target in zip(references, candidates, targets):
            chrf_score = calculate_chrf_score(target, candidate)
            total_chrf_score += chrf_score
            total_s_count += 1
            all_chrf_scores.append(chrf_score)

    average_chrf_score = total_chrf_score / total_s_count
    return average_chrf_score, all_chrf_scores