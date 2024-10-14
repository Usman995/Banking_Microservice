# test_accounts.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.app import app, db
from src.models import Account
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
    (1, 1000, 'savings', 201, None),
    (2, 500, 'checking', 201, None),
    (3, 0, 'savings', 201, None),
    (4, -100, 'savings', 400, 'Balance must be a non-negative number'),
    (5, None, 'savings', 201, None),  # This should be valid and return 201
    ("abcd", 100, 'savings', 400, 'User ID must be a positive integer'),
    (6, 1000, 'invalid_type', 400, 'Invalid account type. Must be \'savings\' or \'checking\''),
    (7, 10**10, 'savings', 400, 'Balance is too large'),
])
def test_create_account(client, user_id, initial_balance, account_type, expected_status, expected_error):
    response = client.post('/accounts', json={
        'user_id': user_id,
        'initial_balance': initial_balance,
        'account_type': account_type,
        'account_number': f'ACC{user_id}'  # Add account number
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
        assert data['account_number'] == f'ACC{user_id}'
        assert 'created_at' in data
        assert 'updated_at' in data
        assert data['is_active'] == True

@pytest.mark.parametrize("account_id, expected_status, expected_balance, expected_account_type", [
    (1, 200, 1000, 'savings'),
    (999, 404, None, None),
])
def test_get_account(client, account_id, expected_status, expected_balance, expected_account_type):
    # Create an account if we're expecting a successful retrieval
    if expected_status == 200:
        client.post('/accounts', json={
            'user_id': account_id,
            'initial_balance': expected_balance,
            'account_type': expected_account_type,
            'account_number': f'ACC{account_id}'
        })

    get_response = client.get(f'/accounts/{account_id}')
    assert get_response.status_code == expected_status

    if expected_status == 200:
        data = get_response.get_json()
        assert data['id'] == account_id
        assert data['balance'] == expected_balance
        assert data['account_type'] == expected_account_type
        assert data['account_number'] == f'ACC{account_id}'
    else:
        error_data = get_response.get_json()
        assert 'error' in error_data
        assert error_data['error'] == 'Account not found'

@pytest.mark.parametrize("initial_balance, deposit_amount, expected_status, expected_balance", [
    (1000, 500, 200, 1500),
    (1000, 0, 400, 1000),
    (1000, -100, 400, 1000),
    (1000, 10**10, 400, 1000),
])
def test_deposit(client, initial_balance, deposit_amount, expected_status, expected_balance):
    # Create an account
    create_response = client.post('/accounts', json={
        'user_id': 1,
        'initial_balance': initial_balance,
        'account_type': 'savings',
        'account_number': 'ACC1'
    })
    account_id = create_response.get_json()['id']

    # Deposit to the account
    deposit_response = client.post(f"/accounts/{account_id}/deposit", json={'amount': deposit_amount})
    assert deposit_response.status_code == expected_status

    if expected_status == 200:
        updated_account = deposit_response.get_json()
        assert updated_account['balance'] == expected_balance
    else:
        error_data = deposit_response.get_json()
        assert 'error' in error_data

@pytest.mark.parametrize("initial_balance, withdraw_amount, expected_status, expected_balance", [
    (1000, 500, 200, 500),
    (1000, 0, 400, 1000),
    (1000, -100, 400, 1000),
    (1000, 1001, 400, 1000),
])
def test_withdraw(client, initial_balance, withdraw_amount, expected_status, expected_balance):
    # Create an account
    create_response = client.post('/accounts', json={
        'user_id': 1,
        'initial_balance': initial_balance,
        'account_type': 'savings',
        'account_number': 'ACC1'
    })
    account_id = create_response.get_json()['id']

    # Withdraw from the account
    withdraw_response = client.post(f"/accounts/{account_id}/withdraw", json={'amount': withdraw_amount})
    assert withdraw_response.status_code == expected_status

    if expected_status == 200:
        updated_account = withdraw_response.get_json()
        assert updated_account['balance'] == expected_balance
    else:
        error_data = withdraw_response.get_json()
        assert 'error' in error_data

def test_list_accounts(client):
    # Create some accounts
    client.post('/accounts', json={
        'user_id': 1,
        'initial_balance': 1000,
        'account_type': 'savings',
        'account_number': 'ACC1'
    })
    client.post('/accounts', json={
        'user_id': 2,
        'initial_balance': 500,
        'account_type': 'checking',
        'account_number': 'ACC2'
    })

    # List the accounts
    list_response = client.get('/accounts')
    assert list_response.status_code == 200

    accounts = list_response.get_json()
    assert len(accounts) == 2

    assert accounts[0]['user_id'] == 1
    assert accounts[0]['balance'] == 1000
    assert accounts[0]['account_type'] == 'savings'
    assert accounts[0]['account_number'] == 'ACC1'

    assert accounts[1]['user_id'] == 2
    assert accounts[1]['balance'] == 500
    assert accounts[1]['account_type'] == 'checking'
    assert accounts[1]['account_number'] == 'ACC2'

@pytest.mark.parametrize("account_id, expected_status", [
    (1, 200),
    (999, 404),
])
def test_delete_account(client, account_id, expected_status):
    if expected_status == 200:
        # Create an account to delete
        client.post('/accounts', json={
            'user_id': account_id,
            'initial_balance': 1000,
            'account_type': 'savings',
            'account_number': f'ACC{account_id}'
        })

    # Attempt to delete the account
    delete_response = client.delete(f'/accounts/{account_id}')
    assert delete_response.status_code == expected_status

    if expected_status == 200:
        # Verify the account no longer exists
        get_response = client.get(f'/accounts/{account_id}')
        assert get_response.status_code == 404
    else:
        error_data = delete_response.get_json()
        assert 'error' in error_data
        assert error_data['error'] == 'Account not found'
