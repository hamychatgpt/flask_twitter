# twitter_analyzer/models/event.py
from . import db
from .mixins import CRUDMixin, TimestampMixin

class Event(db.Model, CRUDMixin, TimestampMixin):
    """
    مدل رویداد برای ثبت رویدادهای مهم
    """
    __tablename__ = 'event'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))  # news, announcement, crisis, etc.
    event_date = db.Column(db.DateTime, nullable=False, index=True)
    
    # اطلاعات تکمیلی
    source = db.Column(db.String(255))  # منبع رویداد
    importance = db.Column(db.Integer, default=3)  # اهمیت (1-5)
    
    # متا دیتا
    tags = db.Column(db.Text)  # برچسب‌ها (JSON)
    related_topics = db.Column(db.Text)  # موضوعات مرتبط (JSON)
    
    # تغییرات احساسات پس از رویداد
    sentiment_before = db.Column(db.Float)  # میانگین احساسات قبل از رویداد
    sentiment_after = db.Column(db.Float)  # میانگین احساسات بعد از رویداد
    volume_change = db.Column(db.Float)  # تغییر حجم توییت‌ها (درصد)
    
    def __repr__(self):
        return f'<Event {self.title}>'