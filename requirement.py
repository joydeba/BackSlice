# BackSlice (BackportSlicer) - Provide semantic slices by analyzing changesets in backporting.

# Installation Instructions
# 1. Clone the repository
# git clone https://joydeba@github.com/joydeba/BackSlice.git
#     - if password is not working, use PAT

# 2. Create a virtual environment
# python3 -m venv venvBackSlice

# 3. Activate the virtual environment
# source venvBackSlice/bin/activate  # Linux/Mac
# venvBackSlice\Scripts\activate  # Windows

import os
import platform

# Install necessary packages
os.system('pip install PyGithub')  # Checked
os.system('pip install pytz')  # Checked
os.system('pip install GitPython')  # Checked
os.system('pip install astunparse')  # Checked
os.system('pip install nvdlib')  # Optional
os.system('pip install Levenshtein')  # Checked
os.system('pip install safety')  # Checked
os.system('pip install pyre-check')  # Optional
os.system('pip install bandit')  # Optional
os.system('pip install nltk')
os.system('pip install sacrebleu')
os.system('pip install py-rouge')
os.system('pip install codebleu')
os.system('pip install scikit-learn')
os.system('pip install mypy')

# Initialize pyre if installed
os.system('pyre init')

# Detect OS and provide specific instructions
if platform.system() == 'Darwin':  # Mac OS
    os.system('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
    os.system('(echo; echo \'eval "$(/opt/homebrew/bin/brew shellenv)"\') >> ~/.zprofile')
    os.system('eval "$(/opt/homebrew/bin/brew shellenv)"')
    os.system('brew install bandit')
    os.system('brew install gh')

    # Instructions for setting OPENAI_API_KEY for zsh
    zshrc_instructions = '''
    # Add the following lines to ~/.zshrc
    export OPENAI_API_KEY='your-api-key-here'
    source ~/.zshrc
    echo $OPENAI_API_KEY
    '''
    print(zshrc_instructions)

elif platform.system() == 'Linux':  # Ubuntu
    os.system('sudo apt update')
    os.system('sudo apt install gh')  # Install GitHub CLI

    # Instructions for setting OPENAI_API_KEY for bash
    bashrc_instructions = '''
    # Add the following lines to ~/.bashrc
    export OPENAI_API_KEY='your-api-key-here'
    source ~/.bashrc
    echo $OPENAI_API_KEY
    '''
    print(bashrc_instructions)

# For BackTrans
os.system('pip install --upgrade openai')
os.system('pip install tiktoken')

# Display additional instructions
additional_instructions = '''
# Optional: Update config keys, install git with brew, clone subject repositories
# To set the OPENAI_API_KEY environment variable:
# Mac (zsh): Add export OPENAI_API_KEY='your-api-key-here' to ~/.zshrc and run source ~/.zshrc
# Ubuntu (bash): Add export OPENAI_API_KEY='your-api-key-here' to ~/.bashrc and run source ~/.bashrc
'''

print(additional_instructions)
