# twitter_analyzer/models/topic.py
from . import db
from .mixins import CRUDMixin, TimestampMixin

class Topic(db.Model, CRUDMixin, TimestampMixin):
    """
    مدل موضوع برای دسته‌بندی توییت‌ها براساس موضوع
    """
    __tablename__ = 'topic'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    description = db.Column(db.Text)
    
    # کلمات کلیدی مرتبط با موضوع (JSON)
    keywords = db.Column(db.Text)
    
    # ارتباط درختی موضوعات
    parent_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    subtopics = db.relationship('Topic', backref=db.backref('parent', remote_side=[id]))
    
    # آمار
    tweet_count = db.Column(db.Integer, default=0)
    average_sentiment = db.Column(db.Float)
    
    def __repr__(self):
        return f'<Topic {self.name}>'

class TopicTweet(db.Model, CRUDMixin, TimestampMixin):
    """
    جدول ارتباطی بین موضوعات و توییت‌ها
    """
    __tablename__ = 'topic_tweet'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), index=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), index=True)
    confidence = db.Column(db.Float, default=1.0)  # میزان اطمینان ارتباط
    
    # روابط
    topic = db.relationship('Topic', backref='topic_tweets')
    tweet = db.relationship('Tweet', backref='topic_tweets')
    
    __table_args__ = (db.UniqueConstraint('topic_id', 'tweet_id'),)
    
    def __repr__(self):
        return f'<TopicTweet {self.topic_id}:{self.tweet_id}>'