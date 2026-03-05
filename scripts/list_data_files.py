#!/usr/bin/env python3

import glob
import shutil
import os
from pprint import pprint

import re

def list_data_files(notebooks_directory, data_directory):
    # Make a list of all of the .csv files under data directory
    csv_files = glob.glob(os.path.join(data_directory, "**", "*.csv"), recursive=True)
    csv_files = [csv_file.replace(f"{data_directory}/","") for csv_file in csv_files]
    #pprint(csv_files)

    # Make a list of all *.ipynb files under notebooks_directory
    ipynb_files = glob.glob(os.path.join(notebooks_directory, "**", "*.ipynb"), recursive=True)
    #pprint(ipynb_files)
    
    # For each notebook file in ipynb_files, 
    # Check to see whether it contains the string path_data
    
    notebooks_with_data = {}
    
    for notebook in ipynb_files:
        with open(notebook, "r") as f:
            contents = f.read()
            if "path_data" in contents:
                notebooks_with_data[notebook.replace(f"{notebooks_directory}/","")] = contents

    occurences={}
    for notebook, contents in notebooks_with_data.items():
        # Search for all occurences of path_data in contents
        # Don't just get a count; get the actual lines that contain path_data
        count = contents.count("path_data")
        if count > 0:
            occurences[notebook] = []
            for line in contents.splitlines():
                if "path_data" in line:
                    occurences[notebook].append(line)

    #pprint(occurences)

    csvs = {}

    for key, data in occurences.items():
        for line in data:
            for csv_file in csv_files:
               
                if csv_file in line:
                    if key in csvs:
                        csvs[key].append(csv_file)
                    else:
                        csvs[key] = [csv_file]

    pprint(csvs)



if __name__ == "__main__":
    csvs = list_data_files("notebooks", "assets/data")
    pprint(csvs)