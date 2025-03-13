# twitter_analyzer/models/sentiment.py
from . import db
from .mixins import CRUDMixin, TimestampMixin

class SentimentAnalysis(db.Model, CRUDMixin, TimestampMixin):
    """
    مدل تحلیل احساسات برای ذخیره نتایج تحلیل لحن توییت‌ها
    """
    __tablename__ = 'sentiment_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), index=True)
    tweet = db.relationship('Tweet', backref='sentiment_analyses')
    
    # نوع تحلیل و نتایج
    analyzer = db.Column(db.String(50))  # نام الگوریتم یا مدل (e.g., 'claude', 'basic', etc.)
    sentiment = db.Column(db.String(20))  # positive, negative, neutral, mixed
    score = db.Column(db.Float)  # امتیاز (-1 تا 1)
    confidence = db.Column(db.Float)  # درصد اطمینان (0 تا 1)
    
    # جزئیات تحلیل
    details = db.Column(db.Text)  # جزئیات بیشتر (JSON)
    
    def __repr__(self):
        return f'<SentimentAnalysis {self.sentiment}:{self.score} for tweet {self.tweet_id}>'