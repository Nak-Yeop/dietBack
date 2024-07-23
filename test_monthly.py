# test_monthly.py

import requests

def test_get_monthly_food(year, month):
    url = f"http://localhost:5001/api/food/monthly?year={year}&month={month}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for day, foods in enumerate(data, start=1):
            if foods:
                print(f"--- {year}-{month:02d}-{day:02d} ---")
                for food in foods:
                    print(f"  food_index: {food['food_index']}, food_name: {food['food_name']}, protein: {food['protein']}, fat: {food['fat']}, carbohydrates: {food['carbohydrates']}, calories: {food['calories']}")
            else:
                print(f"--- {year}-{month:02d}-{day:02d} --- No data")
            print()  # Print a blank line to separate days
    else:
        print(f"Failed to fetch data: {response.status_code}")

if __name__ == '__main__':
    test_year = 2024
    test_month = 7
    test_get_monthly_food(test_year, test_month)