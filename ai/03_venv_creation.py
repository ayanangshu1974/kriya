import json
import subprocess
import os
import sys
import json



def parse_package_dependencies_from_file(json_file_path):
    with open(json_file_path, 'r') as f:
        parsed = json.load(f)

    packages = []
    if 'dependencies' in parsed:
        for pkg, ver in parsed['dependencies'].items():
            # Strip leading ^ or ~ or other characters from version if any
            clean_version = ver.lstrip('^~<>=')
            packages.append(f"{pkg}=={clean_version}")
    else:
        raise ValueError("Expected 'dependencies' key in JSON")

    return packages




def setup_virtualenv_and_install(venv_name, venv_dir_path, json_req_file):
    # Full path for the virtual environment
    venv_full_path = os.path.join(venv_dir_path, venv_name)

    requirements_list = parse_package_dependencies_from_file(json_req_file)

    # Build lines for the proper pip requirements file
    requirements_lines = []
    if all(isinstance(item, dict) for item in requirements_list):
        for pkg in requirements_list:
            if 'name' in pkg and 'version' in pkg:
                requirements_lines.append(f"{pkg['name']}=={pkg['version']}")
            elif 'name' in pkg:
                requirements_lines.append(pkg['name'])
    elif all(isinstance(item, str) for item in requirements_list):
        requirements_lines = requirements_list
    else:
        return "Unexpected JSON format for requirements"

    # Write the properly formatted requirements to a temp file
    clean_req_file = 'requirements_clean.txt'
    with open(clean_req_file, 'w') as f:
        f.write('\n'.join(requirements_lines))

    # Create virtual environment if it does not exist
    if not os.path.exists(venv_full_path):
        subprocess.run([sys.executable, '-m', 'venv', venv_full_path], check=True)

    # Determine pip executable within the virtualenv
    if os.name == 'nt':
        pip_exec = os.path.join(venv_full_path, 'Scripts', 'pip')
    else:
        pip_exec = os.path.join(venv_full_path, 'bin', 'pip')

    # Install dependencies from the cleaned requirements file
    subprocess.run([pip_exec, 'install', '-r', clean_req_file], check=True)

    return f"Virtual environment '{venv_name}' created at '{venv_full_path}' and dependencies installed."




if __name__ == "__main__":
    result=setup_virtualenv_and_install('venvtest1', 'C:\\Users\\gangulay\\Documents\\GenAI', 'requirements_pkgs.json')
    print(result)