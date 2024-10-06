import requests

BASE_URL = "http://localhost:5000"  # Adjust if your service is running on a different port

def test_create_account():
    response = requests.post(f"{BASE_URL}/accounts", json={"user_id": 1, "initial_balance": 1000})
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

def test_list_accounts():
    response = requests.get(f"{BASE_URL}/accounts", params={"user_id": 1})
    assert response.status_code == 200
    print("List accounts test passed")

def test_close_account(account_id):
    response = requests.delete(f"{BASE_URL}/accounts/{account_id}")
    assert response.status_code == 204
    print("Close account test passed")

if __name__ == "__main__":
    account_id = test_create_account()
    test_get_account(account_id)
    test_update_balance(account_id)
    test_list_accounts()
    test_close_account(account_id)