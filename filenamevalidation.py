import os
import pandas as pd

def validate_file_name(file_path):
    """
    Reads a CSV file and checks if the file name contains
    the value from the second column, second row.
    """
    try:
        # Load CSV
        df = pd.read_csv(file_path)

        # Ensure at least 2 rows & 2 columns
        if df.shape[0] < 2 or df.shape[1] < 2:
            raise ValueError("CSV does not have a second row/second column")

        # Extract second column, second row
        second_col_value = str(df.iloc[1, 1]).strip()
        print(f"  ➜ Second column, second row value: {second_col_value}")

        # Get just the filename from full path
        file_name = os.path.basename(file_path)

        # Check match
        return second_col_value in file_name

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def validate_all_in_directory(directory_path):
    """
    Loops through all CSV files in a directory and validates each one.
    """
    for file in os.listdir(directory_path):
        if file.lower().endswith(".csv"):
            full_path = os.path.join(directory_path, file)
            print(f"\nChecking file: {file}")
            if validate_file_name(full_path):
                print("Filename contains the 2nd column, 2nd row value.")
            else:
                print("Filename does NOT contain the 2nd column, 2nd row value.")


# Example usage
if __name__ == "__main__":
    csv_directory_path = r"C:\Users\gangulay\Documents\GenAI\temp\data"
    validate_all_in_directory(csv_directory_path)

