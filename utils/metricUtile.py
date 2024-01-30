import csv
import subprocess
import nltk
# nltk.download('perluniprops')
# nltk.download('codebleu')
# nltk.download('perluniprops')
nltk.download('punkt')
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

    for pull_request in paired_list:
        references, candidates, targets, recommendation = zip(*pull_request)
        for reference, candidate, target in zip(references, candidates, targets):
            total_bleu_score += calculate_bleu_score(target, candidate)

    average_bleu_score = total_bleu_score / len(paired_list)
    return average_bleu_score


# Function to calculate METEOR score using the METEOR jar file
def calculate_meteor_score(reference, candidate):
    meteor_jar = 'utils/meteor-1.5.jar'  # Replace with the actual path to meteor-1.5.jar

    # Tokenize the reference and candidate strings
    reference_tokens = nltk.word_tokenize(reference)
    candidate_tokens = nltk.word_tokenize(candidate)

    # Convert tokens to lowercase (METEOR is case-sensitive)
    reference_tokens = [token.lower() for token in reference_tokens]
    candidate_tokens = [token.lower() for token in candidate_tokens]

    # Call METEOR using subprocess
    command = ['java', '-Xmx2G', '-jar', meteor_jar, candidate, reference, '-l', 'en', '-norm']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if process.returncode == 0:
        meteor_score = float(output.strip())
        return meteor_score
    else:
        print(f"Error calculating METEOR score: {error}")
        return None
    

def calculate_average_meteor_score(paired_list):
    total_meteor_score = 0

    for pull_request in paired_list:
        references, candidates, targets, recommendation = zip(*pull_request)
        for reference, candidate, target in zip(references, candidates, targets):
            meteor_score = calculate_meteor_score(target, candidate)
            if meteor_score is not None:
                total_meteor_score += meteor_score

    average_meteor_score = total_meteor_score / len(paired_list)
    return average_meteor_score


def calculate_code_bleu_score(reference, candidate):
    code_bleu_score = calc_codebleu([reference], [candidate], lang="python", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None)
    return code_bleu_score['codebleu']

def calculate_average_code_bleu_score(paired_list):
    total_code_bleu_score = 0

    for pull_request in paired_list:
        references, candidates, targets, recommendation = zip(*pull_request)
        for reference, candidate, target in zip(references, candidates, targets):
            code_bleu_score = calculate_code_bleu_score(target, candidate)
            total_code_bleu_score += code_bleu_score

    average_code_bleu_score = total_code_bleu_score / len(paired_list)
    return average_code_bleu_score


def calculate_rouge_l_score(reference, candidate):
    rouge = Rouge()
    scores = rouge.get_scores(candidate, reference)
    rouge_l_score = scores[0]['rouge-l']['f']
    return rouge_l_score

def calculate_average_rouge_l(paired_list):
    total_rouge_l_score = 0

    for pull_request in paired_list:
        references, candidates, targets, recommendation = zip(*pull_request)
        for reference, candidate, target in zip(references, candidates, targets):
            rouge_l_score = calculate_rouge_l_score(target, candidate)
            total_rouge_l_score += rouge_l_score

    average_rouge_l_score = total_rouge_l_score / len(paired_list)
    return average_rouge_l_score


def calculate_chrf_score(reference, candidate):
    chrf_score = sacrebleu.corpus_chrf([reference], [candidate])
    return chrf_score.score

def calculate_average_chrf_score(paired_list):
    total_chrf_score = 0

    for pull_request in paired_list:
        references, candidates, targets, recommendation = zip(*pull_request)
        for reference, candidate, target in zip(references, candidates, targets):
            chrf_score = calculate_chrf_score(target, candidate)
            total_chrf_score += chrf_score

    average_chrf_score = total_chrf_score / len(paired_list)
    return average_chrf_score