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

import pymysql
from datetime import datetime

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
    print("로그인~")  # 디버깅 메시지
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

model = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),  # gpt-4o is set by env
    temperature=1.0
)

class NutritionInfo(BaseModel):
    calorie: str = Field(description="The amount of Calories")
    carbohydrate: str = Field(description="The amount of Carbohydrate")
    protein: str = Field(description="The amount of Protein")
    fat: str = Field(description="The amount of Fat")

output_parser = JsonOutputParser(pydantic_object=NutritionInfo)

prompt_template = ChatPromptTemplate.from_template(
    """
    음식이 입력되면 영양정보를 분석해줘
    필수 요소는 칼로리, 탄수화물, 단백질, 지방이야
    입력: {string}
    
    {format_instructions}
    """
).partial(format_instructions=output_parser.get_format_instructions())

def do(param):
    print(f"Received input: {param}")  # Debugging 출력 추가
    prompt_value = prompt_template.invoke({"string": param})
    model_output = model.invoke(prompt_value)
    output = output_parser.invoke(model_output)
    output_dict = output  # 이미 딕셔너리 형태로 반환됨
    output_dict['food_name'] = param  # 음식 이름을 추가
    print(f"Parsed output: {output_dict}")  # Debugging 출력 추가
    return output_dict

def save_to_db(user_id, nutrition_info):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO FOOD (ID, DATE, FOOD_NAME, FOOD_PT, FOOD_FAT, FOOD_CH, FOOD_KCAL)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                user_id,
                datetime.now(),
                nutrition_info['food_name'],
                nutrition_info['protein'],
                nutrition_info['fat'],
                nutrition_info['carbohydrate'],
                nutrition_info['calorie']
            ))
            print("Data saved to database")  # Debugging 출력 추가
        connection.commit()
    finally:
        connection.close()

@app.route('/api/send', methods=['POST'])
def send():
    data = request.json
    user_id = data.get('user_id')
    food_name = data.get('food_name')
    
    if not user_id or not food_name:
        return jsonify({"error": "user_id and food_name are required"}), 400

    nutrition_info = llm.do(food_name)
    
    save_to_db(user_id, nutrition_info)
    
    return jsonify(nutrition_info)


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


@app.route('/api/monthly', methods=['POST'])
def get_monthly_food():
    data = request.json
    year = data.get('year') 
    month = data.get('month')
    # year = request.args.get('year')
    # month = request.args.get('month')

    if not year or not month:
        return jsonify({"error": "Year and month are required"}), 400

    connection = create_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT DATE, FOOD_INDEX, FOOD_NAME, FOOD_PT, FOOD_FAT, FOOD_CH, FOOD_KCAL
                FROM FOOD
                WHERE YEAR(DATE) = %s AND MONTH(DATE) = %s
                ORDER BY DATE
            """
            cursor.execute(sql, (year, month))
            results = cursor.fetchall()
            monthly_data = {}

            for row in results:
                day = row[0].day
                food_info = {
                    "food_index": row[1],
                    "food_name": row[2],
                    "protein": row[3],
                    "fat": row[4],
                    "carbohydrates": row[5],
                    "calories": row[6]
                }

                # Ensuring the output order
                food_info_ordered = {
                    "food_index": food_info["food_index"],
                    "food_name": food_info["food_name"],
                    "protein": food_info["protein"],
                    "fat": food_info["fat"],
                    "carbohydrates": food_info["carbohydrates"],
                    "calories": food_info["calories"]
                }

                if day not in monthly_data:
                    monthly_data[day] = []

                monthly_data[day].append(food_info_ordered)

            # Create a list of 31 days, each day is a list of food items (which may be empty)
            grouped_data = [monthly_data.get(day, []) for day in range(1, 32)]

            return jsonify(grouped_data)
    finally:
        connection.close()

if __name__ == '__main__':
    print("Starting Flask application")  # 디버깅 메시지
    #insert_test_data()  # 애플리케이션 시작 시 테스트 데이터 삽입
    app.run(host='0.0.0.0', port=5000)