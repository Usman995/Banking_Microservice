import os
import sys
import pytest
from flask import json
from datetime import datetime


# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import app, db
from src.models import Transaction

@pytest.fixture
def test_app():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_create_transaction(test_app):
    transaction = Transaction(
        account_id=1,
        amount=100.00,
        type='deposit',
        description='Test deposit',
        balance_after=500.00
    )
    db.session.add(transaction)
    db.session.commit()

    assert transaction.id is not None
    assert transaction.account_id == 1
    assert transaction.amount == 100.00
    assert transaction.type == 'deposit'
    assert transaction.description == 'Test deposit'
    assert transaction.balance_after == 500.00
    assert isinstance(transaction.timestamp, datetime)