import hmac, hashlib, uuid
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, abort, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import config
from extensions import db, jwt, limiter
from models import User, Token
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

def create_app():
    app = Flask(__name__)
    app.config.from_object(config.Config)
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        db.create_all()

    def compute_signature(payload):
        msg = "|".join(str(payload[k]) for k in sorted(payload) if k != 'signature')
        return hmac.new(app.config['HMAC_SECRET'].encode(), msg.encode(), hashlib.sha256).hexdigest()

    def require_json(keys):
        data = request.get_json(force=True)
        for k in keys:
            if k not in data: abort(400, f"Missing field: {k}")
        return data

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/register", methods=["POST"])
    @limiter.limit("5 per minute")
    def register():
        data = require_json(['username','password'])
        if User.query.filter_by(username=data['username']).first(): abort(400,'Username exists')
        user = User(username=data['username'], password_hash=generate_password_hash(data['password']))
        db.session.add(user); db.session.commit()
        return jsonify(msg="User registered"),201

    @app.route("/login", methods=["POST"])
    @limiter.limit("10 per minute")
    def login():
        data = require_json(['username','password'])
        user = User.query.filter_by(username=data['username']).first()
        if not user or not check_password_hash(user.password_hash,data['password']): abort(401,'Bad credentials')
        token = create_access_token(identity=user.username)
        return jsonify(access_token=token)

    @app.route("/balance", methods=["GET"])
    @jwt_required()
    def balance():
        user = User.query.filter_by(username=get_jwt_identity()).first()
        return jsonify(balance=user.balance)

    @app.route('/generate_token', methods=['POST'])
    @jwt_required()
    @limiter.limit("3 per minute")
    def generate_token():
        data = require_json(['receiver_id', 'amount'])
        amount = data['amount']

        # Validate amount
        if not isinstance(amount, int) or not (0 < amount <= 1000):
            abort(400, 'Amount must be integer between 1 and 1000')

        sender_username = get_jwt_identity()
        sender = User.query.filter_by(username=sender_username).first_or_404()

        if sender.balance < amount:
            abort(400, 'Insufficient balance')

        # Deduct balance
        sender.balance -= amount

        # Create token
        now = datetime.utcnow()
        expiry = now + timedelta(seconds=app.config['TOKEN_EXPIRY_SECONDS'])

        # Use datetime objects for DB, ISO strings for signature
        payload = {
            'transaction_id': str(uuid.uuid4()),
            'embedded_sender': str(uuid.uuid4()),
            'embedded_receiver': data['receiver_id'],
            'sender_id': sender.username,
            'receiver_id': data['receiver_id'],
            'amount': amount,
            'timestamp': now,
            'expiry': expiry
        }

        # Signature must use ISO strings
        sign_payload = {
            **payload,
            'timestamp': now.isoformat(),
            'expiry': expiry.isoformat()
        }

        signature = compute_signature(sign_payload)

        token = Token(**payload, signature=signature)
        db.session.add(token)
        db.session.commit()

        return jsonify({**sign_payload, 'signature': signature}), 201

    @app.route('/redeem_token', methods=['POST'])
    @jwt_required()
    @limiter.limit("5 per minute")
    def redeem_token():
        data = require_json(['transaction_id', 'signature'])
        user_username = get_jwt_identity()
        token = Token.query.filter_by(transaction_id=data['transaction_id']).first_or_404()

        if token.redeemed:
            abort(400, 'Token already redeemed')

        if token.receiver_id != user_username:
            abort(403, 'Not authorized to redeem')

        # FIXED: Use timezone-aware datetime
        now = datetime.utcnow()  # Naive datetime to match the model
        
        if now > token.expiry:
            abort(400, 'Token expired')

        # Verify signature
        sign_payload = {
            'transaction_id': token.transaction_id,
            'embedded_sender': token.embedded_sender,
            'embedded_receiver': token.embedded_receiver,
            'sender_id': token.sender_id,
            'receiver_id': token.receiver_id,
            'amount': token.amount,
            'timestamp': token.timestamp.isoformat(),
            'expiry': token.expiry.isoformat()
        }
        expected_sig = compute_signature(sign_payload)

        if not hmac.compare_digest(data['signature'], expected_sig):
            abort(400, 'Invalid signature')

        # Redeem the token
        token.redeemed = True
        receiver = User.query.filter_by(username=user_username).first()
        receiver.balance += token.amount
        db.session.commit()

        return jsonify({'msg': 'Token redeemed', 'new_balance': receiver.balance})
    return app

if __name__=="__main__":
    create_app().run(host='0.0.0.0',port=5000)
