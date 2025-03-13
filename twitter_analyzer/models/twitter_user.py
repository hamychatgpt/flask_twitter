from . import db
from .mixins import CRUDMixin, TimestampMixin

class TwitterUser(db.Model, CRUDMixin, TimestampMixin):
    """
    مدل کاربر توییتر برای ذخیره اطلاعات کاربران توییتر
    """
    __tablename__ = 'twitter_user'
    
    id = db.Column(db.Integer, primary_key=True)
    twitter_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(128))
    bio = db.Column(db.Text)
    location = db.Column(db.String(128))
    followers_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    tweets_count = db.Column(db.Integer, default=0)
    profile_image_url = db.Column(db.String(255))
    verified = db.Column(db.Boolean, default=False)
    twitter_created_at = db.Column(db.DateTime)  # تاریخ ایجاد حساب در توییتر
    
    # آمارهای تحلیلی
    influence_score = db.Column(db.Float, default=0)  # امتیاز تأثیرگذاری
    sentiment_tendency = db.Column(db.Float)  # گرایش احساسی (مثبت یا منفی)
    
    # روابط
    tweets = db.relationship('Tweet', backref='twitter_user', lazy='dynamic')
    
    def __repr__(self):
        return f'<TwitterUser @{self.username}>'

    @classmethod
    def get_or_create(cls, twitter_id, username, **kwargs):
        """
        دریافت کاربر موجود یا ایجاد کاربر جدید
        """
        user = cls.query.filter_by(twitter_id=twitter_id).first()
        if not user:
            user = cls.create(twitter_id=twitter_id, username=username, **kwargs)
        return user