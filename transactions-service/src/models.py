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
    balance_after = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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


    def __repr__(self):
        return f'<Transaction {self.id}>'