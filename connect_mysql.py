import mysql.connector

# Establish connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="rootroot",
    database="testdb"  # Make sure this DB exists
)

cursor = conn.cursor()

# Example: Create a table
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255))")

# Insert data
cursor.execute("INSERT INTO users (name) VALUES (%s)", ("Alice",))
conn.commit()

# Fetch data
cursor.execute("SELECT * FROM users")
for row in cursor.fetchall():
    print(row)

# Close
cursor.close()
conn.close()
