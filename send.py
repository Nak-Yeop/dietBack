# send.py

from flask import Flask, request, jsonify
import pymysql
import os
from dotenv import load_dotenv
from datetime import datetime
import llm

load_dotenv()

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)