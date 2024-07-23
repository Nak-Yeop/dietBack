# test_llm.py

import llm
import pymysql
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# DB Connection
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

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
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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

# Test input
test_user_id = '11'  # 이 부분에 유효한 사용자 ID를 넣으세요.
test_food = "떡볶이"  # 이 부분에 원하는 테스트 음식을 넣으세요.

# Get nutrition info
nutrition_info = llm.do(test_food)

save_to_db(test_user_id, nutrition_info)
print(f"Nutrition information for {test_food} has been saved to the database.")