import requests
import time
import logging
import json
from urllib.parse import urljoin
from flask import current_app
from cachetools import TTLCache

class TwitterAPI:
    """
    رابط برای کار با API غیررسمی توییتر
    """
    
    def __init__(self, app=None):
        self.base_url = "https://api.twitterapi.io"
        self.session = None
        self.api_key = 'cf5800d7a52a4df89b5df7ffe1c7303d'
        self.cache = TTLCache(maxsize=1000, ttl=300)  # کش پیش‌فرض (5 دقیقه)
        self.logger = logging.getLogger("twitter_api")
        
        # اطلاعات rate limit
        self.rate_limit_remaining = 200
        self.rate_limit_reset = 0
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        مقداردهی اولیه افزونه با برنامه Flask
        """
        self.api_key = app.config.get('TWITTER_API_KEY')
        
        if not self.api_key:
            self.logger.warning("TWITTER_API_KEY not set in app config")
        
        # ایجاد یک session جدید برای درخواست‌ها
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": self.api_key})
        
        # تنظیم سایز و زمان کش از پیکربندی برنامه
        cache_size = app.config.get('TWITTER_CACHE_SIZE', 1000)
        cache_ttl = app.config.get('TWITTER_CACHE_TTL', 300)
        self.cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
        
        # تنظیم لاگر
        if app.config.get('DEBUG', False):
            self.logger.setLevel(logging.DEBUG)
        
        # ثبت افزونه در app.extensions
        app.extensions['twitter_api'] = self
        
        # ثبت تابع teardown برای پاکسازی منابع
        app.teardown_appcontext(self._teardown)
    
    def _teardown(self, exception):
        """
        پاکسازی منابع در پایان هر درخواست
        """
        if self.session:
            # بستن session برای آزادسازی منابع
            pass
    
    def _handle_rate_limit(self, response):
        """
        مدیریت اطلاعات rate limit از هدرهای پاسخ
        """
        if 'X-Rate-Limit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-Rate-Limit-Remaining'])
        
        if 'X-Rate-Limit-Reset' in response.headers:
            self.rate_limit_reset = int(response.headers['X-Rate-Limit-Reset'])
        
        # هشدار اگر به محدودیت نزدیک شده‌ایم
        if self.rate_limit_remaining < 10:
            self.logger.warning(f"Rate limit running low: {self.rate_limit_remaining} requests remaining")
            
            # صبر اگر خیلی به محدودیت نزدیک هستیم
            if self.rate_limit_remaining < 5:
                wait_time = max(0, self.rate_limit_reset - time.time())
                if wait_time > 0:
                    time.sleep(min(wait_time, 2))  # حداکثر 2 ثانیه صبر می‌کنیم
    
    def _request(self, method, endpoint, params=None, data=None, json=None, retry_count=3, cache_key=None):
        """
        انجام درخواست HTTP به API توییتر با مدیریت خطا و retry
        """
        # استفاده از کش اگر وجود داشته باشد
        if method == 'GET' and cache_key and cache_key in self.cache:
            self.logger.debug(f"Cache hit for key: {cache_key}")
            return self.cache[cache_key]
        
        url = urljoin(self.base_url, endpoint)
        
        for attempt in range(retry_count):
            try:
                self.logger.debug(f"Making {method} request to {url}")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    timeout=(3.05, 27)  # (connect timeout, read timeout)
                )
                
                # ثبت و مدیریت rate limit
                self._handle_rate_limit(response)
                
                # بررسی کد وضعیت
                if response.status_code == 429:  # Rate limit exceeded
                    wait_time = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                result = response.json()
                
                # ذخیره در کش برای درخواست‌های GET
                if method == 'GET' and cache_key:
                    self.cache[cache_key] = result
                
                return result
                
            except requests.exceptions.HTTPError as e:
                self.logger.error(f"HTTP error: {e}")
                
                if response.status_code == 400:
                    self.logger.error(f"Bad request: {response.text}")
                    return {"status": "error", "msg": "Bad request parameters"}
                elif response.status_code == 401:
                    self.logger.error("Authentication error")
                    return {"status": "error", "msg": "Invalid API key"}
                elif response.status_code == 404:
                    self.logger.error(f"Resource not found: {url}")
                    return {"status": "error", "msg": "Resource not found"}
                elif response.status_code >= 500:
                    if attempt < retry_count - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        self.logger.warning(f"Server error, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"Server error after {retry_count} attempts")
                        return {"status": "error", "msg": "Server error"}
                else:
                    return {"status": "error", "msg": str(e)}
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request exception: {e}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Request error: {e}, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Request failed after {retry_count} attempts: {e}")
                    return {"status": "error", "msg": "Connection error"}
        
        return {"status": "error", "msg": "Max retries exceeded"}

    # === متدهای API برای اطلاعات کاربر ===
    
    def get_user_info(self, username):
        """
        دریافت اطلاعات کاربر با نام کاربری
        
        Endpoint: GET /twitter/user/info
        """
        cache_key = f"user_info_{username}"
        return self._request(
            "GET", 
            "/twitter/user/info", 
            params={"userName": username},
            cache_key=cache_key
        )
    
    def get_user_batch_info(self, user_ids):
        """
        دریافت اطلاعات چند کاربر به صورت همزمان
        
        Endpoint: GET /twitter/user/batch_info_by_ids
        """
        if isinstance(user_ids, list):
            user_ids = ",".join(user_ids)
            
        cache_key = f"batch_users_{user_ids}"
        return self._request(
            "GET", 
            "/twitter/user/batch_info_by_ids", 
            params={"userIds": user_ids},
            cache_key=cache_key
        )
    
    def get_user_followers(self, username, cursor=""):
        """
        دریافت فالوورهای کاربر
        
        Endpoint: GET /twitter/user/followers
        """
        return self._request(
            "GET", 
            "/twitter/user/followers", 
            params={"userName": username, "cursor": cursor}
        )
    
    def get_user_followings(self, username, cursor=""):
        """
        دریافت افرادی که کاربر فالو کرده
        
        Endpoint: GET /twitter/user/followings
        """
        return self._request(
            "GET", 
            "/twitter/user/followings", 
            params={"userName": username, "cursor": cursor}
        )
    
    def get_user_tweets(self, user_id=None, username=None, include_replies=False, cursor=""):
        """
        دریافت آخرین توییت‌های کاربر
        
        Endpoint: GET /twitter/user/last_tweets
        """
        params = {"includeReplies": include_replies, "cursor": cursor}
        
        if user_id:
            params["userId"] = user_id
        elif username:
            params["userName"] = username
        else:
            raise ValueError("Either user_id or username must be provided")
            
        return self._request("GET", "/twitter/user/last_tweets", params=params)
    
    def get_user_mentions(self, username, since_time=None, until_time=None, cursor=""):
        """
        دریافت منشن‌های کاربر
        
        Endpoint: GET /twitter/user/mentions
        """
        params = {"userName": username, "cursor": cursor}
        
        if since_time:
            params["sinceTime"] = since_time
        if until_time:
            params["untilTime"] = until_time
            
        return self._request("GET", "/twitter/user/mentions", params=params)
    
    # === متدهای API برای توییت‌ها ===
    
    def get_tweets_by_ids(self, tweet_ids):
        """
        دریافت توییت‌ها با شناسه‌های آنها
        
        Endpoint: GET /twitter/tweets
        """
        if isinstance(tweet_ids, list):
            tweet_ids = ",".join(tweet_ids)
            
        return self._request(
            "GET", 
            "/twitter/tweets", 
            params={"tweet_ids": tweet_ids}
        )
    
    def get_list_tweets(self, list_id, since_time=None, until_time=None, include_replies=True, cursor=""):
        """
        دریافت توییت‌های یک لیست
        
        Endpoint: GET /twitter/list/tweets
        """
        params = {
            "listId": list_id, 
            "includeReplies": include_replies,
            "cursor": cursor
        }
        
        if since_time:
            params["sinceTime"] = since_time
        if until_time:
            params["untilTime"] = until_time
            
        return self._request("GET", "/twitter/list/tweets", params=params)
    
    def get_tweet_replies(self, tweet_id, since_time=None, until_time=None, cursor=""):
        """
        دریافت پاسخ‌های یک توییت
        
        Endpoint: GET /twitter/tweet/replies
        """
        params = {"tweetId": tweet_id, "cursor": cursor}
        
        if since_time:
            params["sinceTime"] = since_time
        if until_time:
            params["untilTime"] = until_time
            
        return self._request("GET", "/twitter/tweet/replies", params=params)
    
    def get_tweet_quotes(self, tweet_id, since_time=None, until_time=None, include_replies=True, cursor=""):
        """
        دریافت نقل قول‌های یک توییت
        
        Endpoint: GET /twitter/tweet/quotes
        """
        params = {
            "tweetId": tweet_id, 
            "includeReplies": include_replies,
            "cursor": cursor
        }
        
        if since_time:
            params["sinceTime"] = since_time
        if until_time:
            params["untilTime"] = until_time
            
        return self._request("GET", "/twitter/tweet/quotes", params=params)
    
    def get_tweet_retweeters(self, tweet_id, cursor=""):
        """
        دریافت کاربرانی که یک توییت را ریتوییت کرده‌اند
        
        Endpoint: GET /twitter/tweet/retweeters
        """
        return self._request(
            "GET", 
            "/twitter/tweet/retweeters", 
            params={"tweetId": tweet_id, "cursor": cursor}
        )
    
    def search_tweets(self, query, query_type="Latest", cursor=""):
        """جستجوی پیشرفته توییت‌ها"""
        self.logger.info(f"Searching tweets with query: '{query}'")
        
        response = self._request(
            "GET", 
            "/twitter/tweet/advanced_search", 
            params={"query": query, "queryType": query_type, "cursor": cursor}
        )
        
        # Enhanced diagnostics
        self.logger.debug(f"Response type: {type(response)}")
        if isinstance(response, dict):
            self.logger.debug(f"Response top-level keys: {list(response.keys())}")
            
            # Log tweet structure based on API document format
            if 'tweets' in response:
                tweets_container = response['tweets']
                self.logger.debug(f"Tweets container type: {type(tweets_container)}")
                
                if isinstance(tweets_container, list) and tweets_container:
                    sample_tweet = tweets_container[0]
                    self.logger.debug(f"Sample tweet keys: {list(sample_tweet.keys())}")
                    # Look for specific fields we need
                    self.logger.debug(f"Sample tweet id: {sample_tweet.get('id')}")
                    self.logger.debug(f"Sample tweet text: {sample_tweet.get('text', '')[:50]}...")
                    
                    # Check author structure 
                    if 'author' in sample_tweet:
                        self.logger.debug(f"Author keys: {list(sample_tweet['author'].keys())}")
        
        return response
    # === متدهای API برای فیلتر توییت (وبهوک/وبسوکت) ===
    
    def add_tweet_filter_rule(self, tag, value, interval_seconds):
        """
        افزودن قانون فیلتر توییت
        
        Endpoint: POST /oapi/tweet_filter/add_rule
        """
        data = {
            "tag": tag,
            "value": value,
            "interval_seconds": interval_seconds
        }
        
        return self._request("POST", "/oapi/tweet_filter/add_rule", json=data)
    
    def update_tweet_filter_rule(self, rule_id, tag=None, value=None, interval_seconds=None, is_activated=None):
        """
        به‌روزرسانی قانون فیلتر توییت
        
        Endpoint: POST /oapi/tweet_filter/update_rule
        """
        data = {"rule_id": rule_id}
        
        if tag is not None:
            data["tag"] = tag
        if value is not None:
            data["value"] = value
        if interval_seconds is not None:
            data["interval_seconds"] = interval_seconds
        if is_activated is not None:
            data["is_activated"] = is_activated
            
        return self._request("POST", "/oapi/tweet_filter/update_rule", json=data)
    
    def delete_tweet_filter_rule(self, rule_id):
        """
        حذف قانون فیلتر توییت
        
        Endpoint: DELETE /oapi/tweet_filter/delete_rule
        """
        return self._request(
            "DELETE", 
            "/oapi/tweet_filter/delete_rule", 
            params={"rule_id": rule_id}
        )
    
    def get_tweet_filter_rules(self):
        """
        دریافت تمام قوانین فیلتر توییت
        
        Endpoint: GET /oapi/tweet_filter/get_rules
        """
        return self._request("GET", "/oapi/tweet_filter/get_rules")
    
    def register_webhook(self, rule_id, webhook_url):
        """
        ثبت وبهوک برای دریافت توییت‌های فیلتر شده
        
        Endpoint: POST /oapi/tweet_filter/register_webhook
        """
        data = {
            "rule_id": rule_id,
            "webhook_url": webhook_url
        }
        
        return self._request("POST", "/oapi/tweet_filter/register_webhook", json=data)
    
    # === متدهای کمکی برای Pagination ===
    
    def get_all_user_followers(self, username, max_pages=5):
        """
        دریافت تمام فالوورهای کاربر با استفاده از pagination
        """
        all_followers = []
        cursor = ""
        page = 0
        
        while page < max_pages:
            result = self.get_user_followers(username, cursor)
            
            if "users" in result and result["users"]:
                all_followers.extend(result["users"])
            else:
                break
                
            if result.get("has_next_page", False) and "next_cursor" in result:
                cursor = result["next_cursor"]
                page += 1
            else:
                break
                
        return all_followers
    
    def get_all_user_tweets(self, username=None, user_id=None, include_replies=False, max_pages=5):
        """
        دریافت تمام توییت‌های کاربر با استفاده از pagination
        """
        all_tweets = []
        cursor = ""
        page = 0
        
        while page < max_pages:
            result = self.get_user_tweets(
                username=username, 
                user_id=user_id,
                include_replies=include_replies,
                cursor=cursor
            )
            
            if "tweets" in result and result["tweets"]:
                all_tweets.extend(result["tweets"])
            else:
                break
                
            if result.get("has_next_page", False) and "next_cursor" in result:
                cursor = result["next_cursor"]
                page += 1
            else:
                break
                
        return all_tweets