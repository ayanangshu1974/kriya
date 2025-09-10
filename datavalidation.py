from dotenv import load_dotenv
import os
import sqlite3
import json
from datetime import datetime
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core import SQLDatabase
from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent
from llama_index.llms.openai import OpenAI
from llama_index.core.base.llms.types import ChatMessage
import pandas as pd
from IPython.display import Markdown
import asyncio
import sys
import re
import yaml
from IPython.display import Markdown, display


# Fix Windows asyncio bug
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

tables = []
load_dotenv()
os.environ["OPENAI_API_KEY"]

#Reading CSV file
def load_config(config_path="config.yaml"):
    """Load YAML config file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def fetch_dynamic_columns(csv_file_path, config_path="config.yaml"):
    """
    Dynamically fetch column values from CSV based on config.
    Config controls row index, columns list, and check_all_rows flag.
    """
    try:
        # Load config
        config = load_config(config_path)["csv_verification"]
        row_index = config.get("row_index", 1)
        check_all_rows = config.get("check_all_rows", False)
        columns = config.get("columns", [])

        # Load CSV
        df = pd.read_csv(csv_file_path)

        # Validate required columns
        for col_cfg in columns:
            col_name = col_cfg["name"]
            if col_cfg.get("required", False) and col_name not in df.columns:
                raise ValueError(f"Missing required column: {col_name}")

        # Extract only one row (default)
        if not check_all_rows:
            if row_index >= len(df):
                raise ValueError(f"CSV does not have row index {row_index}")
            row = df.iloc[row_index]
            extracted = {}
            for col_cfg in columns:
                col_name = col_cfg["name"]
                if col_name in row:
                    val = str(row[col_name]).strip()
                    if col_cfg.get("to_upper", False):
                        val = val.upper()
                    extracted[col_name] = val
            print(f" Extracted row {row_index}: {extracted}")
            return [extracted]

        # Extract all rows
        results = []
        for _, row in df.iterrows():
            extracted = {}
            for col_cfg in columns:
                col_name = col_cfg["name"]
                if col_name in row:
                    val = str(row[col_name]).strip()
                    if col_cfg.get("to_upper", False):
                        val = val.upper()
                    extracted[col_name] = val
            results.append(extracted)
        print(f"Extracted {len(results)} rows")
        return results

    except Exception as e:
        print(f"Error: {e}")
        return []


#############################
# Path to your SQLite database file
db_path = "kriya.db"
sqlite_uri = f"sqlite:///{db_path}"
conn = sqlite3.connect("kriya.db")
cursor = conn.cursor()
try:
    sql_database = SQLDatabase.from_uri(sqlite_uri)
    print("Database connection successful!")
except Exception as e:
    print(f"Database connection failed: {e}")

# Create SQL Query Engine
sql_database = SQLDatabase.from_uri(sqlite_uri)
sql_query_engine = NLSQLTableQueryEngine(
    sql_database=sql_database,
    tables=tables
)
db_tool = QueryEngineTool(
    query_engine=sql_query_engine,
    metadata=ToolMetadata(
        name="database_validator",
        description="SQL database containing partner details and POS/Inventory information tables."
    )
)
system_prompt = """You are an experienced Data administrator.
Your task is to check the data availability in the tables."""

tools = [db_tool]
agent = FunctionAgent(
    name="database_analyzer_agent",
    description="Database Analyzer Agent",
    tools=tools,
    llm=OpenAI(model="gpt-4o-mini"),
    system_prompt=system_prompt,
    verbose=False
)

async def main(agent, records):
    try:
        print("......Starting main().....")

        # Iterate through all extracted rows from CSV
        for idx, row in enumerate(records, start=1):
            print(f"\n Processing Row {idx}: {row}")

            # Dynamically build query conditions
            query_parts = []
            for col_name, value in row.items():
                if not value:
                    continue
                # Normalize value (remove suffixes like LTD, INC, etc.)
                value_clean = re.sub(r"\b(LTD|LIMITED|COMPANY|INC|CO)\b", "", value, flags=re.IGNORECASE).strip()
                query_parts.append(f"{col_name} = '{value_clean}'")

            # Skip if no valid conditions
            if not query_parts:
                print(f" No valid conditions for row {idx}, skipping...")
                continue

            # Build final natural language query
            query_content = (
                f"Verify in the HPI_Partner_Master table if "
                + " AND ".join(query_parts)
                + " (ignoring suffixes like LTD, LIMITED, COMPANY, INC, CO)."
            )

            query_input = ChatMessage(role="user", content=query_content)

            print("\n Final NL Query Sent to LlamaIndex:\n", query_input.content)

            # Run query against agent
            response = await agent.run(query_input, max_iterations=50)
            print(" Response:", response)

    except Exception as e:
        print(f" Error in main(): {e}")
    finally:
        print(" Exiting main()...")


if __name__ == "__main__":
    csv_file_path = r"C:\\Users\\gangulay\\Documents\\GenAI\\temp\\data\\V2_POS_AMPLIFY_2-SIWB-20652.csv"
    config_path = "config.yaml"
    records = fetch_dynamic_columns(csv_file_path, config_path)
    print(records)
    #display(Markdown(f"{records}"))
