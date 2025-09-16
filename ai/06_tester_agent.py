import os
import json
import re
from pathlib import Path
import sys
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.llms.openai import OpenAI

load_dotenv()  # Load environment variables from .env file


class TesterAgent:
    def __init__(self, project_dir: str, tests_dir: str, requirements_file: str = None):
        self.test_dir = tests_dir
        self.report_file = "test_report.json"

        # --- Fix sys.path so backend imports work ---
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        PROJECT_DIR = os.path.join(BASE_DIR, "project")
        if PROJECT_DIR not in sys.path:
            sys.path.insert(0, PROJECT_DIR)
        #############################################
        self.project_dir = Path(project_dir).resolve()
        self.tests_dir = Path(tests_dir).resolve()

        # Auto-find requirement.json if not provided
        if requirements_file:
            self.requirements_file = Path(requirements_file).resolve()
        else:
            local_req = self.project_dir / "requirement.json"
            base_req = Path("requirement.json")
            if local_req.is_file():
                self.requirements_file = local_req
            elif base_req.is_file():
                self.requirements_file = base_req
            else:
                raise FileNotFoundError(
                    "requirement.json not found in project folder or base folder!"
                )

        self.requirements = self.load_requirements()

    def load_requirements(self):
        with open(self.requirements_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def ensure_backend_files(self):
        """
        Ensure backend/__init__.py, app.py, models.py exist.
        """
        backend_path = self.project_dir / "backend"
        backend_path.mkdir(exist_ok=True)

        # __init__.py
        init_file = backend_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created {init_file}")

        # app.py
        app_file = backend_path / "app.py"
        if not app_file.exists():
            app_file.write_text(
                """from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, World!"
""",
                encoding="utf-8"
            )
            print(f"Created {app_file}")

        # models.py
        models_file = backend_path / "models.py"
        if not models_file.exists():
            models_file.write_text(
                """class ExampleModel:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}!"
""",
                encoding="utf-8"
            )
            print(f"Created {models_file}")

    def build_index(self):
        docs = SimpleDirectoryReader(self.project_dir, recursive=True).load_data()
        return VectorStoreIndex.from_documents(docs)

    def generate_tests(self, index, language="python", framework="flask"):
        llm = OpenAI(model="gpt-4o-mini")
        query_engine = index.as_query_engine(llm=llm)

        test_prompt = f"""
        You are an expert QA engineer. Generate automated test cases for the project.

        Requirements:
        {json.dumps(self.requirements, indent=2)}

        Rules:
        - Use {language} with {framework}-appropriate test framework.
        - For Python: use pytest.
        - Wrap each test file in a markdown code block with its relative path:
          ```python backend/tests/test_file.py
          # test code
          ```
        """
        response = query_engine.query(test_prompt)
        return response.response


    def save_tests_from_llm(self, output: str):
        """
        Parse markdown code blocks from LLM output and save them as files.
        Auto-fixes broken imports for backend modules.
        """
        self.tests_dir.mkdir(parents=True, exist_ok=True)

        lines = output.split("\n")
        current_file = None
        buffer = []

        for line in lines:
            if line.strip().startswith("```"):
                if current_file:  # End of code block
                    filepath = self.tests_dir / current_file
                    filepath.parent.mkdir(parents=True, exist_ok=True)

                    fixed_code = "\n".join(buffer)

                    # --- AUTO-FIX imports with regex ---
                    fixes = [
                        # fix "from app import ..." → "from backend.app import ..." 
                        (r"\bfrom\s+app\s+import", "from backend.app import"),
                        # fix "import app" → "from backend import app"
                        (r"^import\s+app\b", "from backend import app"),
                        # fix "from models import ..." → "from backend.models import ..."
                        (r"\bfrom\s+models\s+import", "from backend.models import"),
                        # fix "import models" → "from backend import models"
                        (r"^import\s+models\b", "from bacend import models"),
                        # catch weird "from app from backend import"
                        (r"from app from backend", "from backend.app"),
                        (r"\bfrom\s+config\s+import", "from backend.config import"),
                        (r"^import\s+config\b", "from backend import config"),
                    ]
                    for pattern, repl in fixes:
                        fixed_code = re.sub(pattern, repl, fixed_code, flags=re.MULTILINE)

                    filepath.write_text(fixed_code, encoding="utf-8")
                    print(f" Wrote {filepath}")

                    # Reset
                    current_file, buffer = None, []
                else:
                    parts = line.strip().split(" ", 1)
                    if len(parts) > 1:
                        current_file = parts[1]
            else:
                if current_file:
                    buffer.append(line)

    def run(self):
        # Step 0: Ensure backend files exist
        self.ensure_backend_files()

        # Step 1: Build index and generate tests
        index = self.build_index()
        print("Loaded requirements and project files. Querying LlamaIndex...")
        output = self.generate_tests(index)

        # Step 2: Save tests from LLM output
        if output:
            self.save_tests_from_llm(output)
            print(f"\nTests saved inside: {self.tests_dir}")
        else:
            print("No response from LLM. Check API key / LlamaIndex setup.")


if __name__ == "__main__":
    project_dir = Path("project-root") if Path("project-root").is_dir() else Path("project")
    tests_dir = project_dir / "tests"

    agent = TesterAgent(project_dir, tests_dir)  # requirements_file auto-detected
    agent.run()
