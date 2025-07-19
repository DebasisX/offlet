from datetime import datetime
from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Integer, default=0)

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(36), unique=True, nullable=False)
    embedded_sender = db.Column(db.String(36), nullable=False)
    embedded_receiver = db.Column(db.String(36), nullable=False)
    sender_id = db.Column(db.String(80), nullable=False)
    receiver_id = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    expiry = db.Column(db.DateTime, nullable=False)
    signature = db.Column(db.String(64), nullable=False)
    redeemed = db.Column(db.Boolean, default=False)
