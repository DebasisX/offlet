import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-super-secret')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///wallet.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HMAC_SECRET = os.getenv('HMAC_SECRET', 'hmac-super-secret')
    TOKEN_EXPIRY_SECONDS = 300  # tokens expire after 5 minutes
