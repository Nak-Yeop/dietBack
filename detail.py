#날짜에 따른 총섭취량, 개별 음식 영양성분 return
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

#환경변수 load
load_dotenv()
app = Flask(__name__)

db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

# 데이터베이스 연결 설정
def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        return connection
    except Error as e:
        print(f"데이터베이스 연결 오류: {e}")
        return None


#REQUEST 객체에 ID, DATE 넘겨주세요
@app.route('/api/calendar', methods=['GET'])
def get_calendar_data():
    user_id = request.args.get('ID')
    date = request.args.get('DATE')
    connection = create_db_connection()

    if connection is None:
        return jsonify({"error": "데이터베이스 연결 실패"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT un.DATE,un.CARBO, un.PROTEIN, un.FAT, un.KCAL,
               f.FOOD_INDEX, f.FOOD_NAME, f.FOOD_PT, f.FOOD_FAT, f.FOOD_CH
        FROM USER u
        JOIN USER_NT un ON u.ID = un.ID
        LEFT JOIN FOOD f ON u.ID = f.ID AND un.DATE = f.DATE
        WHERE u.ID = %s AND un.DATE = %s
        ORDER BY f.FOOD_INDEX
        """
        cursor.execute(query, (user_id, date))
        #fetchall()은 쿼리의 결과를 가져오는 method
        results = cursor.fetchall()

        if not results:
            return jsonify({"message": "데이터가 없습니다."}), 404

        # 결과 데이터 구조화
        user_data = {
            "id": results[0]['ID'],
            "body_weight": results[0]['BODY_WEIGHT'],
            "height": results[0]['HEIGHT'],
            "nutrition": {
                "carbo": results[0]['CARBO'],
                "protein": results[0]['PROTEIN'],
                "fat": results[0]['FAT'],
                "kcal": results[0]['KCAL']
            },
            "foods": []
        }

        for row in results:
            if row['FOOD_INDEX'] is not None:
                user_data['foods'].append({
                    "food_index": row['FOOD_INDEX'],
                    "food_name": row['FOOD_NAME'],
                    "food_pt": row['FOOD_PT'],
                    "food_fat": row['FOOD_FAT'],
                    "food_ch": row['FOOD_CH']
                })

        return jsonify(user_data), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)