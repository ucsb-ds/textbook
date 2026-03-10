# ucsb-ds/textbook

Fork of data-8/textbook for UCSB

This fork exists only to be able to set up Google Colab version of the 
Jupyter Notebooks in the data-8/textbook repo.

This involves the following elements:

1. Additional scripts
2. Additional items in the .gitignore
3. This README_UCSB.md

# Getting Started

## Set up Python venv

```
python3 -m venv venv
source ./venv/bin/activate
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib pandas requests google-auth  
pip install "urllib3<2"    
pip install "requests<2.31"
```