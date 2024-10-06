from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////accounts.db'
db = SQLAlchemy(app)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Float, default=0.0)
    

@app.route('/accounts', methods=['POST'])
def create_account():
    data = request.json
    new_account = Account(user_id=data['user_id'], balance=data.get('balance', 0.0))
    db.session.add(new_account)
    db.session.commit()
    return jsonify({'id': new_account.id, 'user_id': new_account.user_id, 'balance': new_account.balance}), 201

@app.route('/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    account = Account.query.get_or_404(account_id)
    return jsonify({'id': account.id, 'user_id': account.user_id, 'balance': account.balance})

@app.route('/accounts/<int:account_id>/balance', methods=['PUT'])
def update_balance(account_id):
    account = Account.query.get_or_404(account_id)
    data = request.json
    account.balance = data['balance']
    db.session.commit()
    return jsonify({'id': account.id, 'user_id': account.user_id, 'balance': account.balance})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)