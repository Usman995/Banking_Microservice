from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, validates
from sqlalchemy import Enum
from datetime import datetime
from math import isinf


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)



class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(Enum('deposit', 'withdrawal', 'transfer', name='transaction_type'), nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50))
    tags =  db.Column(db.String(100))
    status = db.Column(Enum('pending', 'complete', 'failed'), default='complete')
    balance_after = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @validates('account_id')
    def validate_account_id(self, key, value):
        if value is None:
            raise ValueError("Account ID cannot be None")
        if not isinstance(value, int):
            raise ValueError("Account ID must be an integer")
        if value <= 0:
            raise ValueError("Account ID must be positive")
        if value > 2**31 - 1:  # Assuming 32-bit integer limit
            raise ValueError("Account ID is too large")
        return value


    @validates('type')
    def validate_type(self, key, value):
        if value not in ('deposit', 'withdrawal', 'transfer'):
            raise ValueError(f"Invalid transaction type: {value}")
        return value
    
    @validates('amount')
    def validate_amount(self, key, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Amount must be a number")
        
        if isinf(value):
            raise ValueError("Amount cannot be infinity")
        
        if value < 0:
            raise ValueError("Amount must be positive")
        
        return value

    @validates('status')
    def validate_status(self, key, status):
        valid_statuses = ['pending', 'completed', 'failed']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return status

    def __repr__(self):
        return f'<Transaction {self.id}>'