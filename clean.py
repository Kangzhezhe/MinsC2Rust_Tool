import os
import shutil

def clean_dir_contents(dir_path):
    for item in os.listdir(dir_path):
        if item == "compile_commands.json":
            continue  # 跳过该文件
        item_path = os.path.join(dir_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path, ignore_errors=True)
        else:
            os.remove(item_path)

def clean_build_artifacts(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for dirname in dirnames:
            if dirname in ('build', 'target'):
                full_path = os.path.join(dirpath, dirname)
                print(f"Cleaning contents of: {full_path}")
                clean_dir_contents(full_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python clean.py <root_directory>")
    else:
        clean_build_artifacts(sys.argv[1])