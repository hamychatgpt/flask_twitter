from datetime import datetime
from . import db

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.String(64), unique=True, nullable=False)
    text = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sentiment = db.Column(db.String(10), default='neutral')  # 'positive', 'neutral', 'negative'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<Tweet {self.tweet_id}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'tweet_id': self.tweet_id,
            'text': self.text,
            'username': self.username,
            'created_at': self.created_at,
            'sentiment': self.sentiment
        }
