import re
from datetime import datetime
from flask import current_app
from ..models import db
from ..models.tweet import Tweet
from ..models.hashtag import Hashtag
from ..models.mention import Mention
from ..models.collection import Collection, CollectionRule

class CollectorService:
    """سرویس جمع‌آوری توییت‌ها"""
    
    def __init__(self, twitter_api=None):
        # استفاده از نمونه پیش‌فرض TwitterAPI اگر نمونه خاصی ارائه نشده باشد
        from ..twitter import twitter_api as default_api
        self.twitter_api = twitter_api or default_api
    
    def _extract_hashtags(self, text):
        """استخراج هشتگ‌ها از متن"""
        return re.findall(r'#(\w+)', text)
    
    def _extract_mentions(self, text):
        """استخراج منشن‌ها از متن"""
        return re.findall(r'@(\w+)', text)
    
    def _process_tweet(self, tweet_data, collection_id, method, query):
        """پردازش و ذخیره یک توییت"""
        # بررسی وجود توییت در دیتابیس
        existing_tweet = Tweet.query.filter_by(tweet_id=tweet_data.get('id_str')).first()
        if existing_tweet:
            # به‌روزرسانی آمار توییت موجود
            existing_tweet.likes_count = tweet_data.get('favorite_count', 0)
            existing_tweet.retweets_count = tweet_data.get('retweet_count', 0)
            existing_tweet.collection_id = collection_id
            db.session.commit()
            return existing_tweet, False
        
        # تبدیل تاریخ توییتر به datetime
        created_at = None
        if 'created_at' in tweet_data:
            try:
                created_at = datetime.strptime(tweet_data['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
            except (ValueError, TypeError):
                created_at = datetime.utcnow()
        
        # استخراج متن توییت
        text = tweet_data.get('text') or tweet_data.get('full_text', '')
        
        # ایجاد توییت جدید
        new_tweet = Tweet(
            tweet_id=tweet_data.get('id_str'),
            text=text,
            username=tweet_data.get('user', {}).get('screen_name', ''),
            twitter_created_at=created_at,
            likes_count=tweet_data.get('favorite_count', 0),
            retweets_count=tweet_data.get('retweet_count', 0),
            language=tweet_data.get('lang'),
            source=tweet_data.get('source'),
            is_retweet='retweeted_status' in tweet_data,
            is_quote='quoted_status' in tweet_data,
            is_reply=tweet_data.get('in_reply_to_status_id_str') is not None,
            collection_method=method,
            collection_query=query,
            collection_id=collection_id
        )
        
        db.session.add(new_tweet)
        db.session.flush()  # گرفتن ID بدون commit
        
        # پردازش هشتگ‌ها
        hashtag_texts = self._extract_hashtags(text)
        
        for hashtag_text in hashtag_texts:
            hashtag = Hashtag.query.filter_by(text=hashtag_text).first()
            if not hashtag:
                hashtag = Hashtag(text=hashtag_text)
                db.session.add(hashtag)
                db.session.flush()
            else:
                hashtag.count += 1
                db.session.add(hashtag)
            
            new_tweet.hashtags.append(hashtag)
        
        # پردازش منشن‌ها
        mention_texts = self._extract_mentions(text)
        
        for mention_text in mention_texts:
            mention = Mention.query.filter_by(username=mention_text).first()
            if not mention:
                mention = Mention(username=mention_text)
                db.session.add(mention)
                db.session.flush()
            else:
                mention.count += 1
                db.session.add(mention)
            
            new_tweet.mentions.append(mention)
        
        db.session.commit()
        return new_tweet, True
    
    def collect_by_keyword(self, keyword, max_tweets=100):
        """جمع‌آوری توییت‌ها براساس کلمه کلیدی"""
        # ایجاد جمع‌آوری جدید
        collection = Collection(
            name=f'کلمه کلیدی: {keyword}',
            description=f'جمع‌آوری توییت‌ها با کلمه کلیدی {keyword}',
            status='running',
            started_at=datetime.utcnow(),
            max_tweets=max_tweets
        )
        db.session.add(collection)
        
        # ایجاد قاعده جمع‌آوری
        rule = CollectionRule(
            collection=collection,
            rule_type='keyword',
            value=keyword
        )
        db.session.add(rule)
        db.session.commit()
        
        try:
            # جستجوی توییت‌ها - با استفاده از متد موجود در TwitterAPI
            results = self.twitter_api.search_tweets(keyword)
            
            # پردازش نتایج
            total_new = 0
            
            # بررسی ساختار نتایج براساس پاسخ API
            if isinstance(results, dict) and 'tweets' in results and 'results' in results['tweets']:
                tweets_data = results['tweets']['results']
            elif isinstance(results, dict) and 'tweets' in results:
                tweets_data = results['tweets']
            else:
                tweets_data = []
                current_app.logger.error(f"Unexpected results structure: {results}")
            
            for tweet_data in tweets_data:
                _, is_new = self._process_tweet(tweet_data, collection.id, 'keyword', keyword)
                if is_new:
                    total_new += 1
                    
                # بررسی رسیدن به حداکثر تعداد
                if total_new >= max_tweets:
                    break
            
            # به‌روزرسانی وضعیت جمع‌آوری
            collection.status = 'completed'
            collection.finished_at = datetime.utcnow()
            collection.total_tweets = total_new
            db.session.commit()
            
            return collection, total_new
        
        except Exception as e:
            current_app.logger.error(f"Error collecting tweets by keyword: {str(e)}")
            collection.status = 'failed'
            collection.finished_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def collect_by_username(self, username, max_tweets=100):
        """جمع‌آوری توییت‌های یک کاربر"""
        # حذف @ از ابتدای نام کاربری در صورت وجود
        if username.startswith('@'):
            username = username[1:]
        
        # ایجاد جمع‌آوری جدید
        collection = Collection(
            name=f'کاربر: @{username}',
            description=f'جمع‌آوری توییت‌های کاربر @{username}',
            status='running',
            started_at=datetime.utcnow(),
            max_tweets=max_tweets
        )
        db.session.add(collection)
        
        # ایجاد قاعده جمع‌آوری
        rule = CollectionRule(
            collection=collection,
            rule_type='username',
            value=username
        )
        db.session.add(rule)
        db.session.commit()
        
        try:
            # دریافت توییت‌های کاربر - با استفاده از متد موجود در TwitterAPI
            results = self.twitter_api.get_user_tweets(username=username)
            
            # پردازش نتایج
            total_new = 0
            
            # بررسی ساختار نتایج براساس پاسخ API
            if isinstance(results, dict) and 'tweets' in results:
                tweets_data = results['tweets']
            else:
                tweets_data = []
                current_app.logger.error(f"Unexpected results structure: {results}")
            
            for tweet_data in tweets_data:
                _, is_new = self._process_tweet(tweet_data, collection.id, 'username', username)
                if is_new:
                    total_new += 1
                    
                # بررسی رسیدن به حداکثر تعداد
                if total_new >= max_tweets:
                    break
            
            # به‌روزرسانی وضعیت جمع‌آوری
            collection.status = 'completed'
            collection.finished_at = datetime.utcnow()
            collection.total_tweets = total_new
            db.session.commit()
            
            return collection, total_new
        
        except Exception as e:
            current_app.logger.error(f"Error collecting tweets by username: {str(e)}")
            collection.status = 'failed'
            collection.finished_at = datetime.utcnow()
            db.session.commit()
            raise