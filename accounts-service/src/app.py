import os
import sys

# Add the current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from models import db, Account

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)


@app.route('/accounts', methods=['POST'])
def create_account():
    data = request.json
    if not data or 'user_id' not in data or 'account_number' not in data or 'account_type' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    try:
        new_account = Account(
            user_id=data['user_id'],
            account_number=data['account_number'],
            account_type=data['account_type'],
            initial_balance=data.get('initial_balance', 0)  # Default to 0 if not provided
        )
        db.session.add(new_account)
        db.session.commit()
        return jsonify(new_account.serialize), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    account = Account.query.get(account_id)
    if account is None:
        return jsonify({'error': 'Account not found'}), 404
    return jsonify(account.serialize)

@app.route('/accounts', methods=['GET'])
def list_accounts():
    accounts = Account.query.all()
    return jsonify([account.serialize for account in accounts])

@app.route('/accounts/<int:account_id>/deposit', methods=['POST'])
def deposit(account_id):
    account = Account.query.get(account_id)
    if account is None:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.json
    if not data or 'amount' not in data:
        return jsonify({'error': 'Amount is required'}), 400
    
    amount = data['amount']
    if amount <= 0:
        return jsonify({'error': 'Deposit amount must be positive'}), 400

    try:
        account.deposit(amount)
        db.session.commit()
        return jsonify(account.serialize)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/accounts/<int:account_id>/withdraw', methods=['POST'])
def withdraw(account_id):
    account = Account.query.get(account_id)
    if account is None:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.json
    if not data or 'amount' not in data:
        return jsonify({'error': 'Amount is required'}), 400
    
    amount = data['amount']
    if amount <= 0:
        return jsonify({'error': 'Withdrawal amount must be positive'}), 400

    try:
        account.withdraw(amount)
        db.session.commit()
        return jsonify(account.serialize)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    account = Account.query.get(account_id)
    if account is None:
        return jsonify({'error': 'Account not found'}), 404
    db.session.delete(account)
    db.session.commit()
    return jsonify({'message': 'Account deleted successfully'}), 200

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)
