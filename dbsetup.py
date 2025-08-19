# Create Agent which will set the database with schema 
# and provide a config file with the details like - 
#     DB_NAME: The name of the database to be created
#     DB_USER: The username for the database
#     DB_PASSWORD: The password for the database user
#     DB_HOST: The host where the database is located
#     DB_PORT: The port on which the database is running
import sqlite3
import json
import os

# Database configuration
DB_CONFIG = {
	"DB_NAME": "payloads.db",           # Name of the database
	"DB_USER": "",                      # Username (not used for SQLite)
	"DB_PASSWORD": "",                  # Password (not used for SQLite)
	"DB_HOST": "localhost",             # Host (default for local SQLite)
	"DB_PORT": ""                       # Port (not used for SQLite)
}

def setup_database():
	"""
	Create the SQLite database and the required schema (payloads table).
	"""
	conn = sqlite3.connect(DB_CONFIG["DB_NAME"])
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS payloads (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		data TEXT
	)''')
	conn.commit()
	conn.close()
	print(f"Database '{DB_CONFIG['DB_NAME']}' and table 'payloads' created.")

def write_config_file():
	"""
	Write the database configuration details to dbconfig.json.
	"""
	config_path = os.path.join(os.path.dirname(__file__), "dbconfig.json")
	with open(config_path, "w") as f:
		json.dump(DB_CONFIG, f, indent=4)
	print(f"Config file written to {config_path}")

if __name__ == "__main__":
	setup_database()
	write_config_file()
