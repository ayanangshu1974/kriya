import os
import json
import re
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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = OpenAI(
    api_key=OPENAI_API_KEY,   # <-- API key here
    model="gpt-4o-mini",            # <-- valid model name here
    temperature=0
)
# -------------------------------
# PDF Loading
# -------------------------------
from llama_index.readers.file import PDFReader

pdf_loader = PDFReader()
pdf_file = "BRD.pdf" # For simplicity hardcoding the file name here
pdf_paths = [os.path.join(os.getcwd(), pdf_file)]  # adjust path if needed

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

# AgentRunner to manage the agent
agent = AgentRunner(agent_worker)

# -------------------------------
# Query the Agent
# -------------------------------
query1 = '''Extract 5 functional requirement with user stories and, 
            one major Non functional requirements with user stories and scope
             from the BRD and respond in JSON format only.
            Also create a text file with the Json response named Requirement.txt 
            and save in the root path. '''
response1 = agent.chat(query1)
query2 = '''' Create Requirements.txt file which has all packages dependencies needed for the project.
            Also create a text file with the txt response named Requirements.txt 
            and save in the root path.'''

response2 = agent.chat(query2)

# -------------------------------
# Output
# -------------------------------
print("===== AGENT RESPONSE =====")
print(response1.response)

# -------------------------------
# Parse JSON safely
# -------------------------------
from datetime import datetime
match = re.search(r'(\{.*\}|\[.*\])', response1.response, re.DOTALL)
if match:
    json_output = json.loads(match.group(0))
    print("===== PARSED JSON =====")
    print(json.dumps(json_output, indent=2))
  
    # -------------------------------
    # Handle filename with timestamp
    # -------------------------------
    #filepath = ""
    base_filename = "requirement.json"
    #filepath = os.getenv("REQUIREMENT") + base_filename
    #print (f" ---{filepath}---")
    #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #print(f"timestamp: {timestamp}")
    filename = f"requirement.json"
    
    # Save JSON file

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)

    print(f" JSON saved to {filename}")

else:
    print(" Could not extract JSON automatically. Raw response above.")

match = re.search(r'(\{.*\}|\[.*\])', response2.response, re.DOTALL)
if match:
    json_output = json.loads(match.group(0))
    print("===== PARSED JSON =====")
    print(json.dumps(json_output, indent=2))
  
    # -------------------------------
    # Handle filename with timestamp
    # -------------------------------
    #filepath = ""
    base_filename = "requirements.txt"
    #filepath = os.getenv("REQUIREMENT") + base_filename
    #print (f" ---{filepath}---")
    #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #print(f"timestamp: {timestamp}")
    filename = f"requirements.txt"
    
    # Save JSON file

    with open(filename, "w", encoding="utf-8") as f:
        f.write(response2.response)

    print(f" TEXT saved to {filename}")

else:
    print(" Could not extract TEXT automatically. Raw response above.")
