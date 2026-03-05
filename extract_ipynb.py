#!/usr/bin/env python3

import glob
import shutil
import os
from pprint import pprint

def extract_ipynb_files(source, destination):
    # Your implementation here
    
    # First, make a list of the full path of all files
    # under the source directory that match the pattern "*.ipynb"
    
    ipynb_files = glob.glob(os.path.join(source, "**", "*.ipynb"), recursive=True)

    pprint(ipynb_files)

    # Remove any files from the ipynb_files list that are under the
    # destination directory
    
    ipynb_files = [ipynb_file for ipynb_file in ipynb_files if not ipynb_file.startswith(destination)]

    # Now create a dictionary where the keys are the paths of the existing files
    # in ipynb_files, the keys are a new filename where the "/" have been replaced
    # with underscores

    ipynb_file_mapping = {ipynb_file: ipynb_file.replace(f"{source}/","").replace("/", "_") for ipynb_file in ipynb_files}

    # Create the destination directory if it doesn't exist
    os.makedirs(destination, exist_ok=True)

    # Now, copy each of these files to the destination directory
    # with the new filename
    
    for ipynb_file in ipynb_files:
        new_filename = ipynb_file_mapping[ipynb_file]
        new_filepath = os.path.join(destination, new_filename)
        shutil.copy(ipynb_file, new_filepath)


if __name__ == "__main__":
    extract_ipynb_files("chapters", "notebooks")