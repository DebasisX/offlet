import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    HMAC_SERVER_KEY = os.getenv("HMAC_SERVER_KEY", "fallback-server-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///wallet.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TOKEN_EXPIRY_SECONDS = int(os.getenv("TOKEN_EXPIRY_SECONDS", "300"))
