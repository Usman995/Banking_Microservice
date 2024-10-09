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