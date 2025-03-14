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
        # Log the tweet data structure for debugging
        current_app.logger.debug(f"Processing tweet data: {str(tweet_data)[:200]}...")
        
        if not isinstance(tweet_data, dict):
            current_app.logger.error(f"Expected dict for tweet_data, got {type(tweet_data)}")
            return None, False
        
        # Extract tweet ID
        tweet_id = tweet_data.get('id')
        if not tweet_id:
            current_app.logger.error(f"No 'id' field in tweet data")
            return None, False
        
        # Check if tweet already exists
        existing_tweet = Tweet.query.filter_by(twitter_id=str(tweet_id)).first()
        if existing_tweet:
            current_app.logger.debug(f"Tweet {tweet_id} already exists, updating stats")
            # Update existing tweet stats
            existing_tweet.likes_count = tweet_data.get('likeCount', 0)
            existing_tweet.retweets_count = tweet_data.get('retweetCount', 0)
            existing_tweet.collection_id = collection_id
            db.session.commit()
            return existing_tweet, False
        
        # Extract tweet text
        text = tweet_data.get('text', '')
        
        # Extract author information
        author = tweet_data.get('author', {})
        username = author.get('userName', '')
        twitter_user_id = None
        
        # Find or create TwitterUser
        if username:
            from ..models.twitter_user import TwitterUser
            
            # Get or create TwitterUser record
            twitter_user = TwitterUser.query.filter_by(username=username).first()
            if not twitter_user:
                # برای twitter_id از id موجود در author یا از username استفاده می‌کنیم
                author_id = author.get('id', username)
                twitter_user = TwitterUser(
                    twitter_id=str(author_id),
                    username=username,
                    display_name=author.get('displayName', ''),
                    profile_image_url=author.get('profileImageUrl', '')
                )
                db.session.add(twitter_user)
                db.session.flush()  # Get ID without committing
            
            twitter_user_id = twitter_user.id
        
        # Parse created_at date
        created_at = None
        created_at_str = tweet_data.get('createdAt')
        if created_at_str:
            try:
                created_at = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S +0000 %Y')
            except (ValueError, TypeError):
                current_app.logger.warning(f"Could not parse date: {created_at_str}")
                created_at = datetime.utcnow()
        else:
            created_at = datetime.utcnow()
        
        try:
            # ایجاد توییت جدید - بدون username
            new_tweet = Tweet(
                twitter_id=str(tweet_id),
                text=text,
                twitter_created_at=created_at,
                likes_count=tweet_data.get('likeCount', 0),
                retweets_count=tweet_data.get('retweetCount', 0),
                replies_count=tweet_data.get('replyCount', 0),
                quotes_count=tweet_data.get('quoteCount', 0),
                language=tweet_data.get('lang', ''),
                source=tweet_data.get('source', ''),
                is_retweet=False,
                is_quote=False, 
                is_reply=tweet_data.get('isReply', False),
                collection_method=method,
                collection_query=query,
                collection_id=collection_id,
                twitter_user_id=twitter_user_id  # استفاده از twitter_user_id به جای username
            )
            
            db.session.add(new_tweet)
            db.session.flush()
            
            current_app.logger.info(f"Created new tweet with ID: {tweet_id}")
            
            # پردازش هشتگ‌ها و منشن‌ها بدون تغییر
            hashtag_texts = self._extract_hashtags(text)
            for hashtag_text in hashtag_texts:
                hashtag = Hashtag.query.filter_by(text=hashtag_text).first()
                if not hashtag:
                    hashtag = Hashtag(text=hashtag_text)
                    db.session.add(hashtag)
                    db.session.flush()
                else:
                    hashtag.count += 1
                
                new_tweet.hashtags.append(hashtag)
            
            mention_texts = self._extract_mentions(text)
            for mention_text in mention_texts:
                mention = Mention.query.filter_by(username=mention_text).first()
                if not mention:
                    mention = Mention(username=mention_text)
                    db.session.add(mention)
                    db.session.flush()
                else:
                    mention.count += 1
                
                new_tweet.mentions.append(mention)
            
            db.session.commit()
            return new_tweet, True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving tweet: {str(e)}", exc_info=True)
            return None, False
    
    def collect_by_keyword(self, keyword, max_tweets=100):
        """جمع‌آوری توییت‌ها براساس کلمه کلیدی"""
        # تبدیل max_tweets به عدد صحیح اگر رشته باشد
        if isinstance(max_tweets, str):
            try:
                max_tweets = int(max_tweets)
            except ValueError:
                max_tweets = 100  # مقدار پیش‌فرض اگر تبدیل با خطا مواجه شود
        
        # اطمینان از اینکه max_tweets یک عدد معتبر است
        max_tweets = max(1, min(1000, max_tweets))
        
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
            # According to API docs, use the advanced_search endpoint
            current_app.logger.info(f"Searching tweets with keyword: {keyword}")
            results = self.twitter_api.search_tweets(keyword)
            
            # Log the overall response structure
            current_app.logger.debug(f"API response type: {type(results)}")
            if isinstance(results, dict):
                current_app.logger.debug(f"API response keys: {list(results.keys())}")
            
            # Process results - handling the API structure
            total_new = 0
            tweets_data = []
            
            # According to the API docs structure
            if isinstance(results, dict):
                if 'tweets' in results:
                    if isinstance(results['tweets'], list):
                        tweets_data = results['tweets']
                        current_app.logger.info(f"Found {len(tweets_data)} tweets directly in 'tweets' list")
                    elif isinstance(results['tweets'], dict) and 'results' in results['tweets']:
                        tweets_data = results['tweets']['results']
                        current_app.logger.info(f"Found {len(tweets_data)} tweets in 'tweets.results' list")
                    else:
                        current_app.logger.warning(f"Unexpected 'tweets' structure: {type(results['tweets'])}")
                        
                        # Try to log detailed structure
                        if isinstance(results['tweets'], dict):
                            current_app.logger.debug(f"'tweets' keys: {list(results['tweets'].keys())}")
                else:
                    current_app.logger.warning(f"No 'tweets' key in response. Keys: {list(results.keys())}")
            else:
                current_app.logger.warning(f"Unexpected response type: {type(results)}")
            
            # Process each tweet
            for tweet_data in tweets_data:
                _, is_new = self._process_tweet(tweet_data, collection.id, 'keyword', keyword)
                if is_new:
                    total_new += 1
                    
                if total_new >= max_tweets:
                    break
            
            # Update collection status
            collection.status = 'completed'
            collection.finished_at = datetime.utcnow()
            collection.total_tweets = total_new
            db.session.commit()
            
            if total_new == 0:
                current_app.logger.warning(f"Collection completed but no new tweets were found. Query: {keyword}")
            
            return collection, total_new
        
        except Exception as e:
            current_app.logger.error(f"Error collecting tweets by keyword: {str(e)}", exc_info=True)
            collection.status = 'failed'
            collection.finished_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def collect_by_username(self, username, max_tweets=100):
        """جمع‌آوری توییت‌های یک کاربر"""
        # تبدیل max_tweets به عدد صحیح اگر رشته باشد
        if isinstance(max_tweets, str):
            try:
                max_tweets = int(max_tweets)
            except ValueError:
                max_tweets = 100  # مقدار پیش‌فرض اگر تبدیل با خطا مواجه شود
        
        # اطمینان از اینکه max_tweets یک عدد معتبر است
        max_tweets = max(1, min(1000, max_tweets))
        
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
            # According to API docs, use the user/last_tweets endpoint
            current_app.logger.info(f"Fetching tweets for user: {username}")
            results = self.twitter_api.get_user_tweets(username=username)
            tweets_data = []
            # بررسی ساختار response
            if 'tweets' in results:
                # ساختار استاندارد
                if isinstance(results['tweets'], list):
                    tweets_data = results['tweets']
                elif isinstance(results['tweets'], dict) and 'results' in results['tweets']:
                    tweets_data = results['tweets']['results']
            # ساختار جدید با data
            elif 'data' in results and isinstance(results['data'], list):
                tweets_data = results['data']
            
            # Log the structure for debugging
            current_app.logger.debug(f"API response type: {type(results)}")
            if isinstance(results, dict):
                current_app.logger.debug(f"API response keys: {list(results.keys())}")
            
            # Process results - handling the API structure
            total_new = 0
            tweets_data = []
            
            # According to the API docs structure
            if isinstance(results, dict):
                if 'tweets' in results:
                    if isinstance(results['tweets'], list):
                        tweets_data = results['tweets']
                        current_app.logger.info(f"Found {len(tweets_data)} tweets in 'tweets' list")
                    else:
                        current_app.logger.warning(f"Unexpected 'tweets' structure: {type(results['tweets'])}")
                else:
                    current_app.logger.warning(f"No 'tweets' key in response. Keys: {list(results.keys())}")
            else:
                current_app.logger.warning(f"Unexpected response type: {type(results)}")
            
            # Process each tweet
            for tweet_data in tweets_data:
                _, is_new = self._process_tweet(tweet_data, collection.id, 'username', username)
                if is_new:
                    total_new += 1
                    
                if total_new >= max_tweets:
                    break
            
            # Update collection status
            collection.status = 'completed'
            collection.finished_at = datetime.utcnow()
            collection.total_tweets = total_new
            db.session.commit()
            
            if total_new == 0:
                current_app.logger.warning(f"Collection completed but no new tweets were found. User: {username}")
            
            return collection, total_new
        
        except Exception as e:
            current_app.logger.error(f"Error collecting tweets by username: {str(e)}", exc_info=True)
            collection.status = 'failed'
            collection.finished_at = datetime.utcnow()
            db.session.commit()
            raise