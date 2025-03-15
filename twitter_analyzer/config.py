import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """کلاس پایه تنظیمات"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development-only')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'twitter_analyzer.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # تنظیمات API توییتر
    TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', 'cf5800d7a52a4df89b5df7ffe1c7303d')
    TWITTER_CACHE_SIZE = int(os.environ.get('TWITTER_CACHE_SIZE', 1000))
    TWITTER_CACHE_TTL = int(os.environ.get('TWITTER_CACHE_TTL', 300))  # 5 دقیقه
    
    # تنظیمات جلسه
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # تنظیمات Flask-Admin
    FLASK_ADMIN_SWATCH = 'cerulean'
    
    # تنظیمات زمان‌بندی
    SCHEDULER_API_ENABLED = True
    SCHEDULER_ENABLED = False  # به صورت پیش‌فرض غیرفعال است


    # اضافه کردن به کلاس Config در فایل config.py
class Config:
    """کلاس پایه تنظیمات"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-development-only')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'twitter_analyzer.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # تنظیمات API توییتر
    TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', 'cf5800d7a52a4df89b5df7ffe1c7303d')
    TWITTER_CACHE_SIZE = int(os.environ.get('TWITTER_CACHE_SIZE', 1000))
    TWITTER_CACHE_TTL = int(os.environ.get('TWITTER_CACHE_TTL', 300))  # 5 دقیقه
    
    # تنظیمات جلسه
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # تنظیمات Flask-Admin
    FLASK_ADMIN_SWATCH = 'cerulean'
    
    # تنظیمات زمان‌بندی
    SCHEDULER_API_ENABLED = True
    SCHEDULER_ENABLED = False  # به صورت پیش‌فرض غیرفعال است
    
    # تنظیمات Anthropic API
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    ANTHROPIC_SCREENING_MODEL = os.environ.get('ANTHROPIC_SCREENING_MODEL', 'claude-3-5-haiku-20241022')
    ANTHROPIC_ANALYSIS_MODEL = os.environ.get('ANTHROPIC_ANALYSIS_MODEL', 'claude-3-5-haiku-20241022') 
    ANTHROPIC_REPORTING_MODEL = os.environ.get('ANTHROPIC_REPORTING_MODEL', 'claude-3-5-sonnet-20241022')
    MAX_BATCH_TEXTS = 20
    MAX_REPORT_TEXTS = 50
    
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
    SCHEDULER_ENABLED = True  # فعال کردن زمان‌بندی در محیط تولید
    
# دیکشنری تنظیمات
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}



