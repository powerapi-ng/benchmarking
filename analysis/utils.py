import os
import re


def find_files(root_dir="", regex=""):
    found_files = []
    regex = re.compile(regex)
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if regex.match(file):
                found_files.append(os.path.join(root, file))

    return found_files
