import os
import sys
import json
import requests
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from llama_index.core import Document, VectorStoreIndex
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# -------------------------------
# Load environment
# -------------------------------
load_dotenv()
JIRA_URL = os.getenv("JIRA_URL")  
JIRA_USER = os.getenv("JIRA_USER")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = OpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

# -------------------------------
# Jira Fetch
# -------------------------------
def fetch_jira_issue(issue_id: str):
    url = f"{JIRA_URL}/rest/api/2/issue/{issue_id}"
    response = requests.get(url, auth=(JIRA_USER, JIRA_TOKEN))
    response.raise_for_status()
    return response.json()

# -------------------------------
# Process with LlamaIndex
# -------------------------------
def extract_sections_with_llama(jira_data: dict):
    summary = jira_data["fields"].get("summary", "")
    description = jira_data["fields"].get("description", "")

    # Convert dict ADF description to plain text if needed
    if isinstance(description, dict):
        description = json.dumps(description)

    text = f"""
    Jira Summary: {summary}
    Jira Description: {description}
    """

    doc = Document(text=text)
    index = VectorStoreIndex.from_documents([doc])
    query_engine = index.as_query_engine(llm=llm)

    prompt = """
    Extract the following sections from the Jira issue text:

    - Business Benefit
    - Objective
    - Description
    - Scope
    - Assumptions
    - Constraints

    Return output in JSON format like:
    {
      "Business Benefit": "...",
      "Objective": "...",
      "Description": "...",
      "Scope": "...",
      "Assumptions": "...",
      "Constraints": "..."
    }
    """

    response = query_engine.query(prompt)
    try:
        return json.loads(str(response))
    except Exception:
        return {"Description": str(response)}

# -------------------------------
# Build BRD PDF
# -------------------------------
def create_brd_pdf(issue_id: str, sections: dict, output_file: str):
    doc = SimpleDocTemplate(output_file)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Business Requirement Document</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Jira ID:</b> {issue_id}", styles["Normal"]))
    story.append(Spacer(1, 12))

    for key, value in sections.items():
        story.append(Paragraph(f"<b>{key}</b>", styles["Heading2"]))
        story.append(Paragraph(value if value else "N/A", styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)
    print(f" BRD created: {output_file}")

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        jira_id = sys.argv[1].strip()
        #jira_id = "Neev-307"
    else:
        jira_id = input("Enter Jira Issue ID: ").strip()
        #jira_id = "Neev-307"

    jira_data = fetch_jira_issue(jira_id)
    sections = extract_sections_with_llama(jira_data)
    create_brd_pdf(jira_id, sections, f"BRD.pdf")
