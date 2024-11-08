# VEEAM Test Task
# Made by Daniel Lages
# 
# Goal: Script that synchronizes two folders
#
# Objectives:
#   - One-way synchronization
#   - Synchronization performed perodically
#   - Log actions
#   - Ask user inputs
#
# TODO:
#   There is an error that happens when the code tries to get md5_hash of a non existing file in the source folder

import os
import shutil
import hashlib
from pathlib import Path

# Check if folders exist
def check_folders(source, replica, log):
    if not os.path.exists(source):
        print(f"Source folder '{source}' does not exist.")
        return False
    if not os.path.exists(replica):
        print(f"Replica folder '{replica}' does not exist.")
        return False
    if not os.path.exists(log):
        print(f"Log folder '{log}' does not exist.")
        return False
    return True

# Calculade MD5 hash
def md5_hash(path):
    hash = hashlib.md5()
    path = Path(path)

    # Handle file
    if path.is_file():
        hash.update(open(path, 'rb').read())
    # Handle folders
    elif path.is_dir():
        # Recursively go through the folder items
        for sub_path in path.iterdir():
            hash.update(sub_path.name.encode('utf-8'))  # include names
            if sub_path.is_file():
                hash.update(open(sub_path, 'rb').read())
            else:
                hash.update(sub_path.name.encode('utf-8'))
    else:
        raise ValueError(f"Unknown item in '{path}'")

    return hash.hexdigest()

# One-way synchronization
def sync_folders(source, replica):

    # Get all items in source folder
    items_src = []
    for dirpath, dirnames, filenames in os.walk(source):
        for folder in dirnames:
            items_src.append(os.path.join(dirpath, folder))
        for file in filenames:
            items_src.append(os.path.join(dirpath, file))
    
    # Compare items in both folders
    for item_src in items_src:
        item_rep = os.path.join(replica, os.path.relpath(item_src, source)) # corresponding path in the replica folder
    
        # Handle folders
        if os.path.isdir(item_src):
            if not os.path.exists(item_rep):
                os.makedirs(item_rep)
            # Check for modifications
            else:
                if md5_hash(item_src) != md5_hash(item_rep):
                    print(f"Updating folder '{item_rep}'")
                    os.utime(item_rep, (os.path.getatime(item_src), os.path.getmtime(item_rep)))    # update timestamp and name
        # Handle files
        else:
            if not os.path.exists(item_rep):
                print(f"Copying '{item_src}' to '{item_rep}'")  # log on console
                shutil.copy2(item_src, item_rep)
            else:
                # Check for modifications
                if md5_hash(item_src) != md5_hash(item_rep):
                    print(f"Updating file '{item_rep}'")
                    shutil.copy2(item_src, item_rep)

    # Deletes items in replica that are not in source
    delete_extra_items(source, replica)

def delete_extra_items(source, replica):
    for dirpath, dirnames, filenames in os.walk(replica):
        for file in filenames:
            file_rep = os.path.join(dirpath, file)
            file_src = os.path.join(source, os.path.relpath(file_rep, replica)) # corresponding path in the source folder
            if not os.path.exists(file_src):
                print(f"Deleting file '{file_rep}'")
                os.remove(file_rep)

        for folder in dirnames:
            folder_rep = os.path.join(dirpath, folder)
            folder_src = os.path.join(source, os.path.relpath(folder_rep, replica))
            if not os.path.exists(folder_src):
                print(f"Deleting folder '{folder_rep}'")
                os.rmdir(folder_rep)

def main():
    # Ask user inputs
    print("Folder Synchronization script")
    source_path = input("Enter source folder path:")
    replica_path = input("Enter replica folder path:")
    interval = input("Enter synchronization interval:")
    log_path = input("Enter log folder path:")
    
    if check_folders(source_path, replica_path, log_path):
        while True:
            sync_folders(source_path, replica_path)

if __name__ == "__main__":
    main()