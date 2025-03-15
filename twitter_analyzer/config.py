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
    
    # تنظیمات مانیتورینگ لحظه‌ای
    TRACKING_KEYWORDS = os.environ.get('TRACKING_KEYWORDS', 'ایران,انتخابات,اقتصاد,دلار,بورس').split(',')
    TRACKING_INTERVAL_SECONDS = int(os.environ.get('TRACKING_INTERVAL_SECONDS', 60))
    ADVANCED_ANALYSIS_THRESHOLD = int(os.environ.get('ADVANCED_ANALYSIS_THRESHOLD', 100))
    
    # تنظیمات گزارش‌گیری
    ENABLE_MINUTE_REPORTS = os.environ.get('ENABLE_MINUTE_REPORTS', 'false').lower() == 'true'
    ENABLE_HOURLY_REPORTS = os.environ.get('ENABLE_HOURLY_REPORTS', 'true').lower() == 'true'
    ENABLE_DAILY_REPORTS = os.environ.get('ENABLE_DAILY_REPORTS', 'true').lower() == 'true'
    
    # تنظیمات پردازش توییت‌ها
    BACKGROUND_PROCESSING_ENABLED = os.environ.get('BACKGROUND_PROCESSING_ENABLED', 'false').lower() == 'true'
    BACKGROUND_PROCESSING_INTERVAL = int(os.environ.get('BACKGROUND_PROCESSING_INTERVAL', 300))
    TESTING_STREAM_ENABLED = os.environ.get('TESTING_STREAM_ENABLED', 'false').lower() == 'true'
    AUTO_START_TRACKING = os.environ.get('AUTO_START_TRACKING', 'false').lower() == 'true'
    
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



