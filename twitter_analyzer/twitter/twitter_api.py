import requests
import time
import logging
import json
import traceback
from urllib.parse import urljoin
from flask import current_app
from .rate_limit import RateLimitManager
from .transformers import TwitterDataTransformer
from .models import TweetModel, TwitterUserModel

class TwitterAPI:
    """
    رابط پیشرفته برای کار با API غیررسمی توییتر با پشتیبانی از کش و مدیریت Rate Limit
    """
    
    def __init__(self, app=None, api_key=None):
        # تنظیمات پایه
        self.base_url = "https://api.twitterapi.io"
        self.session = None
        self.api_key = api_key
        self.cache = None  # در init_app مقداردهی می‌شود
        self.logger = logging.getLogger("twitter_api")
        
        # مدیریت کننده rate limit
        self.rate_limiter = RateLimitManager(logger=self.logger)
        
        # تنظیمات پیشرفته
        self.max_retries = 5
        self.base_retry_delay = 2  # ثانیه
        self.max_retry_delay = 60  # ثانیه
        self.timeout = (3.05, 30)  # (connect timeout, read timeout)
        
        # اتصالات وبسوکت فعال
        self.websocket_connections = {}
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        مقداردهی اولیه افزونه با برنامه Flask
        """
        if not self.api_key:
            self.api_key = app.config.get('TWITTER_API_KEY')
        
        if not self.api_key:
            self.logger.warning("TWITTER_API_KEY not set in app config")
        
        # ایجاد یک session جدید برای درخواست‌ها
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})
        
        # استفاده از کش موجود در برنامه
        if 'cache' in app.extensions:
            self.cache = app.extensions['cache']
            self.logger.info("Using existing Flask-Caching instance")
        else:
            self.logger.warning("No Flask-Caching instance found. Caching is disabled.")
        
        # تنظیم تعداد تلاش مجدد و تأخیر
        self.max_retries = app.config.get('TWITTER_API_MAX_RETRIES', 5)
        self.base_retry_delay = app.config.get('TWITTER_API_BASE_RETRY_DELAY', 2)
        self.max_retry_delay = app.config.get('TWITTER_API_MAX_RETRY_DELAY', 60)
        
        # تنظیم timeout
        connect_timeout = app.config.get('TWITTER_API_CONNECT_TIMEOUT', 3.05)
        read_timeout = app.config.get('TWITTER_API_READ_TIMEOUT', 30)
        self.timeout = (connect_timeout, read_timeout)
        
        # تنظیم سطح لاگر
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
        # بستن اتصالات وبسوکت فعال (اگر وجود دارد)
        for ws_id, ws in list(self.websocket_connections.items()):
            try:
                ws.close()
                del self.websocket_connections[ws_id]
            except Exception as e:
                self.logger.error(f"Error closing websocket {ws_id}: {e}")
    
    def _get_cache_key(self, method, endpoint, params):
        """
        تولید کلید یکتا برای کش براساس پارامترهای درخواست
        """
        import hashlib
        
        # تبدیل پارامترها به رشته
        params_str = ""
        if params:
            if isinstance(params, dict):
                # مرتب‌سازی کلیدها برای ثبات
                params_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            else:
                params_str = str(params)
        
        # ترکیب اجزاء و ساخت هش MD5
        key_base = f"{method}:{endpoint}:{params_str}"
        return f"twitter_api:{hashlib.md5(key_base.encode()).hexdigest()}"
    
    def _request(self, method, endpoint, params=None, data=None, json_data=None, 
                 retry_count=None, cache_key=None, headers=None, files=None, stream=False):
        """
        انجام درخواست HTTP به API توییتر با مدیریت خطا، کش و rate limit
        """
        # تعداد تلاش پیش‌فرض
        if retry_count is None:
            retry_count = self.max_retries
        
        # بررسی کش اگر متد GET باشد و کش فعال باشد
        if method == 'GET' and self.cache:
            # استفاده از کلید ارائه شده یا تولید کلید جدید
            if not cache_key:
                cache_key = self._get_cache_key(method, endpoint, params)
            
            # بررسی کش
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self.logger.debug(f"Cache hit for {endpoint}")
                return cached_result
        
        url = urljoin(self.base_url, endpoint)
        
        # بررسی rate limit قبل از ارسال درخواست
        should_wait, wait_time = self.rate_limiter.should_wait(endpoint)
        if should_wait:
            self.logger.info(f"Rate limit check: waiting {wait_time:.2f}s before requesting {endpoint}")
            time.sleep(wait_time)
        
        # چندین تلاش مجدد
        for attempt in range(retry_count):
            try:
                self.logger.debug(f"Making {method} request to {url} (Attempt {attempt+1}/{retry_count})")
                
                # ترکیب هدرهای پایه و اضافی
                request_headers = {}
                if self.session and self.session.headers:
                    request_headers.update(self.session.headers)
                if headers:
                    request_headers.update(headers)
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=request_headers,
                    files=files,
                    stream=stream,
                    timeout=self.timeout
                )
                
                # به‌روزرسانی اطلاعات rate limit
                self.rate_limiter.update(endpoint, response.headers)
                
                # بررسی کد وضعیت
                if response.status_code == 429:  # Rate limit exceeded
                    wait_time = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds")
                    time.sleep(min(wait_time, self.max_retry_delay))
                    continue
                    
                response.raise_for_status()
                
                # پردازش پاسخ stream
                if stream:
                    # برای درخواست‌های stream، خود پاسخ را برمی‌گردانیم
                    return response
                
                # پارس JSON پاسخ
                result = response.json()
                
                # بررسی وضعیت خطا در پاسخ
                if isinstance(result, dict) and result.get('status') == 'error' and 'msg' in result:
                    self.logger.error(f"API error: {result['msg']}")
                    return result
                
                # ذخیره در کش برای درخواست‌های GET
                if method == 'GET' and self.cache and cache_key and result:
                    # محاسبه TTL متناسب با endpoint
                    ttl = 300  # پیش‌فرض 5 دقیقه
                    
                    # TTL کوتاه‌تر برای داده‌های متغیر مانند جستجو
                    if 'search' in endpoint:
                        ttl = 60  # 1 دقیقه
                    # TTL طولانی‌تر برای داده‌های ثابت‌تر مانند اطلاعات کاربر
                    elif 'user/info' in endpoint:
                        ttl = 3600  # 1 ساعت
                    
                    if self.cache and hasattr(self.cache, 'set'):
                        self.cache.set(cache_key, result, timeout=ttl)
                    elif self.cache and isinstance(self.cache, dict):
                        self.cache[cache_key] = result
                
                return result
                
            except requests.exceptions.HTTPError as e:
                self.logger.error(f"HTTP error: {e}")
                
                # پردازش کدهای وضعیت مختلف طبق مستندات
                if response.status_code == 400:  # Bad request
                    self.logger.error(f"Bad request: {response.text}")
                    error_response = {"status": "error", "msg": "Bad request parameters"}
                    
                    # سعی در پارس پیام خطا از پاسخ
                    try:
                        error_data = response.json()
                        if "error" in error_data or "message" in error_data:
                            error_response["msg"] = error_data.get("error", error_data.get("message", "Bad request parameters"))
                    except:
                        pass
                        
                    return error_response
                    
                elif response.status_code == 401:  # Authentication error
                    self.logger.error("Authentication error")
                    return {"status": "error", "msg": "Invalid API key"}
                    
                elif response.status_code == 403:  # Permission denied
                    self.logger.error("Permission denied")
                    return {"status": "error", "msg": "Permission denied"}
                    
                elif response.status_code == 404:  # Resource not found
                    self.logger.error(f"Resource not found: {url}")
                    return {"status": "error", "msg": "Resource not found"}
                    
                elif response.status_code >= 500:  # Server error
                    if attempt < retry_count - 1:
                        wait_time = self.rate_limiter.calculate_backoff(attempt, response.status_code)
                        self.logger.warning(f"Server error, retrying in {wait_time:.2f} seconds...")
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
                    wait_time = self.rate_limiter.calculate_backoff(attempt)
                    self.logger.warning(f"Request error: {e}, retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Request failed after {retry_count} attempts: {e}")
                    return {"status": "error", "msg": "Connection error"}
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON parse error: {e}")
                return {"status": "error", "msg": "Invalid JSON response"}
                
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                self.logger.error(traceback.format_exc())
                return {"status": "error", "msg": f"Unexpected error: {str(e)}"}
                
        return {"status": "error", "msg": "Max retries exceeded"}
    
    # === متدهای API برای اطلاعات کاربر ===
    
    def get_user_info(self, username: str) -> dict:
        """
        دریافت اطلاعات کاربر با نام کاربری
        
        Args:
            username: نام کاربری
            
        Returns:
            dict: اطلاعات کاربر
        """
        cache_key = f"user_info_{username}"
        return self._request(
            "GET", 
            "/twitter/user/info", 
            params={"userName": username},
            cache_key=cache_key
        )
    
    def get_user_batch_info(self, user_ids) -> dict:
        """
        دریافت اطلاعات چند کاربر به صورت همزمان
        
        Args:
            user_ids: لیست شناسه‌های کاربران یا رشته جدا شده با کاما
            
        Returns:
            dict: اطلاعات کاربران
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
    
    def get_user_followers(self, username: str, cursor: str = "") -> dict:
        """
        دریافت فالوورهای کاربر
        
        Args:
            username: نام کاربری
            cursor: نشانگر صفحه‌بندی
            
        Returns:
            dict: فالوورهای کاربر (۲۰۰ فالوور در هر صفحه)
        """
        return self._request(
            "GET", 
            "/twitter/user/followers", 
            params={"userName": username, "cursor": cursor}
        )
    
    def get_all_user_followers(self, username: str, max_pages: int = 5) -> list:
        """
        دریافت تمام فالوورهای کاربر با صفحه‌بندی خودکار
        
        Args:
            username: نام کاربری
            max_pages: حداکثر تعداد صفحات
            
        Returns:
            list: لیست فالوورها
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
                
            # بررسی وجود صفحه بعدی
            if result.get("has_next_page", False) and "next_cursor" in result:
                cursor = result["next_cursor"]
                page += 1
            else:
                break
                
        return all_followers
    
    def get_user_followings(self, username: str, cursor: str = "") -> dict:
        """
        دریافت افرادی که کاربر فالو کرده
        
        Args:
            username: نام کاربری
            cursor: نشانگر صفحه‌بندی
            
        Returns:
            dict: لیست افراد فالو شده (۲۰۰ کاربر در هر صفحه)
        """
        return self._request(
            "GET", 
            "/twitter/user/followings", 
            params={"userName": username, "cursor": cursor}
        )
    
    def get_all_user_followings(self, username: str, max_pages: int = 5) -> list:
        """
        دریافت تمام افرادی که کاربر فالو کرده با صفحه‌بندی خودکار
        
        Args:
            username: نام کاربری
            max_pages: حداکثر تعداد صفحات
            
        Returns:
            list: لیست افراد فالو شده
        """
        all_followings = []
        cursor = ""
        page = 0
        
        while page < max_pages:
            result = self.get_user_followings(username, cursor)
            
            if "users" in result and result["users"]:
                all_followings.extend(result["users"])
            else:
                break
                
            # بررسی وجود صفحه بعدی
            if result.get("has_next_page", False) and "next_cursor" in result:
                cursor = result["next_cursor"]
                page += 1
            else:
                break
                
        return all_followings
    
    def get_user_tweets(self, user_id: str = None, username: str = None, 
                        include_replies: bool = False, cursor: str = "") -> dict:
        """
        دریافت آخرین توییت‌های کاربر
        
        Args:
            user_id: شناسه کاربر (اختیاری)
            username: نام کاربری (اختیاری)
            include_replies: شامل پاسخ‌ها
            cursor: نشانگر صفحه‌بندی
            
        Returns:
            dict: توییت‌های کاربر (۲۰ توییت در هر صفحه)
        """
        if not user_id and not username:
            raise ValueError("Either user_id or username must be provided")
            
        params = {
            "includeReplies": str(include_replies).lower(), 
            "cursor": cursor
        }
        
        if user_id:
            params["userId"] = user_id
        elif username:
            params["userName"] = username
            
        return self._request("GET", "/twitter/user/last_tweets", params=params)
    
    def get_all_user_tweets(self, username: str = None, user_id: str = None, 
                           include_replies: bool = False, max_pages: int = 5, 
                           max_tweets: int = 1000) -> list:
        """
        دریافت تمام توییت‌های کاربر با صفحه‌بندی خودکار
        
        Args:
            username: نام کاربری (اختیاری)
            user_id: شناسه کاربر (اختیاری)
            include_replies: شامل پاسخ‌ها
            max_pages: حداکثر تعداد صفحات
            max_tweets: حداکثر تعداد توییت‌ها
            
        Returns:
            list: لیست توییت‌ها
        """
        all_tweets = []
        cursor = ""
        page = 0
        
        while page < max_pages and len(all_tweets) < max_tweets:
            result = self.get_user_tweets(
                username=username, 
                user_id=user_id,
                include_replies=include_replies,
                cursor=cursor
            )
            
            if "tweets" in result:
                tweets_data = result["tweets"]
                
                # پردازش ساختارهای مختلف پاسخ
                if isinstance(tweets_data, dict) and "results" in tweets_data:
                    # اگر tweets یک دیکشنری با کلید results باشد
                    all_tweets.extend(tweets_data["results"])
                elif isinstance(tweets_data, list):
                    # اگر tweets یک لیست باشد
                    all_tweets.extend(tweets_data)
                else:
                    self.logger.warning(f"Unexpected tweets structure: {type(tweets_data)}")
                    break
            else:
                break
                
            # بررسی وجود صفحه بعدی
            if result.get("has_next_page", False) and "next_cursor" in result:
                cursor = result["next_cursor"]
                page += 1
            else:
                break
                
            # خروج اگر به تعداد مورد نظر رسیدیم
            if len(all_tweets) >= max_tweets:
                break
                
        return all_tweets[:max_tweets]  # اطمینان از تعداد درست
    
    def get_user_mentions(self, username: str, since_time: int = None, 
                          until_time: int = None, cursor: str = "") -> dict:
        """
        دریافت منشن‌های کاربر
        
        Args:
            username: نام کاربری
            since_time: زمان Unix برای شروع جستجوی منشن‌ها
            until_time: زمان Unix برای پایان جستجوی منشن‌ها
            cursor: نشانگر صفحه‌بندی
            
        Returns:
            dict: منشن‌های کاربر (۲۰ منشن در هر صفحه)
        """
        params = {"userName": username, "cursor": cursor}
        
        if since_time is not None:
            params["sinceTime"] = since_time
        if until_time is not None:
            params["untilTime"] = until_time
            
        return self._request("GET", "/twitter/user/mentions", params=params)
    
    def get_all_user_mentions(self, username: str, since_time: int = None, 
                             until_time: int = None, max_pages: int = 5, 
                             max_mentions: int = 1000) -> list:
        """
        دریافت تمام منشن‌های کاربر با صفحه‌بندی خودکار
        
        Args:
            username: نام کاربری
            since_time: زمان Unix برای شروع جستجوی منشن‌ها
            until_time: زمان Unix برای پایان جستجوی منشن‌ها
            max_pages: حداکثر تعداد صفحات
            max_mentions: حداکثر تعداد منشن‌ها
            
        Returns:
            list: لیست منشن‌ها
        """
        all_mentions = []
        cursor = ""
        page = 0
        
        while page < max_pages and len(all_mentions) < max_mentions:
            result = self.get_user_mentions(
                username, 
                since_time, 
                until_time, 
                cursor
            )
            
            if "tweets" in result and result["tweets"]:
                all_mentions.extend(result["tweets"])
            else:
                break
                
            # بررسی وجود صفحه بعدی
            if result.get("has_next_page", False) and "next_cursor" in result:
                cursor = result["next_cursor"]
                page += 1
            else:
                break
                
            # خروج اگر به تعداد مورد نظر رسیدیم
            if len(all_mentions) >= max_mentions:
                break
                
        return all_mentions[:max_mentions]  # اطمینان از تعداد درست
    
    # === متدهای API برای توییت‌ها ===
    
    def get_tweets_by_ids(self, tweet_ids) -> dict:
        """
        دریافت توییت‌ها با شناسه‌های آنها
        
        Args:
            tweet_ids: لیست شناسه‌های توییت‌ها یا رشته جدا شده با کاما
            
        Returns:
            dict: توییت‌ها
        """
        if isinstance(tweet_ids, list):
            tweet_ids = ",".join(tweet_ids)
            
        return self._request(
            "GET", 
            "/twitter/tweets", 
            params={"tweet_ids": tweet_ids}
        )
    
    def get_list_tweets(self, list_id: str, since_time: int = None, 
                        until_time: int = None, include_replies: bool = True, 
                        cursor: str = "") -> dict:
        """
        دریافت توییت‌های یک لیست
        
        Args:
            list_id: شناسه لیست
            since_time: زمان Unix برای شروع جستجوی توییت‌ها
            until_time: زمان Unix برای پایان جستجوی توییت‌ها
            include_replies: شامل پاسخ‌ها
            cursor: نشانگر صفحه‌بندی
            
        Returns:
            dict: توییت‌های لیست (۲۰ توییت در هر صفحه)
        """
        params = {
            "listId": list_id, 
            "includeReplies": str(include_replies).lower(),
            "cursor": cursor
        }
        
        if since_time is not None:
            params["sinceTime"] = since_time
        if until_time is not None:
            params["untilTime"] = until_time
            
        return self._request("GET", "/twitter/list/tweets", params=params)
    
    def search_tweets(self, query: str, query_type: str = "Latest", 
                      cursor: str = "") -> dict:
        """
        جستجوی پیشرفته توییت‌ها
        
        Args:
            query: عبارت جستجو
            query_type: نوع جستجو ("Latest" یا "Top")
            cursor: نشانگر صفحه‌بندی
            
        Returns:
            dict: نتایج جستجو (۲۰ توییت در هر صفحه)
        """
        self.logger.info(f"Searching tweets with query: '{query}'")
        
        # اعتبارسنجی query_type
        if query_type not in ["Latest", "Top"]:
            self.logger.warning(f"Invalid query_type: {query_type}. Using 'Latest'")
            query_type = "Latest"
        
        return self._request(
            "GET", 
            "/twitter/tweet/advanced_search", 
            params={
                "query": query, 
                "queryType": query_type, 
                "cursor": cursor
            }
        )
    
    def search_all_tweets(self, query: str, query_type: str = "Latest", 
                         max_pages: int = 5, max_tweets: int = 1000) -> list:
        """
        جستجوی تمام توییت‌ها با صفحه‌بندی خودکار
        
        Args:
            query: عبارت جستجو
            query_type: نوع جستجو ("Latest" یا "Top")
            max_pages: حداکثر تعداد صفحات
            max_tweets: حداکثر تعداد توییت‌ها
            
        Returns:
            list: نتایج جستجو
        """
        all_tweets = []
        cursor = ""
        page = 0
        
        while page < max_pages and len(all_tweets) < max_tweets:
            self.logger.info(f"Searching tweets page {page+1}/{max_pages} with query: '{query}'")
            
            result = self.search_tweets(query, query_type, cursor)
            
            # استخراج توییت‌ها با توجه به ساختار احتمالی پاسخ
            if 'tweets' in result:
                tweets_container = result['tweets']
                
                if isinstance(tweets_container, list):
                    all_tweets.extend(tweets_container)
                    self.logger.info(f"Found {len(tweets_container)} tweets in page {page+1}")
                    
                elif isinstance(tweets_container, dict) and 'results' in tweets_container:
                    all_tweets.extend(tweets_container['results'])
                    self.logger.info(f"Found {len(tweets_container['results'])} tweets in page {page+1}")
                    
                else:
                    self.logger.warning(f"Unexpected tweets structure: {type(tweets_container)}")
                    break
            else:
                self.logger.warning(f"No 'tweets' key in response. Keys: {list(result.keys())}")
                break
                
            # بررسی وجود صفحه بعدی
            if result.get("has_next_page", False) and "next_cursor" in result:
                cursor = result["next_cursor"]
                page += 1
            else:
                break
                
            # خروج اگر به تعداد مورد نظر رسیدیم
            if len(all_tweets) >= max_tweets:
                break
                
        return all_tweets[:max_tweets]  # اطمینان از تعداد درست
    
    def get_tweet_replies(self, tweet_id: str, since_time: int = None, 
                         until_time: int = None, cursor: str = "") -> dict:
        """
        دریافت پاسخ‌های یک توییت
        
        Args:
            tweet_id: شناسه توییت
            since_time: زمان Unix برای شروع جستجوی پاسخ‌ها
            until_time: زمان Unix برای پایان جستجوی پاسخ‌ها
            cursor: نشانگر صفحه‌بندی
            
        Returns:
            dict: پاسخ‌های توییت (۲۰ پاسخ در هر صفحه)
        """
        params = {"tweetId": tweet_id, "cursor": cursor}
        
        if since_time is not None:
            params["sinceTime"] = since_time
        if until_time is not None:
            params["untilTime"] = until_time
            
        return self._request("GET", "/twitter/tweet/replies", params=params)
    
    def get_all_tweet_replies(self, tweet_id: str, since_time: int = None, 
                             until_time: int = None, max_pages: int = 5, 
                             max_replies: int = 1000) -> list:
        """
        دریافت تمام پاسخ‌های یک توییت با صفحه‌بندی خودکار
        
        Args:
            tweet_id: شناسه توییت
            since_time: زمان Unix برای شروع جستجوی پاسخ‌ها
            until_time: زمان Unix برای پایان جستجوی پاسخ‌ها
            max_pages: حداکثر تعداد صفحات
            max_replies: حداکثر تعداد پاسخ‌ها
            
        Returns:
            list: لیست پاسخ‌ها
        """
        all_replies = []
        cursor = ""
        page = 0
        
        while page < max_pages and len(all_replies) < max_replies:
            result = self.get_tweet_replies(
                tweet_id, 
                since_time, 
                until_time, 
                cursor
            )
            
            if "tweets" in result and result["tweets"]:
                all_replies.extend(result["tweets"])
            else:
                break
                
            # بررسی وجود صفحه بعدی
            if result.get("has_next_page", False) and "next_cursor" in result:
                cursor = result["next_cursor"]
                page += 1
            else:
                break
                
            # خروج اگر به تعداد مورد نظر رسیدیم
            if len(all_replies) >= max_replies:
                break
                
        return all_replies[:max_replies]  # اطمینان از تعداد درست
    
    def get_tweet_quotes(self, tweet_id: str, since_time: int = None, 
                         until_time: int = None, include_replies: bool = True, 
                         cursor: str = "") -> dict:
        """
        دریافت توییت‌های بازنشر یک توییت
        
        Args:
            tweet_id: شناسه توییت
            since_time: زمان Unix برای شروع جستجوی بازنشرها
            until_time: زمان Unix برای پایان جستجوی بازنشرها
            include_replies: شامل پاسخ‌ها
            cursor: نشانگر صفحه‌بندی
            
        Returns:
            dict: توییت‌های بازنشر (۲۰ توییت در هر صفحه)
        """
        params = {
            "tweetId": tweet_id, 
            "includeReplies": str(include_replies).lower(),
            "cursor": cursor
        }
        
        if since_time is not None:
            params["sinceTime"] = since_time
        if until_time is not None:
            params["untilTime"] = until_time
            
        return self._request("GET", "/twitter/tweet/quotes", params=params)
        
    def get_all_tweet_quotes(self, tweet_id: str, since_time: int = None, 
                           until_time: int = None, include_replies: bool = True,
                           max_pages: int = 5, max_quotes: int = 1000) -> list:
        """
        دریافت تمام توییت‌های بازنشر یک توییت با صفحه‌بندی خودکار
        
        Args:
            tweet_id: شناسه توییت
            since_time: زمان Unix برای شروع جستجوی بازنشرها
            until_time: زمان Unix برای پایان جستجوی بازنشرها
            include_replies: شامل پاسخ‌ها
            max_pages: حداکثر تعداد صفحات
            max_quotes: حداکثر تعداد بازنشرها
            
        Returns:
            list: لیست بازنشرها
        """
        all_quotes = []
        cursor = ""
        page = 0
        
        while page < max_pages and len(all_quotes) < max_quotes:
            result = self.get_tweet_quotes(
                tweet_id, 
                since_time, 
                until_time, 
                include_replies,
                cursor
            )
            
            if "tweets" in result and result["tweets"]:
                all_quotes.extend(result["tweets"])
            else:
                break
                
            # بررسی وجود صفحه بعدی
            if result.get("has_next_page", False) and "next_cursor" in result:
                cursor = result["next_cursor"]
                page += 1
            else:
                break
                
            # خروج اگر به تعداد مورد نظر رسیدیم
            if len(all_quotes) >= max_quotes:
                break
                
        return all_quotes[:max_quotes]  # اطمینان از تعداد درست
    
    def get_tweet_retweeters(self, tweet_id: str, cursor: str = "") -> dict:
        """
        دریافت کاربرانی که یک توییت را ریتوییت کرده‌اند
        
        Args:
            tweet_id: شناسه توییت
            cursor: نشانگر صفحه‌بندی
            
        Returns:
            dict: کاربران ریتوییت کننده (حدود ۱۰۰ کاربر در هر صفحه)
        """
        params = {"tweetId": tweet_id, "cursor": cursor}
        return self._request("GET", "/twitter/tweet/retweeters", params=params)
        
    def get_all_tweet_retweeters(self, tweet_id: str, max_pages: int = 5, 
                                max_users: int = 1000) -> list:
        """
        دریافت تمام کاربرانی که یک توییت را ریتوییت کرده‌اند با صفحه‌بندی خودکار
        
        Args:
            tweet_id: شناسه توییت
            max_pages: حداکثر تعداد صفحات
            max_users: حداکثر تعداد کاربران
            
        Returns:
            list: لیست کاربران ریتوییت کننده
        """
        all_retweeters = []
        cursor = ""
        page = 0
        
        while page < max_pages and len(all_retweeters) < max_users:
            result = self.get_tweet_retweeters(tweet_id, cursor)
            
            if "users" in result and result["users"]:
                all_retweeters.extend(result["users"])
            else:
                break
                
            # بررسی وجود صفحه بعدی
            if result.get("has_next_page", False) and "next_cursor" in result:
                cursor = result["next_cursor"]
                page += 1
            else:
                break
                
            # خروج اگر به تعداد مورد نظر رسیدیم
            if len(all_retweeters) >= max_users:
                break
                
        return all_retweeters[:max_users]  # اطمینان از تعداد درست
    
    # === متدهای API برای ترندها ===
    
    def get_trends(self, woeid: int = 1) -> dict:
        """
        دریافت ترندهای فعلی
        
        Args:
            woeid: کد مکان (پیش‌فرض: 1 - جهانی)
            
        Returns:
            dict: لیست ترندها
        """
        return self._request(
            "GET", 
            "/twitter/trends/available", 
            params={"woeid": woeid},
            cache_key=f"trends_{woeid}"
        )
    
    def get_trends_by_location(self, location: str) -> dict:
        """
        دریافت ترندها بر اساس نام مکان
        
        Args:
            location: نام مکان (مثل Iran, Tehran, US, Global, etc.)
            
        Returns:
            dict: لیست ترندها
        """
        # نگاشت نام‌های رایج به کدهای WOEID
        location_map = {
            "global": 1,
            "worldwide": 1,
            "iran": 23424851,
            "tehran": 2251945,
            "us": 23424977,
            "uk": 23424975,
            "turkey": 23424969
        }
        
        woeid = location_map.get(location.lower(), 1)
        
        return self.get_trends(woeid)
    
    # === متدهای API برای وبهوک و وبسوکت ===
    
    def add_tweet_filter_rule(self, tag: str, value: str, interval_seconds: int) -> dict:
        """
        افزودن یک قاعده فیلتر توییت برای وبهوک/وبسوکت
        
        Args:
            tag: برچسب سفارشی برای شناسایی قاعده (حداکثر ۲۵۵ کاراکتر)
            value: قاعده برای فیلتر کردن توییت‌ها (حداکثر ۲۵۵ کاراکتر)
            interval_seconds: بازه زمانی بررسی توییت‌ها به ثانیه (حداقل ۱۰۰، حداکثر ۸۶۴۰۰)
            
        Returns:
            dict: پاسخ API شامل شناسه قاعده ایجاد شده
        """
        # اعتبارسنجی ورودی‌ها
        if len(tag) > 255:
            return {"status": "error", "msg": "Tag must be at most 255 characters"}
            
        if len(value) > 255:
            return {"status": "error", "msg": "Value must be at most 255 characters"}
            
        if interval_seconds < 100 or interval_seconds > 86400:
            return {"status": "error", "msg": "Interval must be between 100 and 86400 seconds"}
            
        return self._request(
            "POST", 
            "/oapi/tweet_filter/add_rule", 
            json_data={
                "tag": tag,
                "value": value,
                "interval_seconds": interval_seconds
            }
        )
    
    def update_tweet_filter_rule(self, rule_id: str, tag: str = None, 
                                value: str = None, interval_seconds: int = None, 
                                is_activated: bool = None) -> dict:
        """
        به‌روزرسانی یک قاعده فیلتر توییت
        
        Args:
            rule_id: شناسه قاعده مورد نظر
            tag: برچسب جدید (اختیاری)
            value: قاعده جدید (اختیاری)
            interval_seconds: بازه زمانی جدید (اختیاری)
            is_activated: وضعیت فعال‌سازی (اختیاری)
            
        Returns:
            dict: پاسخ API
        """
        update_data = {"rule_id": rule_id}
        
        # اضافه کردن فیلدهای اختیاری
        if tag is not None:
            if len(tag) > 255:
                return {"status": "error", "msg": "Tag must be at most 255 characters"}
            update_data["tag"] = tag
            
        if value is not None:
            if len(value) > 255:
                return {"status": "error", "msg": "Value must be at most 255 characters"}
            update_data["value"] = value
            
        if interval_seconds is not None:
            if interval_seconds < 100 or interval_seconds > 86400:
                return {"status": "error", "msg": "Interval must be between 100 and 86400 seconds"}
            update_data["interval_seconds"] = interval_seconds
            
        if is_activated is not None:
            update_data["is_activated"] = is_activated
            
        return self._request(
            "POST", 
            "/oapi/tweet_filter/update_rule", 
            json_data=update_data
        )
    
    def delete_tweet_filter_rule(self, rule_id: str) -> dict:
        """
        حذف یک قاعده فیلتر توییت
        
        Args:
            rule_id: شناسه قاعده مورد نظر
            
        Returns:
            dict: پاسخ API
        """
        return self._request(
            "DELETE", 
            "/oapi/tweet_filter/delete_rule", 
            params={"rule_id": rule_id}
        )
    
    def get_tweet_filter_rules(self) -> dict:
        """
        دریافت تمام قواعد فیلتر توییت
        
        Returns:
            dict: لیست قواعد فیلتر
        """
        return self._request("GET", "/oapi/tweet_filter/get_rules")
    
    def register_webhook(self, rule_id: str, webhook_url: str) -> dict:
        """
        ثبت یک وبهوک برای دریافت توییت‌های منطبق با قاعده
        
        Args:
            rule_id: شناسه قاعده مورد نظر
            webhook_url: آدرس URL وبهوک
            
        Returns:
            dict: پاسخ API شامل شناسه وبهوک
        """
        return self._request(
            "POST", 
            "/oapi/tweet_filter/register_webhook", 
            json_data={
                "rule_id": rule_id,
                "webhook_url": webhook_url
            }
        )
        
    # === متدهای مدیریت کش و Rate Limit ===
    
    def clear_cache(self, pattern=None):
        """
        پاکسازی کش با پشتیبانی از الگو
        
        Args:
            pattern: الگوی کلیدهای کش برای پاکسازی (اختیاری)
            
        Returns:
            str: پیام نتیجه
        """
        if not self.cache:
            return "Cache is not enabled"
            
        if pattern:
            import re
            
            # نکته: این متد نیاز به دسترسی مستقیم به داده‌های کش دارد که ممکن است
            # در برخی پیاده‌سازی‌های Flask-Caching موجود نباشد
            try:
                cache_keys = self.cache.cache._cache.keys()
                pattern_re = re.compile(pattern)
                matching_keys = [k for k in cache_keys if pattern_re.search(k)]
                
                for key in matching_keys:
                    self.cache.delete(key)
                    
                return f"Cleared {len(matching_keys)} cache keys matching pattern: {pattern}"
            except (AttributeError, TypeError):
                # پاکسازی کامل اگر دسترسی به کلیدها ممکن نباشد
                self.cache.clear()
                return f"Pattern matching not supported with current cache backend. All cache cleared."
        else:
            self.cache.clear()
            return "Cache cleared"
    
    def get_rate_limit_stats(self):
        """
        دریافت آمار rate limit
        
        Returns:
            dict: آمار rate limit
        """
        return self.rate_limiter.get_stats()
    
    def reset_rate_limit_stats(self):
        """
        بازنشانی آمار rate limit
        
        Returns:
            str: پیام تأیید
        """
        self.rate_limiter.reset_stats()
        return "Rate limit statistics reset"
    
    # === متدهای درخواست بچ ===
    
    def batch_request(self, requests_info, max_concurrent=3):
        """
        ارسال چندین درخواست به API با مدیریت محدودیت‌ها
        
        Args:
            requests_info: لیستی از درخواست‌ها به فرمت {'method': 'GET', 'endpoint': '...', 'params': {...}}
            max_concurrent: حداکثر تعداد درخواست‌های همزمان
            
        Returns:
            list: نتایج درخواست‌ها
        """
        results = []
        
        # گروه‌بندی درخواست‌ها به دسته‌های کوچکتر
        for i in range(0, len(requests_info), max_concurrent):
            batch = requests_info[i:i+max_concurrent]
            
            # ارسال هر دسته
            batch_results = []
            for req_info in batch:
                method = req_info.get('method', 'GET')
                endpoint = req_info.get('endpoint')
                params = req_info.get('params', {})
                data = req_info.get('data')
                json_data = req_info.get('json')
                
                # ارسال درخواست و ذخیره نتیجه
                result = self._request(
                    method=method, 
                    endpoint=endpoint, 
                    params=params,
                    data=data,
                    json_data=json_data
                )
                batch_results.append(result)
                
                # تأخیر کوتاه بین درخواست‌ها برای جلوگیری از فشار به API
                time.sleep(0.2)
            
            results.extend(batch_results)
            
            # تأخیر بین دسته‌ها
            if i + max_concurrent < len(requests_info):
                time.sleep(1)
        
        return results
    
    def set_api_key(self, api_key):
        """
        تنظیم کلید API جدید
        
        Args:
            api_key: کلید API جدید
            
        Returns:
            str: پیام تأیید
        """
        self.api_key = api_key
        if self.session:
            self.session.headers.update({"X-API-Key": self.api_key})
        
        # پاکسازی کش در صورت وجود
        if self.cache:
            self.cache.clear()
            
        self.logger.info("API key updated and cache cleared")
        return "API key updated successfully"