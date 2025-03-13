from . import db
from .mixins import CRUDMixin, TimestampMixin

class Collection(db.Model, CRUDMixin, TimestampMixin):
    """
    مدل جمع‌آوری برای مدیریت فرآیندهای جمع‌آوری توییت‌ها
    """
    __tablename__ = 'collection'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    
    # آمار جمع‌آوری
    total_tweets = db.Column(db.Integer, default=0)
    filtered_tweets = db.Column(db.Integer, default=0)
    
    # تنظیمات پیشرفته
    max_tweets = db.Column(db.Integer)  # حداکثر تعداد توییت
    timeout_minutes = db.Column(db.Integer)  # حداکثر زمان اجرا
    
    # زمان‌بندی
    is_scheduled = db.Column(db.Boolean, default=False)
    schedule_type = db.Column(db.String(20))  # hourly, daily, weekly
    schedule_value = db.Column(db.String(50))  # مقدار زمان‌بندی
    next_run = db.Column(db.DateTime)
    last_run = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # روابط
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rules = db.relationship('CollectionRule', backref='collection', lazy='dynamic', cascade='all, delete-orphan')
    tweets = db.relationship('Tweet', backref='collection', lazy='dynamic')
    
    def __repr__(self):
        return f'<Collection {self.name}>'

class CollectionRule(db.Model, CRUDMixin, TimestampMixin):
    """
    مدل قاعده جمع‌آوری برای تعریف قواعد جمع‌آوری توییت‌ها
    """
    __tablename__ = 'collection_rule'
    
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), index=True)
    rule_type = db.Column(db.String(20), nullable=False)  # keyword, username, hashtag
    value = db.Column(db.String(255), nullable=False)
    include_replies = db.Column(db.Boolean, default=True)
    include_retweets = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10))
    
    def __repr__(self):
        return f'<CollectionRule {self.rule_type}:{self.value}>'