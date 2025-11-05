import sqlite3

# Connect to the database (it will be created if it doesn't exist)
conn = sqlite3.connect('railmadad.db')
cursor = conn.cursor()

# Create the 'queries' table
cursor.execute('''
CREATE TABLE IF NOT EXISTS queries (
    query_id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    status TEXT DEFAULT 'Open',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
''')

# (We will add the 'complaints' table in a later phase)

print("Database and 'queries' table created successfully.")
conn.commit()
conn.close()