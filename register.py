from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

print("Loading .env file...")
load_dotenv()

db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASS')

# 환경 변수 확인을 위한 디버그 출력
print(f"DB_HOST: {db_host}")
print(f"DB_NAME: {db_name}")
print(f"DB_USER: {db_user}")
print(f"DB_PASSWORD: {db_password}")

app = Flask(__name__)

# 데이터베이스 연결 설정
def create_db_connection():
    try:
        print("Attempting to connect to the database...")
        connection = mysql.connector.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        print("Database connection successful!")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    if not data or 'id' not in data or 'pw' not in data:
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
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# 애플리케이션 시작 시 임의의 데이터 삽입
def insert_test_data():
    print("Inserting test data...")
    data = {
        'id': "admin2",
        'pw': '2',
        'bodyweight': 70,
        'height': 178,
        'age': 25,
        'gender': 1,
        'activity': 5
    }

    connection = create_db_connection()
    if connection is None:
        print("Database connection failed")
        return

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
        print("Test user inserted successfully")
    except Error as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    print("Starting application…")
    insert_test_data()  # 애플리케이션 시작 시 테스트 데이터 삽입
    app.run(debug=True)  # 기본 포트(5000)에서 실행