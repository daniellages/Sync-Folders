# VEEAM Test Task
# Made by Daniel Lages
# 
# Goal: Script that synchronizes two folders
#
# Objectives:
#   - One-way synchronization
#   - Synchronization performed periodically
#   - Log actions
#   - Ask user inputs

import os
import shutil
import hashlib
import time
from pathlib import Path

# Check if folders exist
def check_paths(source, replica, log):
    if not os.path.exists(source):
        print(f"Source folder '{source}' does not exist.")
        return False
    if not os.path.exists(replica):
        print(f"Replica folder '{replica}' does not exist.")
        return False
    if not os.path.exists(log):
        print(f"Log file '{log}' does not exist.")
        return False
    if not os.path.splitext(log)[1].lower() == ".txt":
        print(f"Log file '{log}' is not a text file.")
        return False
    return True

# Logging messages to both file and console
def log_action(log_file, msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"'{timestamp}' {msg}"
    print(full_msg)     # log on console
    with open(log_file, 'a') as log:
        log.write(full_msg + '\n')  # log in file

# Calculade MD5 hash
def md5_hash(path):
    hash = hashlib.md5()
    path = Path(path)

    # Handle file
    if path.is_file():
        # If I don't use chunks it will raise a Permissions error
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash.update(chunk)
    # Handle folders
    elif path.is_dir():
        # Recursively go through the folder items
        for sub_path in path.iterdir():
            hash.update(sub_path.name.encode('utf-8'))  # include names
            if sub_path.is_file():
                with open(sub_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash.update(chunk)
            else:
                hash.update(md5_hash(sub_path).encode('utf-8'))

    return hash.hexdigest()

# One-way synchronization
def sync_folders(source, replica, log):

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
                    log_action(log, f"Updating folder '{item_rep}'")
                    shutil.rmtree(item_rep)                 # remove outdated folder
                    shutil.copytree(item_src, item_rep)     # copy folder
        # Handle files
        else:
            if not os.path.exists(item_rep):
                log_action(log, f"Copying '{item_src}' to '{item_rep}'")  # log on console
                shutil.copy2(item_src, item_rep)
            else:
                # Check for modifications
                if md5_hash(item_src) != md5_hash(item_rep):
                    log_action(log, f"Updating file '{item_rep}'")
                    shutil.copy2(item_src, item_rep)

    # Deletes items in replica that are not in source
    delete_extra_items(source, replica, log)

def delete_extra_items(source, replica, log):
    for dirpath, dirnames, filenames in os.walk(replica):
        for file in filenames:
            file_rep = os.path.join(dirpath, file)
            file_src = os.path.join(source, os.path.relpath(file_rep, replica)) # corresponding path in the source folder
            if not os.path.exists(file_src):
                log_action(log, f"Deleting file '{file_rep}'")
                os.remove(file_rep)

        for folder in dirnames:
            folder_rep = os.path.join(dirpath, folder)
            folder_src = os.path.join(source, os.path.relpath(folder_rep, replica))
            if not os.path.exists(folder_src):
                log_action(log, f"Deleting folder '{folder_rep}'")
                shutil.rmtree(folder_rep)

def main():
    # Ask user inputs
    print("Folder Synchronization script")
    source_path = input("Enter source folder path:")
    replica_path = input("Enter replica folder path:")
    interval = int(input("Enter synchronization interval (seconds):"))
    log_path = input("Enter log file path:")
    
    if check_paths(source_path, replica_path, log_path):
        while True:
            sync_folders(source_path, replica_path, log_path)
            print(f"Folders synchronized! Waiting '{interval}' seconds for next iteration...")
            time.sleep(interval)    # Synchronized periodically

if __name__ == "__main__":
    main()