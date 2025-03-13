import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """کلاس پایه تنظیمات"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development-only')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'twitter_analyzer.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # تنظیمات API توییتر
    TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET', '')
    
    # تنظیمات جلسه
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
class DevelopmentConfig(Config):
    """تنظیمات محیط توسعه"""
    DEBUG = True
    
class TestingConfig(Config):
    """تنظیمات محیط تست"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
class ProductionConfig(Config):
    """تنظیمات محیط تولید"""
    DEBUG = False
    
    # در محیط تولید از متغیرهای محیطی استفاده می‌کنیم
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
# دیکشنری تنظیمات
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
