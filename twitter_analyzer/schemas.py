from .extentions import ma
from .models.tweet import Tweet
from .models.twitter_user import TwitterUser
from .models.hashtag import Hashtag
from .models.mention import Mention
from .models.collection import Collection, CollectionRule

class TwitterUserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TwitterUser
        exclude = ('created_at', 'updated_at')

class HashtagSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Hashtag
        exclude = ('created_at', 'updated_at')

class MentionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mention
        exclude = ('created_at', 'updated_at')

class TweetSchema(ma.SQLAlchemyAutoSchema):
    twitter_user = ma.Nested(TwitterUserSchema, exclude=('id',))
    hashtags = ma.Nested(HashtagSchema, many=True, exclude=('id',))
    mentions = ma.Nested(MentionSchema, many=True, exclude=('id',))
    
    class Meta:
        model = Tweet
        exclude = ('created_at', 'updated_at')

class CollectionRuleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CollectionRule
        exclude = ('created_at', 'updated_at')

class CollectionSchema(ma.SQLAlchemyAutoSchema):
    rules = ma.Nested(CollectionRuleSchema, many=True)
    
    class Meta:
        model = Collection
        exclude = ('created_at', 'updated_at')

# تعریف نمونه‌های Schema
tweet_schema = TweetSchema()
tweets_schema = TweetSchema(many=True)
twitter_user_schema = TwitterUserSchema()
twitter_users_schema = TwitterUserSchema(many=True)
collection_schema = CollectionSchema()
collections_schema = CollectionSchema(many=True)