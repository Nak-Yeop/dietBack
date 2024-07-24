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
    print(f"Received login request for user ID: {data.get('id')}")  # 디버깅 메시지

    connection = create_db_connection()
    if connection is None:
        print("Database connection failed")  # 디버깅 메시지
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM USER WHERE ID = %s AND PASSWORD = %s"
        print(f"Executing query: {query}")  # 디버깅 메시지
        cursor.execute(query, (data["id"], data["password"]))
        user = cursor.fetchone()

        if user:
            print(f"Login successful for user: {user['ID']}")  # 디버깅 메시지
            user.pop("PASSWORD", None)
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
        "id": user_id,
        "password": user_password,
        "bodyweight": 70,  # 예시 데이터
        "height": 178,  # 예시 데이터
        "age": 30,  # 예시 데이터
    }

    connection = create_db_connection()
    if connection is None:
        print("Database connection failed")
        return

    try:
        cursor = connection.cursor()

        # 아이디 중복 확인
        query = "SELECT * FROM USER WHERE ID = %s"
        cursor.execute(query, (data["id"],))
        existing_user = cursor.fetchone()

        if existing_user:
            print(
                f"User ID {data['id']} already exists. Skipping insertion."
            )  # 디버깅 메시지
        else:
            query = """INSERT INTO USER (ID, PASSWORD, BODY_WEIGHT, HEIGHT, AGE) 
                       VALUES (%s, %s, %s, %s, %s)"""
            values = (
                data["id"],
                data["password"],
                data["bodyweight"],
                data["height"],
                data["age"],
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
    temperature=1.0,
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
    output_dict["food_name"] = param  # 음식 이름을 추가
    print(f"Parsed output: {output_dict}")  # Debugging 출력 추가
    return output_dict


def save_to_db(user_id, nutrition_info):
    connection = create_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO FOOD (ID, DATE, FOOD_NAME, FOOD_PT, FOOD_FAT, FOOD_CH, FOOD_KCAL)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    user_id,
                    datetime.now(),
                    nutrition_info["food_name"],
                    nutrition_info["protein"],
                    nutrition_info["fat"],
                    nutrition_info["carbohydrate"],
                    nutrition_info["calorie"],
                ),
            )
            print("Data saved to database")  # Debugging 출력 추가
        connection.commit()
    finally:
        connection.close()


@app.route("/api/send", methods=["POST"])
def send():
    data = request.json
    user_id = data.get("user_id")
    food_name = data.get("food_name")

    if not user_id or not food_name:
        return jsonify({"error": "user_id and food_name are required"}), 400

    nutrition_info = do(food_name)

    # save_to_db(user_id, nutrition_info)

    return jsonify(nutrition_info)


@app.route("/api/send2", methods=["POST"])
def send2():
    data = request.json
    user_id = data.get("user_id")
    nutrition_info = data.get("nutrition_info")
    try:
        save_to_db(user_id, nutrition_info)
        return jsonify({"message": "good"}), 200
    except:
        return jsonify({"message":"DB save error"}),500


@app.route('/api/add_food', methods=['POST'])
def add_food():
    data = request.json
    
    user_id = data.get('ID')
    date = data.get('DATE')
    food_name = data.get('FOOD_NAME')
    
    if not user_id or not date or not food_name:
        return jsonify({"error": "필수 정보가 누락되었습니다."}), 400

    # LLM을 통해 음식 영양 정보를 가져옴
    nutrition_info = do(food_name)

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # FOOD_INDEX를 구함 (해당 날짜의 가장 높은 인덱스를 찾아 +1)
            cursor.execute("SELECT MAX(FOOD_INDEX) FROM FOOD WHERE ID = %s AND DATE = %s", (user_id, date))
            max_index = cursor.fetchone()[0]
            food_index = max_index + 1 if max_index is not None else 0

            insert_query = """
            INSERT INTO FOOD (ID, DATE, FOOD_INDEX, FOOD_NAME, FOOD_CH, FOOD_PT, FOOD_FAT, FOOD_KCAL)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                user_id, date, food_index,
                nutrition_info['food_name'],
                nutrition_info['carbohydrate'],
                nutrition_info['protein'],
                nutrition_info['fat'],
                nutrition_info['calorie']
            ))
            connection.commit()

            added_food_info = {
                "ID": user_id,
                "DATE": date,
                "FOOD_INDEX": food_index,
                "food_name": nutrition_info['food_name'],
                "carbohydrates": nutrition_info['carbohydrate'],
                "protein": nutrition_info['protein'],
                "fat": nutrition_info['fat'],
                "calorie": nutrition_info['calorie']
            }
            print(added_food_info)
            return jsonify({"message": "음식이 성공적으로 추가되었습니다.", "data": added_food_info}), 201

    except pymysql.MySQLError as e:
        return jsonify({"error": str(e)}), 500

    finally:
        connection.close()

@app.route('/api/update_food', methods=['POST'])
def update_food():
    data = request.json

    user_id = data.get('ID')
    date = data.get('DATE')
    food_index = data.get('FOOD_INDEX')
    new_food_name = data.get('NEW_FOOD_NAME')
    
    if not user_id or not date or not food_index or not new_food_name:
        return jsonify({"error": "필수 정보가 누락되었습니다."}), 400

    # LLM을 통해 새로운 음식 영양 정보를 가져옴
    new_nutrition_info = do(new_food_name)

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            update_query = """
            UPDATE FOOD
            SET FOOD_NAME = %s, FOOD_CH = %s, FOOD_PT = %s, FOOD_FAT = %s, FOOD_KCAL = %s
            WHERE ID = %s AND DATE = %s AND FOOD_INDEX = %s
            """
            cursor.execute(update_query, (
                new_nutrition_info['food_name'],
                new_nutrition_info['carbohydrate'],
                new_nutrition_info['protein'],
                new_nutrition_info['fat'],
                new_nutrition_info['calorie'],
                user_id, date, food_index
            ))
            connection.commit()
          
            updated_food_info = {
                "ID": user_id,
                "DATE": date,
                "FOOD_INDEX": food_index,
                "food_name": new_nutrition_info['food_name'],
                "carbohydrates": new_nutrition_info['carbohydrate'],
                "protein": new_nutrition_info['protein'],
                "fat": new_nutrition_info['fat'],
                "calorie": new_nutrition_info['calorie']
            }
          
            return jsonify({"message": "음식이 성공적으로 수정되었습니다.", "data": updated_food_info}), 200

    except pymysql.MySQLError as e:
        return jsonify({"error": str(e)}), 500

    finally:
        connection.close()

    



@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    if not data or "id" not in data or "pw" not in data:
        return jsonify({"error": "Invalid input"}), 400

    connection = create_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        if request.method == "POST":
            # POST 요청: 새로운 사용자 등록
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
                None,  # RDI 값을 기본값으로 설정 (필요에 따라 계산 후 설정 가능)
            )
            cursor.execute(query, values)
            connection.commit()
            return jsonify({"message": "User registered successfully"}), 201
        elif request.method == "PUT":
            print("!!!data: ", data)
            # PUT 요청: 기존 사용자 정보 업데이트
            query = """UPDATE USER SET PASSWORD=%s, BODY_WEIGHT=%s, HEIGHT=%s, AGE=%s, GENDER=%s, ACTIVITY=%s, RDI=%s 
                       WHERE ID=%s"""
                       
            values = (
                data["pw"],
                data["bodyweight"],
                data["height"],
                data["age"],
                data["gender"],
                data["activity"],
                None,  # RDI 값을 기본값으로 설정 (필요에 따라 계산 후 설정 가능)
                data["id"],
            )
            cursor.execute(query, values)
            connection.commit()
            print(cursor)
            if cursor.rowcount == 0:
                return jsonify({"error": "User not found"}), 404
            return jsonify({"message": "User updated successfully"}), 200
    except Error as e:
        print(f"Database query error: {e}")
        return jsonify({"error": "Database query failed"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("할거다함")


# 특정 음식을 삭제하는 엔드포인트
@app.route("/api/delete_food", methods=["DELETE"])
def delete_food():
    user_id = request.args.get("ID")
    date = request.args.get("DATE")
    food_index = request.args.get("FOOD_INDEX")

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


@app.route("/api/monthly", methods=["POST"])
def get_monthly_food():
    data = request.json
    year = data.get("year")
    month = data.get("month")
    UID = data.get("UID")
    if not year or not month:
        return jsonify({"error": "Year and month are required"}), 400

    connection = create_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT DATE, FOOD_INDEX, FOOD_NAME, FOOD_PT, FOOD_FAT, FOOD_CH, FOOD_KCAL
                FROM FOOD
                WHERE YEAR(DATE) = %s AND MONTH(DATE) = %s
                AND ID = %s
                ORDER BY DATE
            """
            cursor.execute(sql, (year, month, UID))
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
                    "calories": row[6],
                }

                # Ensuring the output order
                food_info_ordered = {
                    "food_index": food_info["food_index"],
                    "food_name": food_info["food_name"],
                    "protein": food_info["protein"],
                    "fat": food_info["fat"],
                    "carbohydrates": food_info["carbohydrates"],
                    "calories": food_info["calories"],
                }

                if day not in monthly_data:
                    monthly_data[day] = []

                monthly_data[day].append(food_info_ordered)

            # Create a list of 31 days, each day is a list of food items (which may be empty)
            grouped_data = [monthly_data.get(day, []) for day in range(1, 32)]

            return jsonify(grouped_data)
    finally:
        connection.close()


if __name__ == "__main__":
    print("Starting Flask application")  # 디버깅 메시지
    # insert_test_data()  # 애플리케이션 시작 시 테스트 데이터 삽입
    app.run(host="0.0.0.0", port=5000)
