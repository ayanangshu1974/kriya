# API endpoint that accepts a JSON payload, stores it in a SQLite database, and returns a response with the stored payload and its ID.
from flask import Flask, request, jsonify
import sqlite3

# Initialize Flask app
app = Flask(__name__)

# Database setup
def init_db():
	conn = sqlite3.connect('payloads.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS payloads (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT)''')
	conn.commit()
	conn.close()

init_db()

# API endpoint to receive JSON and store in DB
@app.route('/api/payload', methods=['POST'])
def receive_payload():
	if not request.is_json:
		return jsonify({'error': 'Invalid JSON'}), 400
	payload = request.get_json()
	conn = sqlite3.connect('payloads.db')
	c = conn.cursor()
	c.execute('INSERT INTO payloads (data) VALUES (?)', (str(payload),))
	conn.commit()
	row_id = c.lastrowid
	conn.close()
	return jsonify({'message': 'Payload stored', 'id': row_id, 'payload': payload}), 201

if __name__ == '__main__':
	app.run(debug=True)

