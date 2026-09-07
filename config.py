import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///vtu.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Admin credentials
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@vtu.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
