import requests
import time
import logging
from urllib.parse import urljoin
from flask import current_app, _app_ctx_stack
from werkzeug.local import LocalProxy
from cachetools import TTLCache

# تعریف LocalProxy برای دسترسی راحت به سرویس
def _get_twitter_api():
    return current_app.extensions.get('twitter_api')

current_twitter = LocalProxy(_get_twitter_api)

class TwitterAPI:
    """
    افزونه Flask برای ارتباط با API غیررسمی توییتر
    
    استفاده:
    
        twitter = TwitterAPI()
        
        def create_app():
            app = Flask(__name__)
            twitter.init_app(app)
            return app
            
        # استفاده در ویوها
        @app.route('/user/<username>')
        def get_user(username):
            user = current_twitter.get_user_info(username)
            return jsonify(user)
    """
    
    def __init__(self, app=None):
        self.base_url = "https://api.twitterapi.io"
        self.session = None
        self.api_key = None
        self.cache = None
        self.logger = logging.getLogger("flask-twitter-api")
        
        # اطلاعات rate limit
        self.rate_limit_remaining = 200
        self.rate_limit_reset = 0
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        مقداردهی اولیه افزونه با برنامه Flask
        """
        # تنظیم کلید API از کانفیگ برنامه
        self.api_key = app.config.get('TWITTER_API_KEY')
        
        if not self.api_key:
            self.logger.warning("TWITTER_API_KEY not set in app config")
        
        # ایجاد یک session جدید برای درخواست‌ها
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": self.api_key})
        
        # تنظیم کش
        cache_size = app.config.get('TWITTER_CACHE_SIZE', 1000)
        cache_ttl = app.config.get('TWITTER_CACHE_TTL', 300)  # 5 دقیقه پیش‌فرض
        self.cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
        
        # تنظیم سطح لاگ
        if app.config.get('DEBUG', False):
            self.logger.setLevel(logging.DEBUG)
        
        # ثبت در app.extensions
        app.extensions['twitter_api'] = self
        
        # تنظیم teardown برای پاکسازی منابع
        app.teardown_appcontext(self._teardown)
    
    def _teardown(self, exc):
        """
        پاکسازی منابع در پایان هر درخواست
        """
        ctx = _app_ctx_stack.top
        if hasattr(ctx, 'twitter_api_session'):
            ctx.twitter_api_session.close()
    
    def _handle_rate_limit(self, response):
        """مدیریت اطلاعات rate limit از هدرها"""
        if 'X-Rate-Limit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-Rate-Limit-Remaining'])
        
        if 'X-Rate-Limit-Reset' in response.headers:
            self.rate_limit_reset = int(response.headers['X-Rate-Limit-Reset'])
        
        # هشدار اگر به محدودیت نزدیک شدیم
        if self.rate_limit_remaining < 10:
            self.logger.warning(f"Rate limit running low: {self.rate_limit_remaining} requests remaining")
            
            # تأخیر به صورت هوشمند
            if self.rate_limit_remaining < 5:
                wait_time = max(0, self.rate_limit_reset - time.time())
                if wait_time > 0:
                    self.logger.info(f"Rate limit critical, adding delay of {min(wait_time, 2)}s")
                    time.sleep(min(wait_time, 2))  # حداکثر 2 ثانیه صبر می‌کنیم
    
    def _request(self, method, endpoint, params=None, data=None, json=None, retry_count=3, cache_key=None):
        """
        انجام درخواست HTTP به API توییتر با مدیریت خطا و retry
        """
        # بررسی کش برای درخواست‌های GET
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
                
                # مدیریت rate limit
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
                    return {"status": "error", "msg": "Bad request parameters"}
                elif response.status_code == 401:
                    return {"status": "error", "msg": "Invalid API key"}
                elif response.status_code == 404:
                    return {"status": "error", "msg": "Resource not found"}
                elif response.status_code >= 500:
                    if attempt < retry_count - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        self.logger.warning(f"Server error, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {"status": "error", "msg": "Server error"}
                else:
                    return {"status": "error", "msg": str(e)}
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request exception: {e}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Request error, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {"status": "error", "msg": "Connection error"}
        
        return {"status": "error", "msg": "Max retries exceeded"}

    # =================================================================
    # توابع اصلی API - در اینجا همان توابع قبلی را قرار دهید
    # =================================================================
    
    def get_user_info(self, username):
        """دریافت اطلاعات کاربر با نام کاربری"""
        cache_key = f"user_info_{username}"
        return self._request(
            "GET", 
            "/twitter/user/info", 
            params={"userName": username},
            cache_key=cache_key
        )
    
    def get_user_batch_info(self, user_ids):
        """دریافت اطلاعات چند کاربر به صورت همزمان"""
        if isinstance(user_ids, list):
            user_ids = ",".join(user_ids)
            
        cache_key = f"batch_users_{user_ids}"
        return self._request(
            "GET", 
            "/twitter/user/batch_info_by_ids", 
            params={"userIds": user_ids},
            cache_key=cache_key
        )
    
    # سایر توابع API مانند قبل
    # ...