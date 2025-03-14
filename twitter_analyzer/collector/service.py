import re
from datetime import datetime
from flask import current_app
from ..models import db
from ..models.tweet import Tweet
from ..models.hashtag import Hashtag
from ..models.mention import Mention
from ..models.collection import Collection, CollectionRule
from ..models.twitter_user import TwitterUser

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
            existing_tweet.likes_count = tweet_data.get('likeCount', tweet_data.get('like_count', 0))
            existing_tweet.retweets_count = tweet_data.get('retweetCount', tweet_data.get('retweet_count', 0))
            existing_tweet.replies_count = tweet_data.get('replyCount', tweet_data.get('reply_count', 0))
            existing_tweet.quotes_count = tweet_data.get('quoteCount', tweet_data.get('quote_count', 0))
            existing_tweet.collection_id = collection_id
            db.session.commit()
            return existing_tweet, False
        
        # Extract tweet text
        text = tweet_data.get('text', '')
        
        # Extract author information - handle different API response structures
        author = tweet_data.get('author', {})
        username = author.get('userName', author.get('username', ''))
        twitter_user_id = None
        
        # Find or create TwitterUser
        if username:
            # Get or create TwitterUser record
            twitter_user = TwitterUser.query.filter_by(username=username).first()
            if not twitter_user:
                # For twitter_id, use the id in author or username
                author_id = author.get('id', username)
                display_name = author.get('displayName', author.get('name', ''))
                profile_image_url = author.get('profileImageUrl', author.get('profilePicture', ''))
                
                twitter_user = TwitterUser(
                    twitter_id=str(author_id),
                    username=username,
                    display_name=display_name,
                    bio=author.get('description', ''),
                    location=author.get('location', ''),
                    followers_count=author.get('followers', 0),
                    following_count=author.get('following', 0),
                    profile_image_url=profile_image_url,
                    verified=author.get('isBlueVerified', author.get('verified', False))
                )
                db.session.add(twitter_user)
                db.session.flush()  # Get ID without committing
            
            twitter_user_id = twitter_user.id
        
        # Parse created_at date - handle different date formats
        created_at = None
        created_at_str = tweet_data.get('createdAt')
        
        if created_at_str:
            try:
                # Try standard Twitter format first
                created_at = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S +0000 %Y')
            except (ValueError, TypeError):
                try:
                    # Try ISO format
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    current_app.logger.warning(f"Could not parse date: {created_at_str}")
                    created_at = datetime.utcnow()
        else:
            created_at = datetime.utcnow()
        
        try:
            # Create new Tweet
            new_tweet = Tweet(
                twitter_id=str(tweet_id),
                text=text,
                full_text=tweet_data.get('full_text', text),
                twitter_created_at=created_at,
                likes_count=tweet_data.get('likeCount', tweet_data.get('like_count', 0)),
                retweets_count=tweet_data.get('retweetCount', tweet_data.get('retweet_count', 0)),
                replies_count=tweet_data.get('replyCount', tweet_data.get('reply_count', 0)),
                quotes_count=tweet_data.get('quoteCount', tweet_data.get('quote_count', 0)),
                language=tweet_data.get('lang', ''),
                source=tweet_data.get('source', ''),
                is_retweet=tweet_data.get('isRetweet', False),
                is_quote=tweet_data.get('isQuote', False), 
                is_reply=tweet_data.get('isReply', False),
                in_reply_to_tweet_id=tweet_data.get('inReplyToId'),
                collection_method=method,
                collection_query=query,
                collection_id=collection_id,
                twitter_user_id=twitter_user_id,
                has_media=bool(tweet_data.get('entities', {}).get('media')),
            )
            
            # Process media URLs if present
            media_entities = tweet_data.get('entities', {}).get('media', [])
            if media_entities:
                media_urls = [media.get('media_url_https') for media in media_entities if media.get('media_url_https')]
                new_tweet.set_media_urls(media_urls)
            
            # Process URLs if present
            url_entities = tweet_data.get('entities', {}).get('urls', [])
            if url_entities:
                urls = [url.get('expanded_url') for url in url_entities if url.get('expanded_url')]
                new_tweet.set_urls(urls)
            
            db.session.add(new_tweet)
            db.session.flush()
            
            current_app.logger.info(f"Created new tweet with ID: {tweet_id}")
            
            # Process hashtags and mentions
            hashtag_texts = self._extract_hashtags(text)
            hashtag_entities = tweet_data.get('entities', {}).get('hashtags', [])
            
            # Add hashtags from entities if available
            if hashtag_entities:
                for hashtag_entity in hashtag_entities:
                    hashtag_text = hashtag_entity.get('text')
                    if hashtag_text and hashtag_text not in hashtag_texts:
                        hashtag_texts.append(hashtag_text)
            
            # Process all hashtags
            for hashtag_text in hashtag_texts:
                hashtag = Hashtag.query.filter_by(text=hashtag_text).first()
                if not hashtag:
                    hashtag = Hashtag(text=hashtag_text)
                    db.session.add(hashtag)
                    db.session.flush()
                else:
                    hashtag.count += 1
                
                new_tweet.hashtags.append(hashtag)
            
            # Process mentions from text and entities
            mention_texts = self._extract_mentions(text)
            mention_entities = tweet_data.get('entities', {}).get('user_mentions', [])
            
            # Add mentions from entities if available
            if mention_entities:
                for mention_entity in mention_entities:
                    mention_text = mention_entity.get('screen_name')
                    if mention_text and mention_text not in mention_texts:
                        mention_texts.append(mention_text)
            
            # Process all mentions
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
            # Using the search_all_tweets method to get tweets with pagination
            current_app.logger.info(f"Searching tweets with keyword: {keyword}")
            
            # Get tweets using the search_all_tweets method which handles pagination
            tweets_list = self.twitter_api.search_all_tweets(
                query=keyword,
                query_type="Latest",
                max_tweets=max_tweets
            )
            
            current_app.logger.info(f"Found {len(tweets_list)} tweets matching keyword: {keyword}")
            
            # Process each tweet
            total_new = 0
            for tweet_data in tweets_list:
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
            # Using get_all_user_tweets to fetch tweets with pagination
            current_app.logger.info(f"Fetching tweets for user: {username}")
            
            # Fetch all tweets using the get_all_user_tweets method
            tweets_list = self.twitter_api.get_all_user_tweets(
                username=username,
                include_replies=True,
                max_tweets=max_tweets
            )
            
            current_app.logger.info(f"Found {len(tweets_list)} tweets for user: {username}")
            
            # Process each tweet
            total_new = 0
            for tweet_data in tweets_list:
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
            
    def collect_by_hashtag(self, hashtag, max_tweets=100):
        """جمع‌آوری توییت‌ها براساس هشتگ"""
        # تبدیل max_tweets به عدد صحیح اگر رشته باشد
        if isinstance(max_tweets, str):
            try:
                max_tweets = int(max_tweets)
            except ValueError:
                max_tweets = 100
        
        # اطمینان از اینکه max_tweets یک عدد معتبر است
        max_tweets = max(1, min(1000, max_tweets))
        
        # اضافه کردن # به ابتدای هشتگ اگر وجود نداشته باشد
        if not hashtag.startswith('#'):
            hashtag_query = f'#{hashtag}'
        else:
            hashtag_query = hashtag
            # حذف # برای نام مجموعه
            hashtag = hashtag[1:]
        
        # ایجاد جمع‌آوری جدید
        collection = Collection(
            name=f'هشتگ: {hashtag_query}',
            description=f'جمع‌آوری توییت‌ها با هشتگ {hashtag_query}',
            status='running',
            started_at=datetime.utcnow(),
            max_tweets=max_tweets
        )
        db.session.add(collection)
        
        # ایجاد قاعده جمع‌آوری
        rule = CollectionRule(
            collection=collection,
            rule_type='hashtag',
            value=hashtag
        )
        db.session.add(rule)
        db.session.commit()
        
        try:
            # Using the search_all_tweets method with a hashtag query
            current_app.logger.info(f"Searching tweets with hashtag: {hashtag_query}")
            
            tweets_list = self.twitter_api.search_all_tweets(
                query=hashtag_query,
                query_type="Latest",
                max_tweets=max_tweets
            )
            
            current_app.logger.info(f"Found {len(tweets_list)} tweets with hashtag: {hashtag_query}")
            
            # Process each tweet
            total_new = 0
            for tweet_data in tweets_list:
                _, is_new = self._process_tweet(tweet_data, collection.id, 'hashtag', hashtag)
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
                current_app.logger.warning(f"Collection completed but no new tweets were found. Hashtag: {hashtag_query}")
            
            return collection, total_new
        
        except Exception as e:
            current_app.logger.error(f"Error collecting tweets by hashtag: {str(e)}", exc_info=True)
            collection.status = 'failed'
            collection.finished_at = datetime.utcnow()
            db.session.commit()
            raise
            
    def collect_by_mentions(self, username, max_tweets=100):
        """جمع‌آوری توییت‌هایی که کاربر خاصی را منشن کرده‌اند"""
        # تبدیل max_tweets به عدد صحیح اگر رشته باشد
        if isinstance(max_tweets, str):
            try:
                max_tweets = int(max_tweets)
            except ValueError:
                max_tweets = 100
        
        # اطمینان از اینکه max_tweets یک عدد معتبر است
        max_tweets = max(1, min(1000, max_tweets))
        
        # حذف @ از ابتدای نام کاربری در صورت وجود
        if username.startswith('@'):
            username_clean = username[1:]
        else:
            username_clean = username
            username = f'@{username}'
        
        # ایجاد جمع‌آوری جدید
        collection = Collection(
            name=f'منشن‌های: {username}',
            description=f'جمع‌آوری توییت‌هایی که کاربر {username} را منشن کرده‌اند',
            status='running',
            started_at=datetime.utcnow(),
            max_tweets=max_tweets
        )
        db.session.add(collection)
        
        # ایجاد قاعده جمع‌آوری
        rule = CollectionRule(
            collection=collection,
            rule_type='mention',
            value=username_clean
        )
        db.session.add(rule)
        db.session.commit()
        
        try:
            # Using get_user_mentions to fetch mentions
            current_app.logger.info(f"Fetching mentions for user: {username}")
            
            # Fetch all mentions using the get_all_user_mentions method
            all_mentions = self.twitter_api.get_all_user_mentions(
                username=username_clean,
                max_mentions=max_tweets
            )
            
            current_app.logger.info(f"Found {len(all_mentions)} mentions for user: {username}")
            
            # Process each tweet
            total_new = 0
            for tweet_data in all_mentions:
                _, is_new = self._process_tweet(tweet_data, collection.id, 'mention', username_clean)
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
                current_app.logger.warning(f"Collection completed but no new tweets were found. Mentions: {username}")
            
            return collection, total_new
        
        except Exception as e:
            current_app.logger.error(f"Error collecting tweets by mentions: {str(e)}", exc_info=True)
            collection.status = 'failed'
            collection.finished_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def collect_list_tweets(self, list_id, max_tweets=100):
        """جمع‌آوری توییت‌های یک لیست"""
        # تبدیل max_tweets به عدد صحیح اگر رشته باشد
        if isinstance(max_tweets, str):
            try:
                max_tweets = int(max_tweets)
            except ValueError:
                max_tweets = 100
        
        # اطمینان از اینکه max_tweets یک عدد معتبر است
        max_tweets = max(1, min(1000, max_tweets))
        
        # ایجاد جمع‌آوری جدید
        collection = Collection(
            name=f'لیست: {list_id}',
            description=f'جمع‌آوری توییت‌های لیست با شناسه {list_id}',
            status='running',
            started_at=datetime.utcnow(),
            max_tweets=max_tweets
        )
        db.session.add(collection)
        
        # ایجاد قاعده جمع‌آوری
        rule = CollectionRule(
            collection=collection,
            rule_type='list',
            value=list_id
        )
        db.session.add(rule)
        db.session.commit()
        
        try:
            current_app.logger.info(f"Fetching tweets for list ID: {list_id}")
            
            # استفاده از یک متغیر برای ذخیره توییت‌ها
            all_tweets = []
            cursor = ""
            
            # جمع‌آوری توییت‌ها با صفحه‌بندی
            while len(all_tweets) < max_tweets:
                result = self.twitter_api.get_list_tweets(list_id=list_id, cursor=cursor)
                
                if "tweets" not in result:
                    break
                
                tweets_data = result["tweets"]
                
                # بررسی ساختار پاسخ
                if isinstance(tweets_data, list):
                    all_tweets.extend(tweets_data)
                elif isinstance(tweets_data, dict) and "results" in tweets_data:
                    all_tweets.extend(tweets_data["results"])
                else:
                    current_app.logger.warning(f"Unexpected tweets structure: {type(tweets_data)}")
                    break
                
                # بررسی صفحه بعدی
                if not result.get("has_next_page", False) or "next_cursor" not in result:
                    break
                
                cursor = result["next_cursor"]
            
            current_app.logger.info(f"Found {len(all_tweets)} tweets for list ID: {list_id}")
            
            # محدود کردن به حداکثر تعداد درخواست شده
            all_tweets = all_tweets[:max_tweets]
            
            # Process each tweet
            total_new = 0
            for tweet_data in all_tweets:
                _, is_new = self._process_tweet(tweet_data, collection.id, 'list', list_id)
                if is_new:
                    total_new += 1
            
            # Update collection status
            collection.status = 'completed'
            collection.finished_at = datetime.utcnow()
            collection.total_tweets = total_new
            db.session.commit()
            
            if total_new == 0:
                current_app.logger.warning(f"Collection completed but no new tweets were found. List ID: {list_id}")
            
            return collection, total_new
        
        except Exception as e:
            current_app.logger.error(f"Error collecting tweets from list: {str(e)}", exc_info=True)
            collection.status = 'failed'
            collection.finished_at = datetime.utcnow()
            db.session.commit()
            raise
            
    def collect_tweet_replies(self, tweet_id, max_tweets=100):
        """جمع‌آوری پاسخ‌های یک توییت"""
        # تبدیل max_tweets به عدد صحیح اگر رشته باشد
        if isinstance(max_tweets, str):
            try:
                max_tweets = int(max_tweets)
            except ValueError:
                max_tweets = 100
        
        # اطمینان از اینکه max_tweets یک عدد معتبر است
        max_tweets = max(1, min(1000, max_tweets))
        
        # ایجاد جمع‌آوری جدید
        collection = Collection(
            name=f'پاسخ‌های توییت: {tweet_id}',
            description=f'جمع‌آوری پاسخ‌های توییت با شناسه {tweet_id}',
            status='running',
            started_at=datetime.utcnow(),
            max_tweets=max_tweets
        )
        db.session.add(collection)
        
        # ایجاد قاعده جمع‌آوری
        rule = CollectionRule(
            collection=collection,
            rule_type='tweet_replies',
            value=tweet_id
        )
        db.session.add(rule)
        db.session.commit()
        
        try:
            # Using get_all_tweet_replies to fetch replies
            current_app.logger.info(f"Fetching replies for tweet ID: {tweet_id}")
            
            replies_list = self.twitter_api.get_all_tweet_replies(
                tweet_id=tweet_id,
                max_replies=max_tweets
            )
            
            current_app.logger.info(f"Found {len(replies_list)} replies for tweet ID: {tweet_id}")
            
            # Process each tweet
            total_new = 0
            for tweet_data in replies_list:
                _, is_new = self._process_tweet(tweet_data, collection.id, 'tweet_replies', tweet_id)
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
                current_app.logger.warning(f"Collection completed but no new tweets were found. Tweet replies: {tweet_id}")
            
            return collection, total_new
        
        except Exception as e:
            current_app.logger.error(f"Error collecting tweet replies: {str(e)}", exc_info=True)
            collection.status = 'failed'
            collection.finished_at = datetime.utcnow()
            db.session.commit()
            raise