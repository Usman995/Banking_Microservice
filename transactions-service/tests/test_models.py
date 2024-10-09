import os
import sys
import pytest
from flask import json
from sqlalchemy.exc import DataError, IntegrityError
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


def test_create_transaction_with_negative_amount(test_app):
    with pytest.raises(ValueError):
        new_record = Transaction(
            account_id=1,
            amount=-100.0,  # Attempting to insert negative amount
            type='deposit',
            description='Test transaction',
            balance_after=900.0
        )
        db.session.add(new_record)
        db.session.commit()

@pytest.mark.parametrize("invalid_type", [
    'invalid_type',
    'DEPOSIT',
    'Withdrawal',
    '',
    None,
    123,
])
def test_create_transaction_with_invalid_type(test_app, invalid_type):
    with pytest.raises(ValueError):
        invalid_transaction = Transaction(
            account_id=1,
            amount=100,
            type=invalid_type,
            balance_after=1000
        )
        db.session.add(invalid_transaction)
        db.session.commit()

@pytest.mark.parametrize("valid_type", [
    'deposit',
    'withdrawal',
    'transfer',
])
def test_create_transaction_with_valid_type(test_app, valid_type):
    with test_app.app_context():
        valid_transaction = Transaction(
            account_id=1,
            amount=100,
            type=valid_type,
            balance_after=1000
        )
        db.session.add(valid_transaction)
        db.session.commit()
        assert valid_transaction.id is not None
        db.session.delete(valid_transaction)
        db.session.commit()

@pytest.mark.parametrize("invalid_amount", [
    'not a number',
    '',
    None,
    float('inf'),
    float('nan'),
])
def test_create_transaction_with_invalid_amount(test_app, invalid_amount):
    with pytest.raises((IntegrityError, ValueError)):
        invalid_transaction = Transaction(
            account_id=1,
            amount=invalid_amount,
            type='deposit',
            balance_after=1000
        )
        db.session.add(invalid_transaction)
        db.session.commit()

@pytest.mark.parametrize("valid_amount", [
    0,
    1,
    100.50,
    1e10,
])
def test_create_transaction_with_valid_amount(test_app, valid_amount):
    with test_app.app_context():
        valid_transaction = Transaction(
            account_id=1,
            amount=valid_amount,
            type='deposit',
            balance_after=1000
        )
        db.session.add(valid_transaction)
        db.session.commit()
        assert valid_transaction.id is not None
        db.session.delete(valid_transaction)
        db.session.commit()