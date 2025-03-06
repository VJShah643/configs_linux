import os
import shutil
import subprocess
from datetime import datetime

# Configuration
MACHINE_NAME = os.uname().nodename
BACKUP_REPO_PATH = os.getenv('BACKUP_REPO_PATH') #"/path/to/your/backup/repo"  # Replace with your backup repo path
GIT_REPO_URL = "git@github.com:VJShah643/configs_linux.git"  # Change this to your repo URL
MACHINE_DIR = os.path.join(BACKUP_REPO_PATH, MACHINE_NAME)

# Ensure machine-specific directory exists
#os.makedirs(MACHINE_DIR, exist_ok=True)

# Use the config file from the environment variable or default to MACHINE_DIR/.config/scripts/BACKUP_CONFIGS_LIST
BACKUP_CONFIGS_LIST = os.getenv('BACKUP_CONFIGS_LIST', os.path.join(MACHINE_DIR, '.config', 'scripts', 'BACKUP_CONFIGS_LIST'))

# Check if config file exists
if not os.path.isfile(BACKUP_CONFIGS_LIST):
    print(f"Error: {BACKUP_CONFIGS_LIST} not found!")
    exit(1)

# Clone the repo if it doesn't exist
if not os.path.isdir(os.path.join(BACKUP_REPO_PATH, ".git")):
    print("Cloning backup repository...")
    subprocess.run(["git", "clone", GIT_REPO_URL, BACKUP_REPO_PATH])
else:
    print("Updating repository...")
    subprocess.run(["git", "-C", BACKUP_REPO_PATH, "pull", "origin", "main"])

# Read each line from the config file
with open(BACKUP_CONFIGS_LIST, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        # Expand $USER in paths
        expanded_line = line.replace("$USER", os.getenv('USER'))
        
        # Extract source and optional destination
        parts = expanded_line.split()
        source = parts[0]
        custom_dest = parts[1] if len(parts) > 1 else None
        
        # Determine destination
        if custom_dest:
            destination = os.path.join(MACHINE_DIR, custom_dest)
        else:
            #if source.startswith(f"/home/{os.getenv('USER')}"):
            #    rel_path = source[len(f"/home/{os.getenv('USER')}"):]  # Remove leading '/home/$USER'
            #    destination = os.path.join(MACHINE_DIR, ".config", rel_path)
            #else:
            rel_path = source.lstrip("/")  # Remove leading '/'
            destination = os.path.join(MACHINE_DIR, rel_path)

        # Check if source exists
        if os.path.exists(source):
            # Make sure destination directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)

            # Copy files, excluding .git directories
            if os.path.isdir(source):
                for dirpath, dirnames, filenames in os.walk(source):
                    # Exclude .git directories
                    dirnames[:] = [d for d in dirnames if d != ".git"]

                    # Copy files to the destination
                    for filename in filenames:
                        src_file = os.path.join(dirpath, filename)
                        dest_file = os.path.join(destination, os.path.relpath(src_file, start=source))
                        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                        shutil.copy2(src_file, dest_file)
                        print(f"Copied {src_file} → {dest_file}")
            else:
                shutil.copy2(source, destination)
                print(f"Copied {source} → {destination}")
        else:
            print(f"Warning: Source file {source} not found!")

# Commit and push changes if any
subprocess.run(["git", "-C", BACKUP_REPO_PATH, "add", "."])

# Check for changes
status = subprocess.run(["git", "-C", BACKUP_REPO_PATH, "status", "--porcelain"], capture_output=True, text=True)
if status.stdout:
    commit_message = f"Backup for {MACHINE_NAME}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    subprocess.run(["git", "-C", BACKUP_REPO_PATH, "commit", "-m", commit_message])
    subprocess.run(["git", "-C", BACKUP_REPO_PATH, "push", "origin", "main"])
    print("Backup successfully committed and pushed to GitHub!")
else:
    print("No changes to commit. Backup is up to date.")

