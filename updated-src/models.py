from datetime import datetime
from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    public_id = db.Column(db.String(36), unique=True, nullable=False)
    embedded_id = db.Column(db.String(36), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Integer, default=0)

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(36), unique=True, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    expiry = db.Column(db.DateTime, nullable=False)
    sender_username = db.Column(db.String(80), nullable=False)
    sender_embedded_id = db.Column(db.String(36), nullable=False)
    receiver_embedded_id = db.Column(db.String(36), nullable=True)
    server_signature = db.Column(db.String(64), nullable=False)
    local_signature = db.Column(db.String(64), nullable=True)
    redeemed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
