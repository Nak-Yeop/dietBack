# monthly.py

from flask import Flask, request, jsonify
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# DB Connection
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

@app.route('/api/food/monthly', methods=['GET'])
def get_monthly_food():
    year = request.args.get('year')
    month = request.args.get('month')
    
    if not year or not month:
        return jsonify({"error": "Year and month are required"}), 400

    connection = pymysql.connect(**db_config)
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
    app.run(host='0.0.0.0', port=5001)  # 다른 포트로 실행하여 send.py와 충돌 방지