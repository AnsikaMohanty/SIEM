from flask import Flask, request, jsonify
import mysql.connector

app = Flask(_name_)

# MySQL connection setup (update with your credentials)
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",          # MySQL host
        user="root",           # MySQL username
        password="rootroot",       # MySQL password
        database="db_name"         # Database name
    )

# API to update user details
@app.route('/update_user', methods=['POST'])
def update_user():
    user_id = request.json.get('id')
    new_name = request.json.get('name')
    new_age = request.json.get('age')

    # Establish connection to the MySQL database
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL query to update user details
    query = "UPDATE users SET name = %s, age = %s WHERE id = %s"
    values = (new_name, new_age, user_id)

    # Execute the query and commit changes
    try:
        cursor.execute(query, values)
        conn.commit()

        if cursor.rowcount > 0:
            return jsonify({"message": "User updated successfully!"}), 200
        else:
            return jsonify({"message": "User not found!"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

if _name_ == '_main_':
    app.run(debug=True)
