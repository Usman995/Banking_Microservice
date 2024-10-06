from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Float, default=0.0)

@app.route('/accounts', methods=['POST'])
def create_account():
    data = request.json
    if not data or 'user_id' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    
    try:
        new_account = Account(user_id=data['user_id'], balance=data.get('initial_balance', 0.0))
        db.session.add(new_account)
        db.session.commit()
        return jsonify({'id': new_account.id, 'user_id': new_account.user_id, 'balance': new_account.balance}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    account = Account.query.get_or_404(account_id)
    return jsonify({'id': account.id, 'user_id': account.user_id, 'balance': account.balance})

@app.route('/accounts/<int:account_id>/balance', methods=['PUT'])
def update_balance(account_id):
    account = Account.query.get_or_404(account_id)
    data = request.json
    if not data or 'balance' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    
    try:
        account.balance = data['balance']
        db.session.commit()
        return jsonify({'id': account.id, 'user_id': account.user_id, 'balance': account.balance})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def init_db():
    db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)
else:
    init_db()