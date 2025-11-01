"""
Production Configuration for Object Quest App
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # App settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'object-quest-secret-key-2025'
    
    # Database settings
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'data/leaderboard.db'
    
    # Leaderboard admin token
    LEADERBOARD_CLEAR_TOKEN = os.environ.get('LEADERBOARD_CLEAR_TOKEN') or 'objectquest-admin-2025'
    
    # SSL certificate paths
    SSL_CERT_FILE = os.environ.get('SSL_CERT_FILE') or 'cert.pem'
    SSL_KEY_FILE = os.environ.get('SSL_KEY_FILE') or 'key.pem'
    
    # Flask settings
    JSON_SORT_KEYS = False
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Enable CORS for development
    CORS_ORIGINS = ['http://localhost:5000', 'https://127.0.0.1:5000']

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{Config.DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}