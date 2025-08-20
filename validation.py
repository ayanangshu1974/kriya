import os
import sqlite3
import pandas as pd
from llama_index.core import SimpleDirectoryReader

def find_files_with_partner_master(root_directory):
    """
    Iterates through all folders & subfolders starting at root_directory,
    and finds files that contain 'Partner_Master' in their name.
    """
    matching_files = []

    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if "Partner_Master" in filename:
                full_path = os.path.join(dirpath, filename)
                file_info = {
                    "file_name": filename,
                    "full_path": full_path
                }
                matching_files.append(file_info)
                print(f"Found: {full_path}")

    if not matching_files:
        print("No files found containing 'Partner_Master'.")

    return matching_files

def create_database_and_tables(files):
    """
    Creates a SQLite database named 'kriya' and tables with columns matching the headers of the CSV files.
    """
    # Connect to SQLite database
    conn = sqlite3.connect("kriya.db")
    cursor = conn.cursor()

    for file_info in files:
        try:
            # Read the CSV file using the full path
            df = pd.read_csv(file_info['full_path'])

            # Extract table name from file name (without extension)
            table_name = os.path.splitext(file_info['file_name'])[0]

            # Dynamically create table with columns matching CSV headers
            columns = ", ".join([f"{col} TEXT" for col in df.columns])
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});"
            cursor.execute(create_table_query)

            print(f"Table '{table_name}' created successfully.")
        except Exception as e:
            print(f"Error processing file {file_info['file_name']}: {e}")

    # Commit changes and close connection
    conn.commit()
    conn.close()

def insert_data_into_tables(files):
    """
    Reads data from the second row of each CSV file and inserts it into the respective tables in the 'kriya' database.
    """
    # Connect to SQLite database
    conn = sqlite3.connect("kriya.db")
    cursor = conn.cursor()

    for file_info in files:
        try:
            # Read the CSV file using the full path
            df = pd.read_csv(file_info['full_path'])

            # Ensure there are at least two rows
            if len(df) < 2:
                print(f"File {file_info['file_name']} does not have enough rows to insert data.")
                continue

            # Extract table name from file name (without extension)
            table_name = os.path.splitext(file_info['file_name'])[0]

            # Insert data from the second row onwards
            for _, row in df.iloc[1:].iterrows():
                placeholders = ", ".join(["?" for _ in row])
                insert_query = f"INSERT INTO {table_name} VALUES ({placeholders});"
                cursor.execute(insert_query, row.tolist())

            print(f"Data from {file_info['file_name']} inserted successfully into table '{table_name}'.")
        except Exception as e:
            print(f"Error inserting data from file {file_info['file_name']}: {e}")

    # Commit changes and close connection
    conn.commit()
    conn.close()


# Example usage
if __name__ == "__main__":
    root_dir = r"C:\\Users\\gangulay\\Documents\\GenAI\\temp\\data"  # Change to your folder path

    # Step 1: Find files containing 'Partner_Master'
    found_files = find_files_with_partner_master(root_dir)
    
    print("\nSummary:")
    for f in found_files:
        print(f"Filename: {f['file_name']} | Path: {f['full_path']}")       
        create_database_and_tables(found_files)
        insert_data_into_tables(found_files)



    # Step 2: Create database and tables
    #create_database_and_tables(found_files)

    # Step 3: Insert data into tables
    #insert_data_into_tables(found_files)

