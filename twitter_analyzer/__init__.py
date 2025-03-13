import os
import logging
from logging.handlers import RotatingFileHandler
import jdatetime
from flask import Flask, render_template
from flask_login import current_user

from .config import config_by_name
from .models import db
from .auth.utils import login_manager
from .twitter import twitter_api  # اضافه کردن این خط

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
    
    # پیکربندی مدیریت ورود به سیستم
    login_manager.init_app(app)
    
    # مقداردهی اولیه افزونه TwitterAPI
    twitter_api.init_app(app)  # اضافه کردن این خط
    
    # ثبت بلوپرینت‌ها
    from .auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from .dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    from .api import api_bp
    app.register_blueprint(api_bp)
    
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
    
    # مسیر ساده برای آزمایش اولیه
    @app.route('/hello')
    def hello():
        return 'سلام، تحلیلگر توییتر!'
    
    # بازگرداندن اپلیکیشن پیکربندی شده
    return app

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

    # ثبت دستورات CLI 
    from .cli import init_app as init_cli
    init_cli(app)