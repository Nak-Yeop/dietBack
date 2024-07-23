from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import llm

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# Load environment variables from .env
load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host=db_config["host"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    if not data or "id" not in data or "password" not in data:
        return jsonify({"error": "Invalid input"}), 400

    connection = create_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        query = """INSERT INTO USER (ID, PASSWORD, BODY_WEIGHT, HEIGHT, AGE, GENDER, ACTIVITY, RDI) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (
            data['id'],
            data['pw'],
            data['bodyweight'],
            data['height'],
            data['age'],
            data['gender'],
            data['activity'],
            None  # RDI 값을 기본값으로 설정 (필요에 따라 계산 후 설정 가능)
        )
        cursor.execute(query, values)
        connection.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Error as e:
        print(f"Database query error: {e}")
        return jsonify({"error": "Database query failed"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/api/send", methods=["POST"])
def send():
    data = request.json
    user_id = data.get("user_id")
    food_name = data.get("food_name")

    if not user_id or not food_name:
        return jsonify({"error": "user_id and food_name are required"}), 400

    print("!!! data:", data)  # Debugging output
    nutrition_info = llm.do(food_name)
    print(f"Parsed output: {nutrition_info}")  # Debugging output

    connection = create_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        save_to_db(user_id, nutrition_info, connection)
        return jsonify({"message": "Data saved successfully"})
    except Error as e:
        print(f"Database operation error: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if connection.is_connected():
            connection.close()


def save_to_db(user_id, nutrition_info, connection):
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO FOOD (user_id, food_name, calorie, carbohydrate, protein, fat)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                user_id,
                nutrition_info["food_name"],
                nutrition_info["calorie"],
                nutrition_info["carbohydrate"],
                nutrition_info["protein"],
                nutrition_info["fat"],
            ),
        )
        connection.commit()
    finally:
        cursor.close()


if __name__ == "__main__":
    app.run(debug=True)
