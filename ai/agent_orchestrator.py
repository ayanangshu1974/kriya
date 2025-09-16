import subprocess
import sys
import os

def run_requirement_agent(jira_issue_id):
    print("Running Requirement Agent...")
    result = subprocess.run(
        [sys.executable, "01_requirement_agent.py", jira_issue_id],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Requirement Agent failed:", result.stderr)
        sys.exit(1)
    print("Requirement Agent completed.")
    # BRD.pdf should be generated in current directory
    return "BRD.pdf"

def run_builder_agent():
    print("Running Builder Agent...")
    result = subprocess.run(
        [sys.executable, "02_builder_agent.py"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Builder Agent failed:", result.stderr)
        sys.exit(1)
    print("Builder Agent completed.")
    # Expects requirement.json and requirements_pkgs.json created
    return ("requirement.json", "requirements_pkgs.json")

def run_venv_creation(venv_name, venv_dir, req_json):
    print("Creating virtual environment and installing dependencies...")
    import importlib.util
    # Import your 03_venv_creation as module if structured so; else subprocess alternative
    from importlib import import_module
    venv_module = import_module("03_venv_creation")
    msg = venv_module.setup_virtualenv_and_install(venv_name, venv_dir, req_json)
    print(msg)

def run_coder_agent():
    print("Running Coder Agent...")
    result = subprocess.run(
        [sys.executable, "04_coder_agent.py"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Coder Agent failed:", result.stderr)
        sys.exit(1)
    print("Coder Agent completed.")
    # Generated project files expected now

def run_tester_agent():
    print("Running Tester Agent to generate tests...")
    result = subprocess.run(
        [sys.executable, "06_tester_agent.py"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Tester Agent failed:", result.stderr)
        sys.exit(1)
    print("Tester Agent completed.")
    # Tests should now be generated

def run_test_executor():
    print("Running Test Executor Agent...")
    result = subprocess.run(
        [sys.executable, "05_test_executor.py"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Test Executor failed:", result.stderr)
        sys.exit(1)
    print("Test Executor completed.")

def main():
    # Replace this with actual Jira Issue ID or CLI argument
    jira_issue_id = "Neev-307"

    brd_pdf = run_requirement_agent(jira_issue_id)
    requirement_json, requirements_pkgs_json = run_builder_agent()

    # Define virtualenv name and dir
    venv_name = "venv"
    venv_dir = os.getcwd()

    # Setup virtual env and install dependencies using the JSON generated
    run_venv_creation(venv_name, venv_dir, requirements_pkgs_json)

    run_coder_agent()
    run_tester_agent()
    run_test_executor()

    print("All agents ran successfully.")

if __name__ == "__main__":
    main()
