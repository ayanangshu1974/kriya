import json
import os
import re
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()

def save_multi_file_code(output_text, base_dir=None):
    """
    Parses multi-file code from LLM output and saves into proper directory structure.
    If the first folder in LLM output is detected, uses that as the base_dir.
    """
    # Detect first top-level folder from LLM output (like "my-web-app/")
    folder_match = re.search(r'^([\w\-_]+/)', output_text, re.MULTILINE)
    if folder_match:
        auto_base_dir = folder_match.group(1).rstrip("/")  # remove trailing /
        base_dir = base_dir or auto_base_dir
    else:
        base_dir = base_dir or "generated_project"

    os.makedirs(base_dir, exist_ok=True)

    # Regex: ```lang optional_path ... code ```
    pattern = r"```(?:\w+)?\s*([\w\-/\.]+)?\n(.*?)```"
    matches = re.findall(pattern, output_text, re.DOTALL)

    if not matches:
        # fallback: save everything to single file
        single_file = os.path.join(base_dir, "generated_code.txt")
        with open(single_file, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f" No structured matches found. Saved everything to {single_file}")
        return

    for file_path, code in matches:
        if not file_path:
            continue

        # Skip directory-only paths
        if file_path.endswith("/") or file_path.endswith("\\"):
            print(f" Skipping directory path: {file_path}")
            continue

        full_path = os.path.join(base_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code.strip())
        print(f" Wrote {full_path}")


def generate_code(requirement_file: str, base_dir: str = None):
    """
    Reads requirements JSON and generates multi-file project using LlamaIndex LLM.
    """

    if not os.path.exists(requirement_file):
        raise FileNotFoundError(f"Requirement file not found: {requirement_file}")

    with open(requirement_file, "r", encoding="utf-8") as f:
        requirements = json.load(f)

    language = requirements.get("language", "python")
    framework = requirements.get("framework", "flask")

    api_key = os.getenv("OPENAI_API_KEY")
    llm = OpenAI(model="gpt-4o-mini", api_key=api_key)

    prompt = f"""
    You are a senior full-stack developer agent.

    Based on the requirements below, generate a COMPLETE project codebase.
    Requirements:
    {json.dumps(requirements, indent=2)}

    Rules:
    - Use {language} with {framework}.
    - Provide a realistic project structure with multiple files (backend + frontend if needed).
    - Wrap code in markdown code blocks with the exact file path after the language, e.g.:
      ```javascript backend/server.js
      // code here
      ```
    - Do not provide extra explanations outside code blocks.
    """

    response = llm.complete(prompt)

    # Save output into multi-file structure
    save_multi_file_code(response.text, base_dir=base_dir)
    print(f"\n Project generated inside: {base_dir or 'auto-detected root folder'}")


if __name__ == "__main__":
    # Reads the requirement.json created by builder_agent.py
    generate_code("requirement.json")
