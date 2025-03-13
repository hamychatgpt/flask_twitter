from . import db
from .mixins import CRUDMixin, TimestampMixin

class Mention(db.Model, CRUDMixin, TimestampMixin):
    """
    مدل منشن برای ذخیره و تحلیل منشن‌ها
    """
    __tablename__ = 'mention'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    count = db.Column(db.Integer, default=1)  # تعداد استفاده
    
    # ارتباط با کاربر توییتر
    twitter_user_id = db.Column(db.Integer, db.ForeignKey('twitter_user.id'), nullable=True)
    twitter_user = db.relationship('TwitterUser', backref='mentions')
    
    def __repr__(self):
        return f'<Mention @{self.username}>'
    
    @classmethod
    def get_or_create(cls, username):
        """
        دریافت منشن موجود یا ایجاد منشن جدید
        """
        # حذف @ از ابتدای رشته اگر وجود داشته باشد
        if username.startswith('@'):
            username = username[1:]
        
        mention = cls.query.filter_by(username=username).first()
        if not mention:
            mention = cls.create(username=username)
        else:
            # افزایش شمارنده
            mention.count += 1
            mention.save()
        return mention