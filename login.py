from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

app = Flask(__name__)
CORS(app)  # 크로스 오리진 요청 허용

print("Flask application initialized")  # 디버깅 메시지

# .env 파일에서 환경변수 로드
load_dotenv()
print(f"Environment variables loaded. DB_HOST: {os.getenv('DB_HOST')}")  # 디버깅 메시지

# 데이터베이스 연결 설정
def create_db_connection():
    print("Attempting to create database connection")  # 디버깅 메시지
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        print("Database connection successful")  # 디버깅 메시지
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

@app.route('/api/login', methods=['POST'])
def login():
    print("Login route accessed")  # 디버깅 메시지
    data = request.json
    print(f"Received login request for user ID: {data.get('id')}")  # 디버깅 메시지
    
    connection = create_db_connection()
    if connection is None:
        print("Database connection failed")  # 디버깅 메시지
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM USER WHERE ID = %s AND PASSWORD = %s"
        print(f"Executing query: {query}")  # 디버깅 메시지
        cursor.execute(query, (data['id'], data['password']))
        user = cursor.fetchone()

        if user:
            print(f"Login successful for user: {user['ID']}")  # 디버깅 메시지
            user.pop('PASSWORD', None)
            return jsonify({"message": "Login successful", "user": user}), 200
        else:
            print("Invalid credentials")  # 디버깅 메시지
            return jsonify({"error": "Invalid credentials"}), 401

    except Error as e:
        print(f"Database error occurred: {str(e)}")  # 디버깅 메시지
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed")  # 디버깅 메시지

def insert_test_data():
    print("Inserting test data...")  # 디버깅 메시지
    
    # 콘솔에서 사용자 입력 받기
    user_id = input("Enter user ID: ")
    user_password = input("Enter user password: ")
    
    data = {
        'id': user_id,
        'password': user_password,
        'bodyweight': 70,  # 예시 데이터
        'height': 178,     # 예시 데이터
        'age': 30          # 예시 데이터
    }

    connection = create_db_connection()
    if connection is None:
        print("Database connection failed")
        return

    try:
        cursor = connection.cursor()
        
        # 아이디 중복 확인
        query = "SELECT * FROM USER WHERE ID = %s"
        cursor.execute(query, (data['id'],))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"User ID {data['id']} already exists. Skipping insertion.")  # 디버깅 메시지
        else:
            query = """INSERT INTO USER (ID, PASSWORD, BODY_WEIGHT, HEIGHT, AGE) 
                       VALUES (%s, %s, %s, %s, %s)"""
            values = (
                data['id'],
                data['password'],
                data['bodyweight'],
                data['height'],
                data['age']
            )
            cursor.execute(query, values)
            connection.commit()
            print("Test user inserted successfully")  # 디버깅 메시지
    except Error as e:
        print(f"An error occurred: {str(e)}")  # 디버깅 메시지
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed")  # 디버깅 메시지

if __name__ == '__main__':
    print("Starting Flask application")  # 디버깅 메시지
    insert_test_data()  # 애플리케이션 시작 시 테스트 데이터 삽입
    app.run(debug=True)