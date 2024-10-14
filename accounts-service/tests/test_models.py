import os
import sys
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import app, db
from src.models import Account



@pytest.fixture
def db_session():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def db_session():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.mark.parametrize("user_id, account_number, account_type, initial_balance, expected_error", [
    (1, "ACC001", "savings", 1000, None),
    (2, "ACC002", "checking", 500, None),
    (3, "ACC003", "savings", 0, None),
    (-1, "ACC004", "savings", 100, "User ID must be a positive integer"),
    (1, "ACC005", "invalid", 100, "Invalid account type. Must be 'savings' or 'checking'"),
    (1, "ACC006", "savings", -100, "Balance must be a non-negative number"),
    (1, "ACC007", "savings", 10**10, "Balance is too large"),
])
def test_account_creation(db_session, user_id, account_number, account_type, initial_balance, expected_error):
    if expected_error:
        with pytest.raises(ValueError, match=expected_error):
            Account(user_id=user_id, account_number=account_number, account_type=account_type, initial_balance=initial_balance)
    else:
        account = Account(user_id=user_id, account_number=account_number, account_type=account_type, initial_balance=initial_balance)
        db.session.add(account)
        db.session.commit()
        assert account.id is not None
        assert account.user_id == user_id
        assert account.account_number == account_number
        assert account.account_type == account_type
        assert account.balance == initial_balance
        assert isinstance(account.created_at, datetime)
        assert isinstance(account.updated_at, datetime)
        assert account.is_active == True

def test_unique_account_number(db_session):
    # Create the first account
    account1 = Account(user_id=1, account_number="ACC001", account_type="savings", initial_balance=1000)
    db.session.add(account1)
    db.session.commit()

    # Attempt to create a second account with the same account number
    account2 = Account(user_id=2, account_number="ACC001", account_type="checking", initial_balance=500)
    db.session.add(account2)

    # Expect an IntegrityError when committing the second account
    with pytest.raises(IntegrityError):
        db.session.commit()

    # Rollback the session to clean up
    db.session.rollback()

@pytest.mark.parametrize("initial_balance, deposit_amount, expected_balance, expected_error", [
    (1000, 500, 1500, None),
    (1000, 0, None, "Deposit amount must be a positive number"),
    (1000, -100, None, "Deposit amount must be a positive number"),
    (1000, 10**10, None, "Balance is too large"),
])
def test_deposit(db_session, initial_balance, deposit_amount, expected_balance, expected_error):
    account = Account(user_id=1, account_number="ACC001", account_type="savings", initial_balance=initial_balance)
    db.session.add(account)
    db.session.commit()

    if expected_error:
        with pytest.raises(ValueError, match=expected_error):
            account.deposit(deposit_amount)
    else:
        account.deposit(deposit_amount)
        assert account.balance == expected_balance

@pytest.mark.parametrize("initial_balance, withdraw_amount, expected_balance, expected_error", [
    (1000, 500, 500, None),
    (1000, 0, None, "Withdrawal amount must be a positive number"),
    (1000, -100, None, "Withdrawal amount must be a positive number"),
    (1000, 1001, None, "Insufficient funds"),
])
def test_withdraw(db_session, initial_balance, withdraw_amount, expected_balance, expected_error):
    account = Account(user_id=1, account_number="ACC001", account_type="savings", initial_balance=initial_balance)
    db.session.add(account)
    db.session.commit()

    if expected_error:
        with pytest.raises(ValueError, match=expected_error):
            account.withdraw(withdraw_amount)
    else:
        account.withdraw(withdraw_amount)
        assert account.balance == expected_balance

def test_serialize(db_session):
    account = Account(user_id=1, account_number="ACC001", account_type="savings", initial_balance=1000)
    db.session.add(account)
    db.session.commit()

    serialized = account.serialize
    assert serialized['id'] == account.id
    assert serialized['user_id'] == 1
    assert serialized['account_number'] == "ACC001"
    assert serialized['account_type'] == "savings"
    assert serialized['balance'] == 1000
    assert 'created_at' in serialized
    assert 'updated_at' in serialized
    assert serialized['is_active'] == True

def test_updated_at_changes_on_update(db_session):
    account = Account(user_id=1, account_number="ACC001", account_type="savings", initial_balance=1000)
    db.session.add(account)
    db.session.commit()

    original_updated_at = account.updated_at

    account.deposit(100)
    db.session.commit()

    assert account.updated_at > original_updated_at
