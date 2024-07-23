from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import llm

import pymysql
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# Load environment variables from .env
load_dotenv()

# Define db_config
db_config = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


# Database connection function
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
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM USER WHERE ID = %s AND PASSWORD = %s"
        cursor.execute(query, (data["id"], data["password"]))
        user = cursor.fetchone()

        if user:
            return jsonify({"message": "Login successful", "user": user})
        else:
            return jsonify({"error": "Invalid credentials"}), 401
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
        print("success")
        return jsonify(nutrition_info)
    except Error as e:
        print(f"Database operation error: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if connection.is_connected():
            connection.close()


def save_to_db(user_id, nutrition_info, connection):
    cursor = connection.cursor()
    try:
        sql = """
        INSERT INTO FOOD (user_id, DATE, FOOD_NAME, FOOD_PT, FOOD_FAT, FOOD_CH, FOOD_KCAL)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                user_id,
                datetime.now(),
                nutrition_info['food_name'],
                nutrition_info['protein'],
                nutrition_info['fat'],
                nutrition_info['carbohydrate'],
                nutrition_info['calorie']
            ),
        )
        print("Data saved to database")  # Debugging 출력 추가
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    app.run(debug=True)
