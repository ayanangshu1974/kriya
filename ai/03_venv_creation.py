import json
import subprocess
import os
import sys

def parse_package_dependencies_from_file(json_file_path):
    with open(json_file_path, 'r') as f:
        parsed = json.load(f)
    packages = []
    if 'dependencies' in parsed:
        for pkg, ver in parsed['dependencies'].items():
            # Remove leading symbols like ^, ~, >=, etc.
            clean_version = ver.lstrip('^~<>=')
            packages.append(f"{pkg}=={clean_version}")
    else:
        raise ValueError("Expected 'dependencies' key in JSON")
    return packages

def setup_virtualenv_and_install(venv_name, venv_dir_path, json_req_file):
    venv_full_path = os.path.join(venv_dir_path, venv_name)
    packages = parse_package_dependencies_from_file(json_req_file)

    # Create virtual environment if not exist
    if not os.path.exists(venv_full_path):
        subprocess.run([sys.executable, '-m', 'venv', venv_full_path], check=True)

    # OS-dependent pip executable path
    if os.name == 'nt':  # Windows
        pip_executable = os.path.join(venv_full_path, 'Scripts', 'pip.exe')
    else:  # Linux / macOS
        pip_executable = os.path.join(venv_full_path, 'bin', 'pip')

    # Ensure pip is upgraded
    subprocess.run([pip_executable, 'install', '--upgrade', 'pip'], check=True)

    # Install packages
    for pkg in packages:
        subprocess.run([pip_executable, 'install', pkg], check=True)

    return f"Virtual environment '{venv_name}' created at '{venv_full_path}' with dependencies installed."

if __name__ == "__main__":
    # Example parameters, can be parameterized as needed
    result = setup_virtualenv_and_install('venvtest1', 'C:\\Users\\gangulay\\Documents\\GenAI', 'requirements_pkgs.json')
    print(result)
