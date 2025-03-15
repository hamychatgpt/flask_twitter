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
    sentiment_analysis_method = db.Column(db.String(20))  # local, anthropic, hybrid
    sentiment_confidence = db.Column(db.Float)  # میزان اطمینان (0 تا 1)
    sentiment_details = db.Column(db.Text)  # جزئیات تحلیل (JSON)
    
    # آمار پیشرفته
    engagement_score = db.Column(db.Integer)  # امتیاز تعامل محاسبه شده
    virality_score = db.Column(db.Float)  # امتیاز ویروسی شدن (0 تا 1)
    has_ai_analysis = db.Column(db.Boolean, default=False)  # آیا تحلیل هوش مصنوعی انجام شده است
    
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
    
    def set_sentiment_details(self, details):
        """تنظیم جزئیات تحلیل احساسات به صورت JSON"""
        if details:
            self.sentiment_details = json.dumps(details)
    
    def get_sentiment_details(self):
        """دریافت جزئیات تحلیل احساسات به صورت دیکشنری"""
        if not self.sentiment_details:
            return {}
        try:
            return json.loads(self.sentiment_details)
        except:
            return {}
    
    def calculate_engagement_score(self):
        """محاسبه امتیاز تعامل براساس لایک، ریتوییت و پاسخ"""
        likes = self.likes_count or 0
        retweets = self.retweets_count or 0
        replies = self.replies_count or 0
        quotes = self.quotes_count or 0
        
        # فرمول محاسبه: لایک + (ریتوییت * 2) + (پاسخ * 3) + (نقل قول * 2)
        score = likes + (retweets * 2) + (replies * 3) + (quotes * 2)
        self.engagement_score = score
        
        return score
    
    def calculate_virality_score(self):
        """محاسبه امتیاز ویروسی شدن توییت (0 تا 1)"""
        engagement = self.engagement_score or self.calculate_engagement_score()
        
        # آستانه‌های ویروسی شدن
        thresholds = [10, 50, 100, 500, 1000, 5000, 10000]
        
        # محاسبه امتیاز از 0 تا 1
        for i, threshold in enumerate(thresholds):
            if engagement < threshold:
                # محاسبه خطی بین آستانه‌ها
                if i == 0:
                    score = engagement / threshold
                else:
                    prev_threshold = thresholds[i-1]
                    score = i/len(thresholds) + (engagement - prev_threshold) / (threshold - prev_threshold) / len(thresholds)
                break
        else:
            # بالاتر از همه آستانه‌ها
            score = 1.0
        
        self.virality_score = score
        return score
    
    def analyze_sentiment_with_local_processor(self, text_processor=None):
        """تحلیل احساسات با استفاده از پردازشگر محلی"""
        from flask import current_app
        
        # دریافت پردازشگر محلی
        if text_processor is None:
            if hasattr(current_app, 'extensions') and 'persian_content_analyzer' in current_app.extensions:
                text_processor = current_app.extensions['persian_content_analyzer']
            else:
                from ..utils.text_processor import PersianTextProcessor
                text_processor = PersianTextProcessor()
        
        # تحلیل احساسات
        result = text_processor.analyze_sentiment(self.text)
        sentiment, score, negative_words, positive_words = result
        
        # ذخیره نتایج
        self.sentiment = sentiment
        self.sentiment_score = score
        self.sentiment_analysis_method = 'local'
        self.sentiment_confidence = 0.7  # اطمینان پیش‌فرض برای تحلیل محلی
        
        # ذخیره جزئیات
        details = {
            'negative_words': negative_words,
            'positive_words': positive_words,
            'method': 'local'
        }
        self.set_sentiment_details(details)
        
        return sentiment
    
    def analyze_sentiment_with_ai(self, force=False):
        """تحلیل احساسات با استفاده از هوش مصنوعی"""
        from flask import current_app
        
        # بررسی وجود تحلیلگر هوش مصنوعی
        if not hasattr(current_app, 'extensions') or 'anthropic_analyzer' not in current_app.extensions:
            return None
        
        # دریافت تحلیلگر هوش مصنوعی
        ai_analyzer = current_app.extensions['anthropic_analyzer']
        
        try:
            # تحلیل با هوش مصنوعی
            result = ai_analyzer.analyze_sentiment(self.text, force_full_analysis=force)
            
            # ذخیره نتایج
            sentiment = result.get('sentiment', 'neutral')
            self.sentiment = sentiment
            self.sentiment_score = result.get('intensity', 0.5) * (1 if sentiment == 'positive' else -1 if sentiment == 'negative' else 0)
            self.sentiment_analysis_method = 'anthropic'
            self.sentiment_confidence = result.get('confidence', 0.8)
            
            # ذخیره جزئیات
            self.set_sentiment_details(result)
            self.has_ai_analysis = True
            
            return sentiment
            
        except Exception as e:
            if hasattr(current_app, 'logger'):
                current_app.logger.error(f"Error in AI sentiment analysis: {e}", exc_info=True)
            return None
        
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
            
            # محاسبه امتیاز تعامل
            if 'likes_count' in kwargs or 'retweets_count' in kwargs or 'replies_count' in kwargs:
                tweet.calculate_engagement_score()
                tweet.calculate_virality_score()
        
        return tweet