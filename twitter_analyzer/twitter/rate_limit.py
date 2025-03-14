"""
مدیریت Rate Limit برای API توییتر
"""
import time
import random
import logging
from datetime import datetime, timedelta

class RateLimitManager:
    """
    مدیریت هوشمند Rate Limit با پشتیبانی از backoff نمایی و جلوگیری از درخواست‌های بلاک شده
    """
    def __init__(self, default_limit=200, logger=None):
        self.logger = logger or logging.getLogger("twitter_api.rate_limit")
        
        # تنظیمات اصلی rate limit
        self.endpoints = {}  # نگهداری اطلاعات rate limit به تفکیک endpoint
        self.default_limit = default_limit
        self.default_remaining = default_limit
        self.default_reset_time = datetime.utcnow() + timedelta(minutes=15)
        
        # تنظیمات backoff
        self.base_delay = 1.0  # زمان پایه تأخیر (ثانیه)
        self.max_delay = 60.0  # حداکثر زمان تأخیر (ثانیه)
        self.factor = 2.0  # ضریب رشد نمایی
        self.jitter = 0.1  # میزان تصادفی‌سازی (jitter)
        
        # آمار
        self.stats = {
            'blocked_count': 0,
            'wait_count': 0,
            'total_wait_time': 0,
            'last_reset': datetime.utcnow()
        }
    
    def update(self, endpoint, headers):
        """به‌روزرسانی اطلاعات rate limit برای یک endpoint خاص از هدرهای پاسخ"""
        limit = headers.get('X-Rate-Limit-Limit')
        remaining = headers.get('X-Rate-Limit-Remaining')
        reset = headers.get('X-Rate-Limit-Reset')
        
        # اگر اطلاعات rate limit در هدرها وجود داشت، ذخیره می‌کنیم
        if limit or remaining or reset:
            if endpoint not in self.endpoints:
                self.endpoints[endpoint] = {
                    'limit': self.default_limit,
                    'remaining': self.default_remaining,
                    'reset_time': self.default_reset_time
                }
            
            if limit:
                self.endpoints[endpoint]['limit'] = int(limit)
            
            if remaining:
                self.endpoints[endpoint]['remaining'] = int(remaining)
                
                # هشدار اگر محدودیت زیر 10% است
                if int(remaining) < self.endpoints[endpoint]['limit'] * 0.1:
                    self.logger.warning(
                        f"Rate limit for {endpoint} is running low: {remaining} "
                        f"of {self.endpoints[endpoint]['limit']} remaining"
                    )
            
            if reset:
                self.endpoints[endpoint]['reset_time'] = datetime.fromtimestamp(int(reset))
    
    def should_wait(self, endpoint):
        """
        بررسی اینکه آیا قبل از ارسال درخواست جدید به endpoint باید صبر کنیم یا خیر
        
        Returns:
            (bool, float): آیا باید صبر کنیم و برای چه مدت
        """
        # اگر اطلاعات endpoint موجود نباشد، نیازی به صبر نیست
        if endpoint not in self.endpoints:
            return False, 0
        
        # بررسی تعداد درخواست‌های باقی‌مانده
        if self.endpoints[endpoint]['remaining'] <= 0:
            # محاسبه زمان باقی‌مانده تا reset
            now = datetime.utcnow()
            reset_time = self.endpoints[endpoint]['reset_time']
            
            if reset_time > now:
                wait_seconds = (reset_time - now).total_seconds()
                
                # اگر زمان زیادی تا reset مانده، مقدار کمتری صبر می‌کنیم
                if wait_seconds > 5:
                    wait_seconds = min(5, wait_seconds * 0.2)  # حداکثر 5 ثانیه یا 20% زمان باقی‌مانده
                
                self.logger.warning(
                    f"Rate limit for {endpoint} exceeded. Waiting {wait_seconds:.2f} seconds."
                )
                
                self.stats['blocked_count'] += 1
                self.stats['wait_count'] += 1
                self.stats['total_wait_time'] += wait_seconds
                
                return True, wait_seconds
        
        return False, 0
    
    def calculate_backoff(self, attempt, status_code=None):
        """محاسبه زمان backoff نمایی برای تلاش مجدد"""
        # محاسبه تأخیر پایه براساس شماره تلاش با رشد نمایی
        delay = min(self.max_delay, self.base_delay * (self.factor ** attempt))
        
        # افزودن jitter (تصادفی‌سازی) برای جلوگیری از thundering herd
        jitter_value = self.jitter * delay * (random.random() * 2 - 1)  # -jitter*delay to +jitter*delay
        delay = max(0, delay + jitter_value)  # اطمینان از عدم منفی شدن تأخیر
        
        # تنظیم تأخیر براساس کد وضعیت
        if status_code:
            if status_code == 429:  # Rate limit exceeded
                delay *= 1.5  # افزایش 50% برای rate limit
            elif 500 <= status_code < 600:  # خطای سرور
                delay *= 1.2  # افزایش 20% برای خطاهای سرور
            elif status_code == 408:  # Request timeout
                delay *= 1.3  # افزایش 30% برای timeout
        
        self.stats['wait_count'] += 1
        self.stats['total_wait_time'] += delay
        
        return delay
    
    def get_stats(self):
        """دریافت آمار rate limit"""
        stats = self.stats.copy()
        
        # اطلاعات endpoint ها
        endpoint_stats = {}
        for endpoint, data in self.endpoints.items():
            now = datetime.utcnow()
            reset_time = data['reset_time']
            time_to_reset = max(0, (reset_time - now).total_seconds())
            
            endpoint_stats[endpoint] = {
                'limit': data['limit'],
                'remaining': data['remaining'],
                'usage_percent': ((data['limit'] - data['remaining']) / data['limit']) * 100 if data['limit'] > 0 else 0,
                'reset_in_seconds': time_to_reset
            }
        
        stats['endpoints'] = endpoint_stats
        stats['avg_wait_time'] = stats['total_wait_time'] / stats['wait_count'] if stats['wait_count'] > 0 else 0
        
        return stats
    
    def reset_stats(self):
        """بازنشانی آمار"""
        self.stats = {
            'blocked_count': 0,
            'wait_count': 0,
            'total_wait_time': 0,
            'last_reset': datetime.utcnow()
        }