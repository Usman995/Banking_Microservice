import os
import sys
import pytest
from flask import json
from datetime import datetime


# Add the src directory to sys.path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_dir)

from app import app
from models import db,Transaction

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_create_transaction(client):
    # Test data
    transaction_data = {
        'account_id': 1,
        'amount': 100.00,
        'type': 'deposit',
        'description': 'Test deposit',
        'balance_after': 500.00
    }

    # Send POST request to create a new transaction
    response = client.post(
        '/transactions',
        data=json.dumps(transaction_data),
        content_type='application/json'
    )

    # Check response status code
    assert response.status_code == 201

    # Parse the response data
    data = json.loads(response.data)

    # Check the response data
    assert 'id' in data
    assert data['account_id'] == transaction_data['account_id']
    assert data['amount'] == transaction_data['amount']
    assert data['type'] == transaction_data['type']
    assert data['description'] == transaction_data['description']
    assert 'timestamp' in data
    assert 'balance_after' in data

    # Verify that the transaction was actually created in the database
    transaction = Transaction.query.get(data['id'])
    assert transaction is not None
    assert transaction.account_id == transaction_data['account_id']
    assert transaction.amount == transaction_data['amount']
    assert transaction.type == transaction_data['type']
    assert transaction.description == transaction_data['description']

@pytest.mark.parametrize("invalid_account_id, expected_status_code, expected_error_content", [
    (0, 400, "account id"),           # Account ID can't be zero
    (-1, 400, "account id"),          # Account ID can't be negative
    ('abc', 400, "account id"),       # Account ID must be a number, not a string
    (None, 400, "account id"),        # Account ID can't be None
    (1.5, 400, "account id"),         # Account ID must be an integer, not a float
    (2**31, 400, "account id"),       # Account ID too large (assuming 32-bit integer limit)
])
def test_create_transaction_with_invalid_account_id(client, invalid_account_id, expected_status_code, expected_error_content):
    transaction_data = {
        'account_id': invalid_account_id,
        'amount': 100.00,
        'type': 'deposit',
        'description': 'Test deposit',
        'balance_after': 500.00
    }

    response = client.post(
        '/transactions',
        data=json.dumps(transaction_data),
        content_type='application/json'
    )

    assert response.status_code == expected_status_code
    
    # Check that an error message is returned
    data = json.loads(response.data)
    assert 'error' in data
    assert expected_error_content.lower() in data['error'].lower()
    # Verify that no transaction was created in the database
    with app.app_context():
        transactions = Transaction.query.all()
        assert len(transactions) == 0



@pytest.mark.parametrize("transaction_data", [
    {
        'account_id': 1,
        'amount': 100.00,
        'type': 'deposit',
        'description': 'Test deposit',
        'balance_after': 500.00
    },
    {
        'account_id': 2,
        'amount': 50.00,
        'type': 'withdrawal',
        'description': 'Test withdrawal',
        'balance_after': 450.00
    },
    {
        'account_id': 3,
        'amount': 75.00,
        'type': 'transfer',
        'description': 'Test transfer',
        'balance_after': 525.00
    }
])
def test_get_transaction(client, transaction_data):
    # Send POST request to create a new transaction
    response = client.post(
        '/transactions',
        data=json.dumps(transaction_data),
        content_type='application/json'
    )
    assert response.status_code == 201
    created_transaction = response.get_json()

    # Send GET request to retrieve the created transaction
    response2 = client.get(f'/transactions/{created_transaction["id"]}')

    assert response2.status_code == 200
    retrieved_transaction = response2.get_json()

    # Assert that the retrieved transaction matches the created one
    assert retrieved_transaction['id'] == created_transaction['id']
    assert retrieved_transaction['account_id'] == transaction_data['account_id']
    assert retrieved_transaction['amount'] == transaction_data['amount']
    assert retrieved_transaction['type'] == transaction_data['type']
    assert retrieved_transaction['description'] == transaction_data['description']
    assert retrieved_transaction['balance_after'] == transaction_data['balance_after']
    assert 'timestamp' in retrieved_transaction

@pytest.mark.parametrize("invalid_id, expected_status", [
    ('abc', 400),   # string
    ('1.5', 400),   # float
    ('-1', 400),    # negative (treated as non-existent)
    ('0', 400),     # zero
])
def test_get_transaction_with_invalid_or_nonexistent_id(client, invalid_id, expected_status):
    response = client.get(f'/transactions/{invalid_id}')
    assert response.status_code == expected_status, f"Failed for ID: {invalid_id}"
    data = json.loads(response.data)
    assert 'error' in data
    if expected_status == 400:
        assert 'invalid transaction id' in data['error'].lower()
    elif expected_status == 404:
        assert 'transaction not found' in data['error'].lower()


def create_test_transactions(client):
    transaction_data = [
        {
            'account_id': 1,
            'amount': 100.00,
            'type': 'deposit',
            'description': 'Test deposit',
            'balance_after': 500.00
        },
        {
            'account_id': 2,
            'amount': 50.00,
            'type': 'withdrawal',
            'description': 'Test withdrawal',
            'balance_after': 450.00
        },
        {
            'account_id': 3,
            'amount': 75.00,
            'type': 'transfer',
            'description': 'Test transfer',
            'balance_after': 525.00
        }
    ]
    
    created_transactions = []
    for transaction in transaction_data:
        response = client.post(
            '/transactions',
            data=json.dumps(transaction),
            content_type='application/json'
        )
        assert response.status_code == 201
        created_transactions.append(response.get_json())
    
    return created_transactions

def test_list_transactions(client):
    # Create test transactions (assuming you have a function for this)
    create_test_transactions(client)

    response = client.get('/transactions')
    assert response.status_code == 200
    data = response.get_json()
    
    assert 'transactions' in data
    assert 'total' in data
    assert data['total'] == 3  # Expecting 3 transactions
    assert len(data['transactions']) == 3

    # Optionally, verify the contents of each transaction
    for transaction in data['transactions']:
        assert 'id' in transaction
        assert 'account_id' in transaction
        assert 'amount' in transaction
        assert 'type' in transaction
        assert 'description' in transaction
        assert 'balance_after' in transaction
        assert 'timestamp' in transaction

def test_pagination(client):
    create_test_transactions(client)

    response = client.get('/transactions?page=1&per_page=2')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'transactions' in data
    assert len(data['transactions']) == 2
    assert 'pagination' in data
    assert data['pagination']['total'] == 3
    assert data['pagination']['pages'] == 2
    assert data['pagination']['page'] == 1
    assert data['pagination']['per_page'] == 2

    response = client.get('/transactions?page=2&per_page=2')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'transactions' in data
    assert len(data['transactions']) == 1

@pytest.mark.parametrize("filter_param, expected_count", [
    ('account_id=1', 1),
    ('type=deposit', 1),
    ('type=withdrawal', 1),
    ('type=transfer', 1),
])
def test_filtering(client, filter_param, expected_count):
    create_test_transactions(client)

    response = client.get(f'/transactions?{filter_param}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'transactions' in data
    assert len(data['transactions']) == expected_count

    if 'account_id' in filter_param:
        account_id = int(filter_param.split('=')[1])
        assert all(t['account_id'] == account_id for t in data['transactions'])
    elif 'type' in filter_param:
        type_ = filter_param.split('=')[1]
        assert all(t['type'] == type_ for t in data['transactions'])

def test_sorting(client):
    create_test_transactions(client)

    response = client.get('/transactions?sort=amount&order=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'transactions' in data
    amounts = [t['amount'] for t in data['transactions']]
    assert amounts == sorted(amounts, reverse=True)

    response = client.get('/transactions?sort=amount&order=asc')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'transactions' in data
    amounts = [t['amount'] for t in data['transactions']]
    assert amounts == sorted(amounts)
