# twitter_analyzer/models/alert.py
from . import db
from .mixins import CRUDMixin, TimestampMixin

class Alert(db.Model, CRUDMixin, TimestampMixin):
    """
    مدل هشدار برای تعریف و ثبت هشدارها
    """
    __tablename__ = 'alert'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    
    # نوع و شرایط هشدار
    rule_type = db.Column(db.String(50))  # keyword, sentiment, volume, mention
    condition = db.Column(db.String(50))  # more_than, less_than, equal, contains
    threshold = db.Column(db.Float)  # مقدار آستانه
    value = db.Column(db.Text)  # مقدار مورد بررسی
    
    # تنظیمات ارسال
    notify_via = db.Column(db.String(50), default='dashboard')  # dashboard, telegram, email
    notify_to = db.Column(db.Text)  # مقصد هشدارها (JSON)
    
    # وضعیت
    is_active = db.Column(db.Boolean, default=True)
    triggered_count = db.Column(db.Integer, default=0)
    last_triggered = db.Column(db.DateTime)
    
    # ارتباط با کاربر
    user_i