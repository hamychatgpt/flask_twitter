import os
import logging
from logging.handlers import RotatingFileHandler
import jdatetime
from flask import Flask, render_template
from flask_login import current_user

from .config import config_by_name
from .models import db
from .auth.utils import login_manager
from .twitter import twitter_api
from .extensions import migrate, bootstrap, scheduler, cache
from .utils.text_processor import PersianTextProcessor


def create_app(config_name='default'):
    """Application factory - ایجاد و پیکربندی اپلیکیشن Flask"""
    # ایجاد نمونه Flask
    app = Flask(__name__, instance_relative_config=True)
    
    # بارگذاری تنظیمات بر اساس نام ارائه شده
    app.config.from_object(config_by_name[config_name])
    
    # می‌توان تنظیمات اضافی را از یک فایل در پوشه instance بارگذاری کرد (اختیاری)
    app.config.from_pyfile('config.py', silent=True)
    
    # اطمینان از وجود پوشه instance
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    

    # پیکربندی پایگاه داده
    db.init_app(app)
    
    # پیکربندی سیستم کش
    cache.init_app(app, config={
        'CACHE_TYPE': app.config.get('CACHE_TYPE', 'SimpleCache'),
        'CACHE_DEFAULT_TIMEOUT': app.config.get('TWITTER_CACHE_TTL', 300)
    })

    # پیکربندی کتابخانه‌های جدید
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    
    # پیکربندی مدیریت ورود به سیستم
    login_manager.init_app(app)
    
    # مقداردهی اولیه افزونه TwitterAPI
    twitter_api.init_app(app)
    
    # ثبت بلوپرینت‌ها
    from .auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from .dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    from .api import api_bp
    app.register_blueprint(api_bp)
    
    # ثبت بلوپرینت جدید collector
    from .collector import collector_bp
    app.register_blueprint(collector_bp)
    
    # تنظیم Flask-Admin
    from .admin import init_app as init_admin
    init_admin(app)
    
    # ثبت مدیریت خطاها
    register_error_handlers(app)
    
    # پیکربندی لاگینگ
    configure_logging(app)
    
    # اضافه کردن تابعی برای در دسترس قرار دادن تاریخ شمسی و سایر توابع کمکی در قالب‌ها
    @app.context_processor
    def inject_helpers():
        """تزریق توابع و متغیرهای کمکی به قالب‌ها"""
        def jalali_date(date):
            """تبدیل تاریخ میلادی به شمسی"""
            if date:
                jdate = jdatetime.datetime.fromgregorian(datetime=date)
                return jdate.strftime('%Y/%m/%d')
            return ''
            
        return {
            'current_year': jdatetime.datetime.now().year,
            'jalali_date': jalali_date,
            'current_user': current_user
        }
    
    # پیکربندی و شروع زمان‌بندی
    scheduler.init_app(app)


    try:
        # بررسی وجود پردازشگر متن فارسی
        from .utils.text_processor import PersianTextProcessor
        
        # فقط اگر PersianTextProcessor در app.extensions نباشد، اضافه کن
        if hasattr(app, 'extensions') and 'persian_content_analyzer' not in app.extensions:
            text_processor = PersianTextProcessor()
            text_processor.init_app(app)
            app.logger.info("PersianTextProcessor initialized successfully")
    except ImportError:
        app.logger.warning("PersianTextProcessor not available. Continuing without it.")
        pass

# ثبت بلوپرینت analyzer
    from .analyzer import analyzer_bp
    app.register_blueprint(analyzer_bp)

    # راه‌اندازی analyzer
    from .analyzer.routes import init_app as init_analyzer
    init_analyzer(app)
    
    # ثبت بلوپرینت مانیتورینگ لحظه‌ای
    from .realtime import realtime_bp
    app.register_blueprint(realtime_bp)
    
    # راه‌اندازی Socket.IO
    from .realtime.socket import init_app as init_socket
    init_socket(app)
    
    # ثبت بلوپرینت گزارش‌گیری
    from .reports import reports_bp
    app.register_blueprint(reports_bp)
    
    # راه‌اندازی سرویس گزارش‌گیری
    from .reports.service import ReportingService
    reporting_service = ReportingService(app)
    
    # راه‌اندازی سرویس پردازش توییت‌ها
    from .services.tweet_processor import TweetProcessor
    tweet_processor = TweetProcessor(app)
    
    # شروع پردازش توییت‌ها در پس‌زمینه اگر فعال باشد
    if app.config.get('BACKGROUND_PROCESSING_ENABLED', False):
        interval = app.config.get('BACKGROUND_PROCESSING_INTERVAL', 300)
        tweet_processor.start_background_processing(interval_seconds=interval)
        app.logger.info(f"Started background tweet processing with interval: {interval} seconds")
    
    # اگر برنامه در حالت دیباگ اجرا می‌شود، یک نمونه TwitterStream ایجاد می‌کنیم
    if app.debug and app.config.get('TESTING_STREAM_ENABLED', False):
        from .realtime.stream import TwitterStream
        stream = TwitterStream()
        app.extensions['twitter_stream'] = stream
        
        # شروع ردیابی با کلمات کلیدی پیش‌فرض
        if app.config.get('AUTO_START_TRACKING', False):
            stream.start_tracking()
            app.logger.info(f"Auto-started tracking with keywords: {stream.tracking_keywords}")
    
    # فقط در محیط تولید یا وقتی آگاهانه زمان‌بندی را فعال می‌کنیم
    if app.config.get('SCHEDULER_ENABLED', False):
        scheduler.start()

    # فقط در محیط تولید یا وقتی آگاهانه زمان‌بندی را فعال می‌کنیم
    if app.config.get('SCHEDULER_ENABLED', False):
        scheduler.start()
    
    return app

# فانکشن‌های کمکی بدون تغییر
def register_error_handlers(app):
    """ثبت توابع مدیریت خطا"""
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html', title='صفحه یافت نشد'), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html', title='خطای سرور'), 500

def configure_logging(app):
    """پیکربندی سیستم لاگینگ"""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/twitter_analyzer.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Twitter Analyzer startup')

