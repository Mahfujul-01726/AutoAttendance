import os
from huggingface_hub import HfApi, create_repo

import sys
token = sys.argv[1]
api = HfApi(token=token)

try:
    username = api.whoami()["name"]
    repo_id = f"{username}/AutoAttendance"
    print(f"Creating repo: {repo_id}")
    
    create_repo(repo_id=repo_id, repo_type="space", space_sdk="docker", exist_ok=True, token=token)
    
    print("Uploading folder...")
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        ignore_patterns=[".git", ".github", "__pycache__", "ProjectReport", "*.mp4", "*.ipynb", "logs/*"],
        token=token
    )
    print(f"Successfully deployed! View it at: https://huggingface.co/spaces/{repo_id}")
except Exception as e:
    print(f"Error deploying: {e}")
