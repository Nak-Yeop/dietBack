from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# 환경 변수 로드
print("Loading .env file...")
load_dotenv()

db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

# 환경 변수 확인을 위한 디버그 출력
print(f"DB_HOST: {db_host}")
print(f"DB_NAME: {db_name}")
print(f"DB_USER: {db_user}")
print(f"DB_PASS: {db_password}")

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

# 특정 음식을 삭제하는 엔드포인트
@app.route('/api/delete_food', methods=['DELETE'])
def delete_food():
    user_id = request.json.get('ID')
    date = request.json.get('DATE')
    food_index = request.json.get('FOOD_INDEX')
    
    if not user_id or not date or not food_index:
        return jsonify({"error": "필수 정보가 누락되었습니다."}), 400

    connection = create_db_connection()
    if connection is None:
        return jsonify({"error": "데이터베이스 연결 실패"}), 500

    try:
        cursor = connection.cursor()
        delete_query = """
        DELETE FROM FOOD
        WHERE ID = %s AND DATE = %s AND FOOD_INDEX = %s
        """
        cursor.execute(delete_query, (user_id, date, food_index))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"message": "삭제할 데이터가 없습니다."}), 404

        return jsonify({"message": "음식이 성공적으로 삭제되었습니다."}), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)