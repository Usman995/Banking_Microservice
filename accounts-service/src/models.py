from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from datetime import datetime

db = SQLAlchemy()

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)  # Ensure this is set to unique
    account_type = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    @validates('user_id')
    def validate_user_id(self, key, user_id):
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("User ID must be a positive integer")
        return user_id

    @validates('account_type')
    def validate_account_type(self, key, account_type):
        if account_type not in ['savings', 'checking']:
            raise ValueError("Invalid account type. Must be 'savings' or 'checking'")
        return account_type

    @validates('balance')
    def validate_balance(self, key, balance):
        if balance is None:
            balance = 0  # Default to 0 if None
        if not isinstance(balance, (int, float)) or balance < 0:
            raise ValueError("Balance must be a non-negative number")
        if balance > 10**9:  # Assuming 1 billion is too large
            raise ValueError("Balance is too large")
        return balance

    def __init__(self, user_id, account_number, account_type, initial_balance=0):
        self.user_id = user_id
        self.account_number = account_number
        self.account_type = account_type
        self.balance = initial_balance

    def deposit(self, amount):
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Deposit amount must be a positive number")
        new_balance = self.balance + amount
        if new_balance > 10**9:
            raise ValueError("Balance is too large")
        self.balance = new_balance
        self.updated_at = datetime.utcnow()

    def withdraw(self, amount):
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Withdrawal amount must be a positive number")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.updated_at = datetime.utcnow()

    @property
    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_number': self.account_number,
            'account_type': self.account_type,
            'balance': self.balance,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }
