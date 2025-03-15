"""
ماژول ترجمه و تبدیل داده‌های API توییتر

این ماژول شامل کلاس‌ها و توابعی برای استانداردسازی و تبدیل پاسخ‌های
دریافتی از API توییتر به ساختار داخلی استاندارد برنامه است.
"""

from datetime import datetime
import logging
import json
import re
from typing import Dict, List, Any, Optional, Union, Tuple

# تنظیم لاگر
logger = logging.getLogger("twitter.transformers")

class TwitterDataTransformer:
    """
    کلاس اصلی برای تبدیل داده‌های دریافتی از API توییتر به ساختار استاندارد داخلی
    """
    
    def __init__(self, logger=None):
        """
        مقداردهی اولیه ترنسفورمر با امکان تنظیم لاگر اختصاصی
        
        Args:
            logger: لاگر اختصاصی (اختیاری)
        """
        self.logger = logger or logging.getLogger("twitter.transformers")
    
    def transform_tweet(self, tweet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تبدیل داده‌های یک توییت به ساختار استاندارد داخلی
        
        این تابع، ساختارهای مختلف داده‌های توییت را شناسایی و به یک ساختار استاندارد تبدیل می‌کند.
        
        Args:
            tweet_data: دیکشنری شامل داده‌های توییت از API
            
        Returns:
            دیکشنری با ساختار استاندارد داخلی
        """
        if not isinstance(tweet_data, dict):
            self.logger.error(f"داده ورودی باید دیکشنری باشد، اما {type(tweet_data)} دریافت شد")
            raise ValueError(f"داده توییت باید دیکشنری باشد، اما {type(tweet_data)} دریافت شد")
        
        try:
            # ایجاد ساختار پایه توییت استاندارد
            standardized_tweet = {
                "tweet_id": self._extract_tweet_id(tweet_data),
                "text": self._extract_text(tweet_data),
                "full_text": self._extract_full_text(tweet_data),
                "created_at": self._parse_date(tweet_data.get("createdAt") or tweet_data.get("created_at")),
                "user": self._extract_user_info(tweet_data),
                "metrics": self._extract_metrics(tweet_data),
                "entities": self._extract_entities(tweet_data),
                "metadata": self._extract_metadata(tweet_data),
                "reply_info": self._extract_reply_info(tweet_data),
                "raw_entities": tweet_data.get("entities", {})
            }
            
            return standardized_tweet
            
        except Exception as e:
            self.logger.error(f"خطا در تبدیل داده‌های توییت: {str(e)}", exc_info=True)
            # بازگرداندن یک خروجی با حداقل داده‌های ضروری در صورت بروز خطا
            return {
                "tweet_id": self._extract_tweet_id(tweet_data) or "unknown",
                "text": tweet_data.get("text", ""),
                "created_at": None,
                "user": {"username": "unknown"},
                "metrics": {},
                "entities": {},
                "metadata": {"error": str(e)},
                "raw_entities": {}
            }
    
    def transform_tweets_batch(self, tweets_data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        تبدیل یک دسته از توییت‌ها به ساختار استاندارد
        
        این تابع ساختارهای متفاوت بازگشتی از API را مدیریت می‌کند:
        - لیست مستقیم توییت‌ها
        - دیکشنری با کلید "tweets"
        - دیکشنری با کلید "results" در داخل "tweets"
        
        Args:
            tweets_data: داده‌های توییت در یکی از فرمت‌های بالا
            
        Returns:
            لیست توییت‌ها با ساختار استاندارد
        """
        standardized_tweets = []
        
        try:
            # بررسی نوع داده ورودی و استخراج توییت‌ها
            tweets_list = self._extract_tweets_list(tweets_data)
            
            # تبدیل هر توییت به ساختار استاندارد
            for tweet in tweets_list:
                standardized_tweet = self.transform_tweet(tweet)
                standardized_tweets.append(standardized_tweet)
            
            return standardized_tweets
            
        except Exception as e:
            self.logger.error(f"خطا در تبدیل دسته توییت‌ها: {str(e)}", exc_info=True)
            return []
    
    def transform_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تبدیل داده‌های کاربر توییتر به ساختار استاندارد
        
        Args:
            user_data: دیکشنری شامل داده‌های کاربر از API
            
        Returns:
            دیکشنری با ساختار استاندارد داخلی برای کاربر
        """
        if not isinstance(user_data, dict):
            self.logger.error(f"داده کاربر باید دیکشنری باشد، اما {type(user_data)} دریافت شد")
            raise ValueError(f"داده کاربر باید دیکشنری باشد، اما {type(user_data)} دریافت شد")
        
        try:
            # اطلاعات پایه کاربر
            standardized_user = {
                "user_id": str(user_data.get("id", user_data.get("userId", ""))),
                "twitter_id": str(user_data.get("id_str", user_data.get("id", ""))),
                "username": user_data.get("userName", user_data.get("username", user_data.get("screen_name", ""))),
                "display_name": user_data.get("displayName", user_data.get("name", "")),
                "bio": user_data.get("description", user_data.get("bio", "")),
                "location": user_data.get("location", ""),
                "followers_count": int(user_data.get("followers", user_data.get("followers_count", 0))),
                "following_count": int(user_data.get("following", user_data.get("friends_count", 0))),
                "tweets_count": int(user_data.get("tweets", user_data.get("statuses_count", 0))),
                "profile_image_url": user_data.get("profileImageUrl", user_data.get("profile_image_url", "")),
                "verified": bool(user_data.get("isBlueVerified", user_data.get("verified", False))),
                "created_at": self._parse_date(user_data.get("created_at")) if "created_at" in user_data else None,
                "url": user_data.get("url", ""),
                "metadata": {
                    "protected": bool(user_data.get("protected", False)),
                    "listed_count": int(user_data.get("listed_count", 0)),
                    "language": user_data.get("lang", "")
                }
            }
            
            return standardized_user
            
        except Exception as e:
            self.logger.error(f"خطا در تبدیل داده‌های کاربر: {str(e)}", exc_info=True)
            # بازگرداندن یک خروجی با حداقل داده‌های ضروری در صورت بروز خطا
            return {
                "user_id": str(user_data.get("id", "")),
                "twitter_id": str(user_data.get("id", "")),
                "username": user_data.get("userName", user_data.get("username", "unknown")),
                "display_name": user_data.get("displayName", user_data.get("name", "")),
                "profile_image_url": "",
                "followers_count": 0,
                "metadata": {"error": str(e)}
            }
    
    def transform_users_batch(self, users_data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        تبدیل یک دسته از کاربران به ساختار استاندارد
        
        Args:
            users_data: دیکشنری یا لیستی از داده‌های کاربران
            
        Returns:
            لیست کاربران با ساختار استاندارد
        """
        standardized_users = []
        
        try:
            # استخراج لیست کاربران
            if isinstance(users_data, list):
                users_list = users_data
            elif isinstance(users_data, dict) and "users" in users_data:
                users_list = users_data["users"]
            else:
                self.logger.warning(f"ساختار داده‌های کاربران ناشناخته است: {type(users_data)}")
                return []
            
            # تبدیل هر کاربر به ساختار استاندارد
            for user in users_list:
                standardized_user = self.transform_user(user)
                standardized_users.append(standardized_user)
            
            return standardized_users
            
        except Exception as e:
            self.logger.error(f"خطا در تبدیل دسته کاربران: {str(e)}", exc_info=True)
            return []
    
    def _extract_tweets_list(self, data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        استخراج لیست توییت‌ها از انواع مختلف پاسخ API
        
        Args:
            data: داده‌های دریافتی از API
            
        Returns:
            لیست توییت‌ها
        """
        if isinstance(data, list):
            return data
            
        if isinstance(data, dict):
            # ساختار اول: {"tweets": [tweet1, tweet2, ...]}
            if "tweets" in data and isinstance(data["tweets"], list):
                return data["tweets"]
                
            # ساختار دوم: {"tweets": {"results": [tweet1, tweet2, ...]}}
            if "tweets" in data and isinstance(data["tweets"], dict) and "results" in data["tweets"]:
                return data["tweets"]["results"]
                
            # ساختار سوم: {"results": [tweet1, tweet2, ...]}
            if "results" in data and isinstance(data["results"], list):
                return data["results"]
                
            # ساختار چهارم: یک توییت تنها
            if "id" in data or "tweet_id" in data or "twitter_id" in data:
                return [data]
        
        self.logger.warning(f"ساختار داده‌های توییت ناشناخته: {type(data)}")
        return []
    
    def _extract_tweet_id(self, tweet_data: Dict[str, Any]) -> str:
        """
        استخراج شناسه توییت از فرمت‌های مختلف
        
        Args:
            tweet_data: داده‌های توییت
            
        Returns:
            شناسه توییت به صورت رشته
        """
        tweet_id = None
        
        # بررسی کلیدهای مختلف ممکن برای شناسه توییت
        for key in ["id", "id_str", "tweet_id", "tweetId", "twitter_id", "twitterId"]:
            if key in tweet_data and tweet_data[key]:
                tweet_id = str(tweet_data[key])
                break
        
        return tweet_id
    
    def _extract_text(self, tweet_data: Dict[str, Any]) -> str:
        """
        استخراج متن توییت
        
        Args:
            tweet_data: داده‌های توییت
            
        Returns:
            متن توییت
        """
        # بررسی کلیدهای مختلف برای متن توییت
        for key in ["text", "full_text", "tweet", "content"]:
            if key in tweet_data and tweet_data[key]:
                return tweet_data[key]
        
        return ""
    
    def _extract_full_text(self, tweet_data: Dict[str, Any]) -> str:
        """
        استخراج متن کامل توییت (برای توییت‌هایی که truncated هستند)
        
        Args:
            tweet_data: داده‌های توییت
            
        Returns:
            متن کامل توییت
        """
        # ابتدا full_text را بررسی می‌کنیم
        if "full_text" in tweet_data:
            return tweet_data["full_text"]
        
        # سپس extended_tweet.full_text را بررسی می‌کنیم
        if "extended_tweet" in tweet_data and "full_text" in tweet_data["extended_tweet"]:
            return tweet_data["extended_tweet"]["full_text"]
        
        # اگر توییت truncated نیست، همان text کافی است
        return self._extract_text(tweet_data)
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        تبدیل رشته تاریخ توییتر به شیء datetime
        
        این تابع فرمت‌های مختلف تاریخ را پشتیبانی می‌کند
        
        Args:
            date_str: رشته تاریخ
            
        Returns:
            شیء datetime یا None در صورت عدم موفقیت
        """
        if not date_str:
            return None
        
        # لیست فرمت‌های تاریخ رایج در API توییتر
        date_formats = [
            '%a %b %d %H:%M:%S +0000 %Y',  # Tue Mar 21 20:50:14 +0000 2023
            '%Y-%m-%dT%H:%M:%S.%fZ',       # 2023-03-21T20:50:14.000Z
            '%Y-%m-%dT%H:%M:%SZ',          # 2023-03-21T20:50:14Z
            '%Y-%m-%d %H:%M:%S',           # 2023-03-21 20:50:14
        ]
        
        # تلاش برای تبدیل تاریخ با فرمت‌های مختلف
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # تلاش برای تبدیل با datetime.fromisoformat
        try:
            # تبدیل Z به +00:00 برای سازگاری با fromisoformat
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            
            return datetime.fromisoformat(date_str)
        except (ValueError, AttributeError):
            pass
        
        # تبدیل تاریخ در فرمت RFC 3339 با استفاده از regex
        try:
            # مثلاً: "2023-08-23T15:30:45.123+03:00"
            rfc3339_pattern = r'(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})\.?\d*(?:Z|([+-]\d{2}:\d{2}))?'
            match = re.match(rfc3339_pattern, date_str)
            if match:
                date_part, time_part = match.groups()[0:2]
                return datetime.strptime(f"{date_part} {time_part}", '%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        
        # اگر همه روش‌ها شکست خوردند، لاگ می‌کنیم و None برمی‌گردانیم
        self.logger.warning(f"تبدیل تاریخ ناموفق بود: '{date_str}'")
        return None
    
    def _extract_user_info(self, tweet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        استخراج اطلاعات کاربر از توییت
        
        Args:
            tweet_data: داده‌های توییت
            
        Returns:
            دیکشنری اطلاعات کاربر
        """
        user_info = {}
        
        # بررسی ساختارهای مختلف برای اطلاعات کاربر
        if "author" in tweet_data and isinstance(tweet_data["author"], dict):
            author = tweet_data["author"]
            user_info = {
                "user_id": str(author.get("id", "")),
                "username": author.get("userName", author.get("username", "")),
                "display_name": author.get("displayName", author.get("name", "")),
                "profile_image_url": author.get("profileImageUrl", author.get("profile_image_url", "")),
                "verified": bool(author.get("isBlueVerified", author.get("verified", False)))
            }
        elif "user" in tweet_data and isinstance(tweet_data["user"], dict):
            user = tweet_data["user"]
            user_info = {
                "user_id": str(user.get("id", user.get("id_str", ""))),
                "username": user.get("screen_name", user.get("username", "")),
                "display_name": user.get("name", ""),
                "profile_image_url": user.get("profile_image_url_https", user.get("profile_image_url", "")),
                "verified": bool(user.get("verified", False))
            }
        
        # اطمینان از اینکه username با @ شروع نمی‌شود
        if "username" in user_info and user_info["username"].startswith('@'):
            user_info["username"] = user_info["username"][1:]
        
        return user_info
    
    def _extract_metrics(self, tweet_data: Dict[str, Any]) -> Dict[str, int]:
        """
        استخراج آمار توییت (لایک، ریتوییت و غیره)
        
        Args:
            tweet_data: داده‌های توییت
            
        Returns:
            دیکشنری آمار توییت
        """
        metrics = {
            "likes_count": 0,
            "retweets_count": 0,
            "replies_count": 0,
            "quotes_count": 0
        }
        
        # تعیین مقادیر با بررسی کلیدهای مختلف
        metrics_mapping = {
            "likes_count": ["likeCount", "favorite_count", "likes", "favoriteCount", "likesCount"],
            "retweets_count": ["retweetCount", "retweet_count", "retweets", "retweetsCount"],
            "replies_count": ["replyCount", "reply_count", "replies", "repliesCount"],
            "quotes_count": ["quoteCount", "quote_count", "quotes", "quotesCount"]
        }
        
        for metric_key, possible_keys in metrics_mapping.items():
            for key in possible_keys:
                if key in tweet_data:
                    try:
                        metrics[metric_key] = int(tweet_data[key])
                        break
                    except (ValueError, TypeError):
                        pass
        
        return metrics
    
    def _extract_entities(self, tweet_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        استخراج موجودیت‌های توییت (هشتگ‌ها، منشن‌ها، URL‌ها)
        
        Args:
            tweet_data: داده‌های توییت
            
        Returns:
            دیکشنری موجودیت‌های استخراج شده
        """
        entities = {
            "hashtags": [],
            "mentions": [],
            "urls": [],
            "media": []
        }
        
        # استخراج از بخش entities اگر موجود باشد
        tweet_entities = tweet_data.get("entities", {})
        
        # پردازش هشتگ‌ها
        if "hashtags" in tweet_entities and isinstance(tweet_entities["hashtags"], list):
            for hashtag in tweet_entities["hashtags"]:
                if isinstance(hashtag, dict) and "text" in hashtag:
                    text = hashtag["text"]
                    # اطمینان از اینکه با # شروع نمی‌شود
                    if text.startswith('#'):
                        text = text[1:]
                    entities["hashtags"].append({"text": text})
        
        # پردازش منشن‌ها
        if "user_mentions" in tweet_entities and isinstance(tweet_entities["user_mentions"], list):
            for mention in tweet_entities["user_mentions"]:
                if isinstance(mention, dict) and "screen_name" in mention:
                    username = mention["screen_name"]
                    # اطمینان از اینکه با @ شروع نمی‌شود
                    if username.startswith('@'):
                        username = username[1:]
                    entities["mentions"].append({
                        "username": username,
                        "user_id": str(mention.get("id", mention.get("id_str", "")))
                    })
        
        # پردازش URL‌ها
        if "urls" in tweet_entities and isinstance(tweet_entities["urls"], list):
            for url in tweet_entities["urls"]:
                if isinstance(url, dict):
                    entities["urls"].append({
                        "url": url.get("url", ""),
                        "expanded_url": url.get("expanded_url", url.get("url", "")),
                        "display_url": url.get("display_url", "")
                    })
        
        # پردازش رسانه‌ها
        if "media" in tweet_entities and isinstance(tweet_entities["media"], list):
            for media in tweet_entities["media"]:
                if isinstance(media, dict):
                    entities["media"].append({
                        "media_url": media.get("media_url_https", media.get("media_url", "")),
                        "type": media.get("type", ""),
                        "url": media.get("url", "")
                    })
        
        # استخراج مستقیم از متن اگر entities وجود نداشته باشد
        text = self._extract_text(tweet_data)
        
        # استخراج هشتگ‌ها از متن
        if not entities["hashtags"]:
            hashtags = re.findall(r'#(\w+)', text)
            entities["hashtags"] = [{"text": tag} for tag in hashtags]
        
        # استخراج منشن‌ها از متن
        if not entities["mentions"]:
            mentions = re.findall(r'@(\w+)', text)
            entities["mentions"] = [{"username": username} for username in mentions]
        
        return entities
    
    def _extract_metadata(self, tweet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        استخراج متادیتای توییت
        
        Args:
            tweet_data: داده‌های توییت
            
        Returns:
            دیکشنری متادیتا
        """
        metadata = {
            "lang": tweet_data.get("lang", tweet_data.get("language", "")),
            "source": tweet_data.get("source", ""),
            "possibly_sensitive": bool(tweet_data.get("possibly_sensitive", False)),
            "coordinates": tweet_data.get("coordinates", None),
            "place": tweet_data.get("place", None),
            "truncated": bool(tweet_data.get("truncated", False))
        }
        
        # اطلاعات نوع توییت
        metadata["is_retweet"] = bool(tweet_data.get("isRetweet", tweet_data.get("retweeted_status" is not None if "retweeted_status" in tweet_data else False)))
        metadata["is_reply"] = bool(tweet_data.get("isReply", tweet_data.get("in_reply_to_status_id") is not None if "in_reply_to_status_id" in tweet_data else False))
        metadata["is_quote"] = bool(tweet_data.get("isQuote", tweet_data.get("quoted_status_id") is not None if "quoted_status_id" in tweet_data else False))
        
        return metadata
    
    def _extract_reply_info(self, tweet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        استخراج اطلاعات پاسخ توییت
        
        Args:
            tweet_data: داده‌های توییت
            
        Returns:
            دیکشنری اطلاعات پاسخ
        """
        reply_info = {
            "in_reply_to_tweet_id": None,
            "in_reply_to_user_id": None,
            "in_reply_to_username": None
        }
        
        # اطلاعات پاسخ
        reply_keys_mapping = {
            "in_reply_to_tweet_id": ["in_reply_to_status_id", "in_reply_to_status_id_str", "inReplyToId", "replyToId"],
            "in_reply_to_user_id": ["in_reply_to_user_id", "in_reply_to_user_id_str", "inReplyToUserId", "replyToUserId"],
            "in_reply_to_username": ["in_reply_to_screen_name", "inReplyToUserName", "replyToUserName"]
        }
        
        for info_key, possible_keys in reply_keys_mapping.items():
            for key in possible_keys:
                if key in tweet_data and tweet_data[key]:
                    reply_info[info_key] = str(tweet_data[key])
                    break
        
        return reply_info