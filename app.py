from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

app = Flask(__name__)

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route("/api/register", methods=["GET", "POST", "PUT"])
def register():
    if request.method == "GET":
        user_id = request.args.get("id")
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        connection = create_db_connection()
        if connection is None:
            return jsonify({"error": "Database connection failed"}), 500

        try:
            cursor = connection.cursor()
            query_nutrients = """SELECT RD_PROTEIN, RD_CARBO, RD_FAT FROM USER_NT WHERE ID=%s"""
            cursor.execute(query_nutrients, (user_id,))
            nutrients_result = cursor.fetchone()

            if nutrients_result is None:
                return jsonify({"error": "User NT not found"}), 404

            rd_protein, rd_carbo, rd_fat = nutrients_result
            return jsonify({
                "RD_PROTEIN": rd_protein,
                "RD_CARBO": rd_carbo,
                "RD_FAT": rd_fat,
            }), 200
        except Error as e:
            print(f"Database query error: {e}")
            return jsonify({"error": "Database query failed"}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    data = request.json

    if not data or "id" not in data or "pw" not in data:
        return jsonify({"error": "Invalid input"}), 400

    connection = create_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        
        if request.method == "PUT":
            query = """UPDATE USER SET PASSWORD=%s, BODY_WEIGHT=%s, HEIGHT=%s, AGE=%s, ACTIVITY=%s WHERE ID=%s"""
            values = (
                data["pw"],
                data["bodyweight"],
                data["height"],
                data["age"],
                data["activity"],
                data["id"]
            )
        else:
            query = """INSERT INTO USER (ID, PASSWORD, BODY_WEIGHT, HEIGHT, AGE, GENDER, ACTIVITY, RDI) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (
                data["id"],
                data["pw"],
                data["bodyweight"],
                data["height"],
                data["age"],
                data["gender"],
                data["activity"],
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

if __name__ == "__main__":
    app.run(debug=True)
