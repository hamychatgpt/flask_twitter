from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import مدل‌ها برای اینکه Alembic بتواند آنها را پیدا کند
from .user import User
from .tweet import Tweet
from .twitter_user import TwitterUser
from .hashtag import Hashtag
from .mention import Mention
from .collection import Collection, CollectionRule