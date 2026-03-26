import os

def load_path(path, file_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    file_path = os.path.join(project_root, path, file_name)
    return file_path