import json
from . import db
from .mixins import CRUDMixin, TimestampMixin

# جدول‌های واسط برای روابط چندبه‌چند
hashtag_tweet = db.Table(
    'hashtag_tweet',
    db.Column('hashtag_id', db.Integer, db.ForeignKey('hashtag.id'), primary_key=True),
    db.Column('tweet_id', db.Integer, db.ForeignKey('tweet.id'), primary_key=True)
)

mention_tweet = db.Table(
    'mention_tweet',
    db.Column('mention_id', db.Integer, db.ForeignKey('mention.id'), primary_key=True),
    db.Column('tweet_id', db.Integer, db.ForeignKey('tweet.id'), primary_key=True)
)

class Tweet(db.Model, CRUDMixin, TimestampMixin):
    """
    مدل توییت برای ذخیره اطلاعات کامل توییت‌ها
    """
    __tablename__ = 'tweet'
    
    id = db.Column(db.Integer, primary_key=True)
    twitter_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    processed_text = db.Column(db.Text) 
    full_text = db.Column(db.Text)  # متن کامل در صورت وجود
    twitter_created_at = db.Column(db.DateTime, index=True)  # زمان انتشار در توییتر
    
    # اطلاعات آماری
    likes_count = db.Column(db.Integer, default=0)
    retweets_count = db.Column(db.Integer, default=0)
    replies_count = db.Column(db.Integer, default=0)
    quotes_count = db.Column(db.Integer, default=0)
    
    # ویژگی‌های متنی
    language = db.Column(db.String(10), index=True)
    source = db.Column(db.String(255))  # منبع ارسال
    
    # نوع توییت
    is_retweet = db.Column(db.Boolean, default=False)
    is_quote = db.Column(db.Boolean, default=False)
    is_reply = db.Column(db.Boolean, default=False)
    
    # ارتباطات
    original_tweet_id = db.Column(db.String(64), index=True)  # برای ریتوییت یا نقل قول
    in_reply_to_tweet_id = db.Column(db.String(64), index=True)
    in_reply_to_user_id = db.Column(db.String(64), index=True)
    
    # فراداده‌های جمع‌آوری
    collection_method = db.Column(db.String(20), index=True)  # keyword, username, scheduled
    collection_query = db.Column(db.String(255))  # کلمه کلیدی یا نام کاربری
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=True, index=True)
    
    # فیلترینگ و تحلیل
    is_filtered = db.Column(db.Boolean, default=False)
    filter_reason = db.Column(db.String(50))
    is_processed = db.Column(db.Boolean, default=False)
    processing_date = db.Column(db.DateTime)
    
    # محتوای اضافی
    has_media = db.Column(db.Boolean, default=False)
    media_urls = db.Column(db.Text)  # JSON string
    urls = db.Column(db.Text)  # JSON string
    
    # نتایج تحلیل‌ها
    sentiment = db.Column(db.String(10))  # positive, neutral, negative
    sentiment_score = db.Column(db.Float)  # امتیاز دقیق احساسات (-1 تا 1)
    
    # روابط
    twitter_user_id = db.Column(db.Integer, db.ForeignKey('twitter_user.id'), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    
    # روابط چندبه‌چند
    hashtags = db.relationship('Hashtag', secondary=hashtag_tweet, backref=db.backref('tweets', lazy='dynamic'))
    mentions = db.relationship('Mention', secondary=mention_tweet, backref=db.backref('tweets', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Tweet {self.twitter_id}>'
    
    def get_media_urls(self):
        """دریافت URL‌های رسانه به صورت لیست"""
        if not self.media_urls:
            return []
        try:
            return json.loads(self.media_urls)
        except:
            return []
    
    def set_media_urls(self, urls_list):
        """تنظیم URL‌های رسانه از لیست"""
        if isinstance(urls_list, list):
            self.media_urls = json.dumps(urls_list)
    
    def get_urls(self):
        """دریافت URL‌های متن به صورت لیست"""
        if not self.urls:
            return []
        try:
            return json.loads(self.urls)
        except:
            return []
    
    def set_urls(self, urls_list):
        """تنظیم URL‌های متن از لیست"""
        if isinstance(urls_list, list):
            self.urls = json.dumps(urls_list)
    
    @classmethod
    def get_or_create(cls, twitter_id, text, twitter_user_id, **kwargs):
        """
        دریافت توییت موجود یا ایجاد توییت جدید
        """
        tweet = cls.query.filter_by(twitter_id=twitter_id).first()
        if not tweet:
            tweet = cls.create(
                twitter_id=twitter_id, 
                text=text, 
                twitter_user_id=twitter_user_id,
                **kwargs
            )
        return tweet