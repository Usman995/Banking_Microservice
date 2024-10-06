import requests

BASE_URL = "http://localhost:5001"

def test_create_account():
    response = requests.post(f"{BASE_URL}/accounts", json={"user_id": 1, "initial_balance": 1000})
    print(f"Status code: {response.status_code}")
    print(f"Response content: {response.text}")
    assert response.status_code == 201
    print("Create account test passed")
    return response.json()['id']

def test_get_account(account_id):
    response = requests.get(f"{BASE_URL}/accounts/{account_id}")
    assert response.status_code == 200
    print("Get account test passed")

def test_update_balance(account_id):
    response = requests.put(f"{BASE_URL}/accounts/{account_id}/balance", json={"balance": 1500})
    assert response.status_code == 200
    print("Update balance test passed")


if __name__ == "__main__":
    account_id = test_create_account()
    test_get_account(account_id)
    test_update_balance(account_id)