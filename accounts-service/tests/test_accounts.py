# test_accounts.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.app import app, db, Account
from flask import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()



@pytest.mark.parametrize("user_id, initial_balance, account_type, expected_status, expected_error", [
    (1, 1000, 'savings', 201, None),                          # Valid input
    (2, 500, 'checking', 201, None),                          # Valid input
    (3, 0, 'savings', 201, None),                             # Valid input with zero balance
    (4, -100, 'savings', 400, 'Initial balance cannot be negative'),  # Invalid input (negative balance)
    (5, None, 'savings', 201, None),                          # Valid input (None should default to 0)
    ("abcd", 100, 'savings', 400, 'Invalid user type'),      # Invalid user_id (non-integer)
])
def test_create_account(client, user_id, initial_balance, account_type, expected_status, expected_error):
    response = client.post('/accounts', json={
        'user_id': user_id,
        'initial_balance': initial_balance,
        'account_type': account_type
    })

    assert response.status_code == expected_status

    if expected_error:
        assert expected_error in response.get_json()['error']
    else:
        data = response.get_json()
        assert 'id' in data
        assert data['user_id'] == user_id
        assert data['balance'] == (initial_balance if initial_balance is not None else 0)
        assert data['account_type'] == account_type

@pytest.mark.parametrize("user_id_create, user_id_lookup, expected_status, expected_balance, expected_account_type", [
    (1, 1, 200, 1000, 'savings'),  # Valid lookup for an existing account
    (1, 2, 404, None, None),        # Lookup for a non-existing account
    (2, 1, 404, None, None),        # Lookup for a non-existing account (created user_id)
])
def test_get_account(client, user_id_create, user_id_lookup, expected_status, expected_balance, expected_account_type):
    # Create an account to update
    response = client.post('/accounts', json={
        'user_id': user_id_create,
        'initial_balance': 1000,
        'account_type': 'savings'
    })
    assert response.status_code == 201  # Ensure account creation was successful

    # Now, attempt to get the account
    get_response = client.get(f'/accounts/{user_id_lookup}')

    # Assert the response status code
    assert get_response.status_code == expected_status

    if expected_status == 200:
        data = get_response.get_json()
        assert data['user_id'] == user_id_lookup
        assert data['balance'] == expected_balance
        assert data['account_type'] == expected_account_type
    elif expected_status == 404:
        error_data = get_response.get_json()
        assert 'error' in error_data
        assert error_data['error'] == 'Account does not exist'

@pytest.mark.parametrize("new_balance, expected_status", [
    (1000, 200),   # Valid balance
    (500, 200),    # Valid balance
    (0, 200),      # Valid balance
    (-100, 400),   # Invalid balance (assuming your app returns 400 for negative balance)
    (10000, 200),  # Valid balance (high value)
])
def test_update_balance(client, new_balance, expected_status):
    # First, create an account to update
    response = client.post('/accounts', json={
        'user_id': 1,
        'balance': 1000
    })
    account_id = response.get_json()['id']

    # Now, update the balance
    put_response = client.put(f'/accounts/{account_id}/balance', json={
        'balance': new_balance
    })

    # Assert the response status code
    assert put_response.status_code == expected_status

    # If the update is successful, check the balance
    if expected_status == 200:
        updated_account = client.get(f'/accounts/{account_id}')
        assert updated_account.get_json()['balance'] == new_balance


@pytest.mark.parametrize("user_id, expected_status, should_exist", [
    (1, 200, False),  # Valid deletion, account should not exist afterward
    (2, 404, False),  # Attempt to delete a non-existing account
])
def test_delete_account(client, user_id, expected_status, should_exist):
    # Create an account to delete
    response = client.post('/accounts', json={
        'user_id': 1,
        'initial_balance': 1000,
        'account_type': 'savings'
    })
    assert response.status_code == 201  # Ensure account creation was successful

    # Attempt to delete the account
    delete_response = client.delete(f'/accounts/{user_id}')

    # Assert the response status code
    assert delete_response.status_code == expected_status

    # Check if the account still exists in the database
    if should_exist:
        get_response = client.get(f'/accounts/{user_id}')
        assert get_response.status_code == 200  # Account should exist
    else:
        get_response = client.get(f'/accounts/{user_id}')
        assert get_response.status_code == 404  # Account should not exist

def test_list_accounts(client):
    # Create some accounts
    response1 = client.post('/accounts', json={
        'user_id': 1,
        'initial_balance': 1000,
        'account_type': 'savings'
    })
    assert response1.status_code == 201  # Ensure account creation was successful

    response2 = client.post('/accounts', json={
        'user_id': 2,
        'initial_balance': 500,
        'account_type': 'checking'
    })
    assert response2.status_code == 201  # Ensure account creation was successful

    # Now, attempt to list the accounts
    list_response = client.get('/accounts/list')

    # Assert the response status code
    assert list_response.status_code == 200

    # Assert the response data
    accounts = list_response.get_json()
    assert len(accounts) == 2  # We created 2 accounts

    # Check the details of the first account
    assert accounts[0]['user_id'] == 1
    assert accounts[0]['balance'] == 1000
    assert accounts[0]['account_type'] == 'savings'

    # Check the details of the second account
    assert accounts[1]['user_id'] == 2
    assert accounts[1]['balance'] == 500
    assert accounts[1]['account_type'] == 'checking'
