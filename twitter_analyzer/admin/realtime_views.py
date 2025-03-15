from flask_admin import BaseView, expose
from flask import redirect, url_for, request, jsonify, render_template, current_app, flash
from flask_login import current_user
from wtforms import Form, StringField, BooleanField, IntegerField, validators
from ..models import db

class RealtimeMonitoringView(BaseView):
    """نمای مدیریت مانیتورینگ لحظه‌ای در پنل ادمین"""
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))
    
    @expose('/')
    def index(self):
        """صفحه اصلی مدیریت مانیتورینگ لحظه‌ای"""
        # بررسی وضعیت سرویس مانیتورینگ
        stream = current_app.extensions.get('twitter_stream')
        
        if stream:
            stream_status = {
                'is_running': stream.is_running,
                'tracking_keywords': stream.tracking_keywords
            }
        else:
            stream_status = {
                'is_running': False,
                'tracking_keywords': []
            }
        
        # دریافت تنظیمات فعلی
        current_settings = {
            'tracking_keywords': ', '.join(current_app.config.get('TRACKING_KEYWORDS', [])),
            'tracking_interval': current_app.config.get('TRACKING_INTERVAL_SECONDS', 60),
            'advanced_analysis_threshold': current_app.config.get('ADVANCED_ANALYSIS_THRESHOLD', 100)
        }
        
        return self.render(
            'admin/realtime/index.html',
            stream_status=stream_status,
            current_settings=current_settings
        )
    
    @expose('/start', methods=['POST'])
    def start_tracking(self):
        """شروع ردیابی"""
        keywords = request.form.get('keywords', '')
        
        # تبدیل رشته کلمات کلیدی به لیست
        keywords_list = [k.strip() for k in keywords.split(',') if k.strip()]
        
        # دریافت سرویس ردیابی
        if 'twitter_stream' not in current_app.extensions:
            from ..realtime.stream import TwitterStream
            stream = TwitterStream()
            current_app.extensions['twitter_stream'] = stream
        else:
            stream = current_app.extensions['twitter_stream']
        
        # شروع ردیابی
        if stream.start_tracking(keywords_list):
            flash(f'ردیابی با کلمات کلیدی {stream.tracking_keywords} شروع شد', 'success')
        else:
            flash('خطا در شروع ردیابی', 'error')
        
        return redirect(url_for('.index'))
    
    @expose('/stop', methods=['POST'])
    def stop_tracking(self):
        """توقف ردیابی"""
        if 'twitter_stream' in current_app.extensions:
            stream = current_app.extensions['twitter_stream']
            if stream.stop_tracking():
                flash('ردیابی متوقف شد', 'success')
            else:
                flash('خطا در توقف ردیابی', 'error')
        else:
            flash('سرویس ردیابی یافت نشد', 'error')
        
        return redirect(url_for('.index'))
    
    @expose('/settings', methods=['GET', 'POST'])
    def settings(self):
        """تنظیمات مانیتورینگ لحظه‌ای"""
        class SettingsForm(Form):
            default_keywords = StringField('کلمات کلیدی پیش‌فرض (جدا شده با کاما)', [validators.DataRequired()])
            tracking_interval = IntegerField('بازه زمانی بررسی (ثانیه)', [validators.NumberRange(min=10, max=3600)])
            analysis_threshold = IntegerField('آستانه امتیاز تعامل برای تحلیل پیشرفته', [validators.NumberRange(min=10)])
            auto_start = BooleanField('شروع خودکار ردیابی در زمان راه‌اندازی برنامه')
        
        # ایجاد فرم با مقادیر فعلی
        form = SettingsForm(request.form)
        
        if request.method == 'GET':
            form.default_keywords.data = ', '.join(current_app.config.get('TRACKING_KEYWORDS', []))
            form.tracking_interval.data = current_app.config.get('TRACKING_INTERVAL_SECONDS', 60)
            form.analysis_threshold.data = current_app.config.get('ADVANCED_ANALYSIS_THRESHOLD', 100)
            form.auto_start.data = current_app.config.get('AUTO_START_TRACKING', False)
        
        if request.method == 'POST' and form.validate():
            # دریافت مقادیر فرم
            default_keywords = [k.strip() for k in form.default_keywords.data.split(',') if k.strip()]
            tracking_interval = form.tracking_interval.data
            analysis_threshold = form.analysis_threshold.data
            auto_start = form.auto_start.data
            
            # ذخیره در تنظیمات برنامه - این تنظیمات فقط تا راه‌اندازی مجدد برنامه معتبر هستند
            current_app.config['TRACKING_KEYWORDS'] = default_keywords
            current_app.config['TRACKING_INTERVAL_SECONDS'] = tracking_interval
            current_app.config['ADVANCED_ANALYSIS_THRESHOLD'] = analysis_threshold
            current_app.config['AUTO_START_TRACKING'] = auto_start
            
            flash('تنظیمات با موفقیت ذخیره شد', 'success')
            
            # بررسی نیاز به راه‌اندازی مجدد سرویس ردیابی
            stream = current_app.extensions.get('twitter_stream')
            if stream and stream.is_running:
                flash('برای اعمال تنظیمات جدید، سرویس ردیابی باید مجدداً راه‌اندازی شود', 'warning')
                
            # اگر شروع خودکار فعال است و سرویس ردیابی خاموش است، آن را روشن می‌کنیم
            if auto_start and stream and not stream.is_running:
                stream.start_tracking(default_keywords)
                flash(f'ردیابی با کلمات کلیدی {stream.tracking_keywords} شروع شد', 'success')
            
            return redirect(url_for('.index'))
        
        return self.render('admin/realtime/settings.html', form=form)
    
    @expose('/stats')
    def stats(self):
        """آمار ردیابی لحظه‌ای"""
        # دریافت آمار از سرویس ردیابی
        stream = current_app.extensions.get('twitter_stream')
        
        if not stream:
            return jsonify({
                'status': 'error',
                'message': 'سرویس ردیابی یافت نشد'
            })
        
        # در این نسخه آمار واقعی نداریم، اما می‌توان در آینده اضافه کرد
        stats = {
            'is_running': stream.is_running,
            'tracking_keywords': stream.tracking_keywords,
            'uptime': 0,  # تنها نمونه‌ای برای API
            'tweets_processed': 0,
            'last_check_time': None
        }
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })