import os

def print_tree(startpath, ignore_dirs={'.venv', '__pycache__', 'migrations','.idea', '.git', 'node_modules', 'js', 'css'}):
    for root, dirs, files in os.walk(startpath):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        level = root.replace(startpath, '').count(os.sep)
        indent = '    ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '    ' * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

if __name__ == "__main__":
    print_tree(".")
