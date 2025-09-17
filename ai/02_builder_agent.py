import os
import json
import re
import requests
from dotenv import load_dotenv

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# -------------------------------
# LLM Setup
# -------------------------------
from llama_index.llms.openai import OpenAI

llm = OpenAI(
    api_key=OPENAI_API_KEY,  # <-- API key here
    model="gpt-4o-mini",     # <-- valid model name here
    temperature=0
)

# -------------------------------
# PDF Loading
# -------------------------------
from llama_index.readers.file import PDFReader

pdf_loader = PDFReader()
pdf_file = "BRD.pdf"  # Hardcoded filename
pdf_paths = [os.path.join(os.getcwd(), pdf_file)]

all_docs = []
for path in pdf_paths:
    all_docs.extend(pdf_loader.load_data(file=path))

print(f"Loaded {len(all_docs)} documents from PDFs.")

# -------------------------------
# Build VectorStoreIndex
# -------------------------------
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents(all_docs)
query_engine = index.as_query_engine()

# -------------------------------
# Wrap QueryEngine in a Tool
# -------------------------------
from llama_index.core.tools import QueryEngineTool, ToolMetadata

brd_tool = QueryEngineTool(
    query_engine=query_engine,
    metadata=ToolMetadata(
        name="BRD_Query_Tool",
        description="Use this tool to query the BRD and extract functional and non-functional requirements."
    )
)

# -------------------------------
# Build Agent
# -------------------------------
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner

system_prompt = """You are an expert in web architecture and solution design.
Your task is to carefully analyze the BRD (Business Requirement Document),
extract business requirements, and translate them into:
1. Functional requirements
2. Non-functional requirements
3. APIs, integrations, and data flow needs
4. Technology stack suggestions
5. Create Requirements.txt file which has all packages dependencies needed for the project.
Respond in JSON format."""

agent_worker = FunctionCallingAgentWorker.from_tools(
    tools=[brd_tool],
    llm=llm,
    system_prompt=system_prompt,
    verbose=True
)

agent = AgentRunner(agent_worker)

# -------------------------------
# Queries
# -------------------------------
query1 = '''Extract 5 functional requirement with user stories and,
one major Non functional requirements with user stories and scope
from the BRD and respond in JSON format only.
Also create a text file with the Json response named Requirement.txt
and save in the root path. '''
response1 = agent.chat(query1)

query2 = '''Create requirements_pkgs.json file which has all packages dependencies needed for
the project.Also create a json file with the json response named requirements_pkgs.json
and save in the root path.'''
response2 = agent.chat(query2)

# -------------------------------
# Function to fetch latest version from PyPI
# -------------------------------
def fetch_latest_version(pkg):
    try:
        url = f"https://pypi.org/pypi/{pkg}/json"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data['info']['version']
    except Exception as e:
        print(f"Warning: Could not fetch latest version for package {pkg}: {e}")
    return None

# -------------------------------
# Sanitize and update dependencies dynamically
# -------------------------------
def sanitize_dependencies_dynamic(deps: dict) -> dict:
    clean_deps = {}
    for pkg, ver in deps.items():
        # Strip caret, tilde, etc from agent version suggestion
        base_ver = ver.lstrip("^~<>= ") if isinstance(ver, str) else ver
        latest_ver = fetch_latest_version(pkg)
        if latest_ver:
            clean_deps[pkg] = latest_ver
        else:
            clean_deps[pkg] = base_ver
    return clean_deps

# -------------------------------
# Handle first response (functional requirements)
# -------------------------------
print("===== AGENT RESPONSE =====")
print(response1.response)

from datetime import datetime
match = re.search(r'(\{.*\}|\[.*\])', response1.response, re.DOTALL)
if match:
    json_output = json.loads(match.group(0))
    print("===== PARSED JSON =====")
    print(json.dumps(json_output, indent=2))
    filename = "requirement.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    print(f"JSON saved to {filename}")
else:
    print("Could not extract JSON automatically. Raw response above.")

# -------------------------------
# Handle second response (package dependencies)
# -------------------------------
match = re.search(r'(\{.*\}|\[.*\])', response2.response, re.DOTALL)
if match:
    json_output = json.loads(match.group(0))
    print("===== PARSED JSON =====")
    print(json.dumps(json_output, indent=2))
    # Sanitize and replace with latest versions dynamically
    if 'dependencies' in json_output:
        json_output['dependencies'] = sanitize_dependencies_dynamic(json_output['dependencies'])
    filename = "requirements_pkgs.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    print(f"JSON saved to {filename}")
else:
    print("Could not extract JSON automatically. Raw response above.")
