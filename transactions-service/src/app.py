import os
import sys

# Add the current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from flask import Flask, jsonify, request, abort
from sqlalchemy.exc import DataError
from flask_migrate import Migrate
import logging
from models import db, Transaction

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.json
    try:
        logging.info(f'Creating transaction: {data}')
        transaction = Transaction(
            account_id=data['account_id'],
            amount=data['amount'],
            type=data['type'],
            description=data.get('description', ''),
            balance_after=data['balance_after']
        )
        logging.info(f'Transaction created: {transaction.id}')
        logging.info(f'Transaction balance after: {transaction.balance_after}')
        db.session.add(transaction)
        db.session.commit()
        return jsonify({'id': transaction.id, 'account_id': transaction.account_id, 'amount': transaction.amount, 'type': transaction.type, 'description': transaction.description, 'balance_after': transaction.balance_after, 'timestamp': transaction.timestamp}), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except DataError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f'Unexpected error: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    try:
        # Convert to integer
        transaction_id = int(transaction_id)
        logging.info("Transaction id is %s", transaction_id)
        if transaction_id <= 0:
            abort(400, description="Invalid transaction ID")
    except ValueError:
        abort(400, description="Invalid transaction ID")

    transaction = Transaction.query.get(transaction_id)
    if transaction is None:
        abort(404, description="Transaction not found")

    return jsonify({
        'id': transaction.id,
        'account_id': transaction.account_id,
        'amount': transaction.amount,
        'type': transaction.type,
        'description': transaction.description,
        'balance_after': transaction.balance_after,
        'timestamp': transaction.timestamp
    })



@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e.description)), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify(error=str(e.description)), 404
    


def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)