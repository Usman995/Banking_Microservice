import os
import sys

# Add the current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from flask import Flask, jsonify, request, abort
import logging
from models import db, Transaction

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.json
    if not data or 'account_id' not in data or 'amount' not in data or 'type' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    if not isinstance(data['account_id'], int) or not isinstance(data['amount'], (int, float)) or not isinstance(data['type'], str):
        return jsonify({'error': 'Invalid input types'}), 400
    if data['type'] not in ['deposit', 'withdrawal', 'transfer']:
        return jsonify({'error': 'Invalid transaction type'}), 400
    try:
        logging.info(f'Creating transaction: {data}')
        transaction = Transaction(
            account_id=data['account_id'],
            amount=data['amount'],
            type=data['type'],
            description=data.get('description', ''),
            balance_after=data['balance_after']
        )
        logging.info(f'Transaction created: {transaction}')
        logging.info(f'Transaction balance after: {transaction.balance_after}')
        db.session.add(transaction)
        db.session.commit()
        return jsonify({'id': transaction.id, 'account_id': transaction.account_id, 'amount': transaction.amount, 'type': transaction.type, 'description': transaction.description, 'balance_after': transaction.balance_after, 'timestamp': transaction.timestamp}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)