import os
import importlib
import sys

def find_bad_imports(start_path):
    # Add the app directory to the python path
    sys.path.insert(0, os.path.abspath(os.path.join(start_path, '..')))

    for root, dirs, files in os.walk(start_path):
        # Skip alembic and venv
        if 'alembic' in dirs:
            dirs.remove('alembic')
        if 'venv' in dirs:
            dirs.remove('venv')

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                module_name = os.path.relpath(file_path, os.path.join(start_path, '..')).replace(os.path.sep, '.').replace('.py', '')
                
                # Skip the script itself and certain problematic modules
                if module_name == 'app.find_bad_imports' or 'main' in module_name or '__init__' in module_name:
                    continue

                print(f"Attempting to import {module_name}...")
                try:
                    importlib.import_module(module_name)
                    print(f"  SUCCESS: {module_name}")
                except Exception as e:
                    print(f"  !!!!!!!! FAILED to import {module_name} !!!!!!!!")
                    print(f"  ERROR: {e}")
                    print("-" * 20)

if __name__ == "__main__":
    find_bad_imports('backend/app') 