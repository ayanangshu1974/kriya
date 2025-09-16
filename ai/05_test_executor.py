import os
import sys
import subprocess
import json
import importlib.util

from llama_index.core import Document, VectorStoreIndex
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def ensure_package(package_name):
    """Check if a Python package is installed, if not install it."""
    if importlib.util.find_spec(package_name) is None:
        print(f"[INFO] {package_name} not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
    else:
        print(f"[INFO] {package_name} is already installed.")


def run_pytest(test_dir="project/tests", results_file="report.json"):
    """Run pytest with JSON reporting enabled and return parsed report."""
    ensure_package("pytest")
    ensure_package("pytest_json_report")

    results_file = os.path.abspath(results_file)

    # Ensure project root is on PYTHONPATH
    project_root = os.path.abspath("project")
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    print(f"[INFO] Running pytest in {test_dir} with PYTHONPATH={env['PYTHONPATH']}...")

    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            test_dir,
            "--json-report",
            f"--json-report-file={results_file}"
        ],
        capture_output=True,
        text=True,
        env=env,   # <-- inject modified PYTHONPATH
    )

    print("========== PYTEST OUTPUT ==========")
    print(result.stdout)
    print("========== PYTEST ERRORS ==========")
    print(result.stderr)
    print("==================================")

    if not os.path.exists(results_file):
        raise FileNotFoundError("No pytest JSON report found. Ensure tests exist and plugin works.")

    with open(results_file, "r", encoding="utf-8") as f:
        return json.load(f)


    print("========== PYTEST OUTPUT ==========")
    print(result.stdout)
    print("========== PYTEST ERRORS ==========")
    print(result.stderr)
    print("==================================")

    if not os.path.exists(results_file):
        raise FileNotFoundError("No pytest JSON report found. Ensure tests exist and plugin works.")

    with open(results_file, "r", encoding="utf-8") as f:
        return json.load(f)


def summarize_report(report):
    """Summarize pytest JSON report (structured)."""
    summary = {
        "total_tests": report.get("summary", {}).get("total", 0),
        "passed": report.get("summary", {}).get("passed", 0),
        "failed": report.get("summary", {}).get("failed", 0),
        "skipped": report.get("summary", {}).get("skipped", 0),
        "errors": report.get("summary", {}).get("error", 0),
    }
    return summary


def generate_llm_summary(report):
    """Use LlamaIndex + LLM to generate a natural language summary of test execution."""
    # Convert report into a readable text
    report_text = json.dumps(report, indent=4)

    # Wrap it in a LlamaIndex Document
    doc = Document(text=report_text)

    # Build a mini index
    index = VectorStoreIndex.from_documents([doc])

    # Set up LLM (replace with your model)
    llm = OpenAI(model="gpt-4o-mini")  # or "gpt-4o", "gpt-3.5-turbo"

    query_engine = index.as_query_engine(llm=llm)

    # Ask the LLM to summarize test execution
    response = query_engine.query(
        "Summarize this pytest report. Highlight how many tests passed, failed, skipped, "
        "and describe main failures in simple language."
    )

    return str(response)


if __name__ == "__main__":
    try:
        report = run_pytest()
        summary = summarize_report(report)
        print("\n===== STRUCTURED SUMMARY =====")
        print(json.dumps(summary, indent=4))

        print("\n===== LLM SUMMARY =====")
        llm_summary = generate_llm_summary(report)
        print(llm_summary)

    except Exception as e:
        print(f"[ERROR] {e}")
