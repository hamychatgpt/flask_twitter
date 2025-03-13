from . import db
from .mixins import CRUDMixin, TimestampMixin

class Hashtag(db.Model, CRUDMixin, TimestampMixin):
    """
    مدل هشتگ برای ذخیره و تحلیل هشتگ‌ها
    """
    __tablename__ = 'hashtag'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(128), unique=True, nullable=False, index=True)
    count = db.Column(db.Integer, default=1)  # تعداد استفاده
    
    # آمارهای تحلیلی
    trend_score = db.Column(db.Float, default=0)  # امتیاز محبوبیت
    average_sentiment = db.Column(db.Float)  # میانگین احساسات
    
    def __repr__(self):
        return f'<Hashtag #{self.text}>'
    
    @classmethod
    def get_or_create(cls, text):
        """
        دریافت هشتگ موجود یا ایجاد هشتگ جدید
        """
        # حذف # از ابتدای رشته اگر وجود داشته باشد
        if text.startswith('#'):
            text = text[1:]
        
        hashtag = cls.query.filter_by(text=text).first()
        if not hashtag:
            hashtag = cls.create(text=text)
        else:
            # افزایش شمارنده
            hashtag.count += 1
            hashtag.save()
        return hashtag