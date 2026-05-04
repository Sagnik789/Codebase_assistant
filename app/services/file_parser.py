import os

SUPPORTED_EXTENSIONS = [".py", ".js", ".ts", ".java", ".cpp"]

def get_code_files(repo_path: str):
    code_files = []

    for root, _, files in os.walk(repo_path):
        for file in files:
            if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                full_path = os.path.join(root, file)
                code_files.append(full_path)

    return code_files

def read_file(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None