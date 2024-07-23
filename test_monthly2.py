# test_monthly.py

import requests

def test_get_monthly_food(year, month):
    url = f"http://localhost:5001/api/food/monthly?year={year}&month={month}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None

if __name__ == '__main__':
    test_year = 2024
    test_month = 7
    test_get_monthly_food(test_year, test_month)