import hmac
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, abort, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

import config
from extensions import db, jwt, limiter
from models import User, Token

def create_app():
    app = Flask(__name__)
    app.config.from_object(config.Config)
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        db.create_all()

    def require_json(keys):
        data = request.get_json(force=True)
        for k in keys:
            if k not in data:
                abort(400, f"Missing {k}")
        return data

    def sign_server(payload):
        msg = "|".join(str(payload[k]) for k in sorted(payload))
        return hmac.new(app.config['HMAC_SERVER_KEY'].encode(),
                        msg.encode(), hashlib.sha256).hexdigest()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/register', methods=['POST'])
    @limiter.limit("5/minute")
    def register():
        data = require_json(['username', 'password'])
        if User.query.filter_by(username=data['username']).first():
            abort(400, 'User exists')
        public_id = str(uuid.uuid4())
        embedded_id = str(uuid.uuid4())
        user = User(
            username=data['username'],
            public_id=public_id,
            embedded_id=embedded_id,
            password_hash=generate_password_hash(data['password'])
        )
        db.session.add(user)
        db.session.commit()
        return jsonify(msg='Registered',
                       public_id=public_id,
                       embedded_id=embedded_id), 201

    @app.route('/add_money', methods=['POST'])
    def add_money():
        data = require_json(['username', 'amount'])
        user = User.query.filter_by(username=data['username']).first_or_404()
        user.balance += int(data['amount'])
        db.session.commit()
        return jsonify(msg='Balance updated', balance=user.balance)

    @app.route('/login', methods=['POST'])
    @limiter.limit("10/minute")
    def login():
        data = require_json(['username', 'password'])
        user = User.query.filter_by(username=data['username']).first_or_404()
        if not check_password_hash(user.password_hash, data['password']):
            abort(401, 'Bad credentials')
        token = create_access_token(identity=user.username)
        return jsonify(access_token=token)

    @app.route('/generate_master', methods=['POST'])
    @jwt_required()
    @limiter.limit("5/minute")
    def generate_master():
        data = require_json(['amount'])
        sender = get_jwt_identity()
        user = User.query.filter_by(username=sender).first_or_404()
        if user.balance < int(data['amount']):
            abort(400, 'Insufficient balance')
        user.balance -= int(data['amount'])

        now = datetime.now(timezone.utc)
        expiry = now + timedelta(seconds=app.config['TOKEN_EXPIRY_SECONDS'])
        payload = {
            'transaction_id': str(uuid.uuid4()),
            'amount': int(data['amount']),
            'expiry': expiry.isoformat(),
            'sender_username': sender,
            'sender_embedded_id': user.embedded_id
        }
        server_sig = sign_server(payload)

        token = Token(
            transaction_id=payload['transaction_id'],
            amount=payload['amount'],
            expiry=expiry,
            sender_username=sender,
            sender_embedded_id=user.embedded_id,
            server_signature=server_sig
        )
        db.session.add(token)
        db.session.commit()

        payload['server_signature'] = server_sig
        return jsonify(payload), 201

    @app.route('/redeem_token', methods=['POST'])
    @jwt_required()
    @limiter.limit("5/minute")
    def redeem_token():
        data = require_json([
            'transaction_id',
            'receiver_embedded_id',
            'server_signature',
            'local_signature'
        ])
        username = get_jwt_identity()
        token = Token.query.filter_by(transaction_id=data['transaction_id']).first_or_404()
        if token.redeemed:
            abort(400, 'Token already redeemed')
        if token.expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            abort(400, 'Token expired')
        # verify server signature pehla 
        server_payload = {
            'transaction_id': token.transaction_id,
            'amount': token.amount,
            'expiry': token.expiry.isoformat(),
            'sender_username': token.sender_username,
            'sender_embedded_id': token.sender_embedded_id
        }
        if data['server_signature'] != token.server_signature:
            abort(400, 'Invalid server signature')
        
        # fixed consistent expiry format colon ka dikkat in timezone offset
        expiry_str = token.expiry.replace(tzinfo=timezone.utc).isoformat()
        if expiry_str.endswith("+0000"):
            expiry_str = expiry_str[:-5] + "+00:00"
        
        msg = "|".join([
            token.transaction_id,
            str(token.amount),
            expiry_str,  
            token.sender_username,
            token.sender_embedded_id,
            data['receiver_embedded_id']
        ])
        
        expected_local = hmac.new(
            token.sender_embedded_id.encode(),
            msg.encode(), hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(data['local_signature'], expected_local):
            return jsonify(msg='Invalid local signature'), 400

        token.redeemed = True
        token.receiver_embedded_id = data['receiver_embedded_id']
        receiver = User.query.filter_by(embedded_id=data['receiver_embedded_id']).first_or_404()
        receiver.balance += token.amount
        db.session.commit()

        return jsonify(msg='Redeemed successfully', balance=receiver.balance)    
    return app


if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=5000)
