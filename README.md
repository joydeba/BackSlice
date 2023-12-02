# ProSlice
ProSlice (PropagationSlicer) - Provide semantic slices by analyzing changesets in backporting.

# Installation
- git clone https://joydeba@github.com/joydeba/ProSlice.git
    - if password is not working, use PAT
- python3 -m venv . venvProSlice
- source bin/activate [locations]
 

# Required packages
- pip/pip3 install PyGithub [Checked]
- pip3 install pytz [Checked]
- pip/pip3 install GitPython [Checked]
- pip3 install astunparse [Checked]
- pip3 install nvdlib [Optional]
- pip install Levenshtein [Checked]
- pip install safety [Checked]
- pip install pyre-check [optional]
- pyre init
- pip install bandit [Optional]

- /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" 
- (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> /Users/joydeba/.zprofile
- eval "$(/opt/homebrew/bin/brew shellenv)"   
- brew install gh

- [Optinal] Update config keys, install git with brew, clone subject repositories
