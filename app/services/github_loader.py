import os
from git import Repo

BASE_DIR = "repos"

def clone_repo(repo_url: str):
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(BASE_DIR, repo_name)

    # Avoid re-cloning
    if os.path.exists(repo_path):
        return repo_path

    Repo.clone_from(repo_url, repo_path)
    return repo_path