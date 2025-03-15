import time
import threading
from flask import current_app
from . import socket

class TwitterStream:
    """
    سرویس دریافت لحظه‌ای توییت‌ها
    """
    
    def __init__(self, twitter_api=None):
        """
        مقداردهی اولیه
        
        Args:
            twitter_api: نمونه TwitterAPI (اختیاری)
        """
        from ..twitter import twitter_api as default_api
        self.twitter_api = twitter_api or default_api
        self.tracking_keywords = []
        self.tracking_thread = None
        self.is_running = False
        self.logger = None
        
        if current_app:
            self.logger = current_app.logger
    
    def start_tracking(self, keywords=None):
        """
        شروع ردیابی کلمات کلیدی
        
        Args:
            keywords: لیست کلمات کلیدی برای ردیابی (اختیاری)
        """
        if self.is_running:
            return False
            
        # استفاده از کلمات کلیدی پیش‌فرض اگر هیچ کلمه کلیدی ارائه نشده باشد
        self.tracking_keywords = keywords or current_app.config.get('TRACKING_KEYWORDS', [])
        
        if not self.tracking_keywords:
            if self.logger:
                self.logger.warning("No tracking keywords provided")
            return False
            
        # شروع ردیابی در یک thread جداگانه
        self.is_running = True
        self.tracking_thread = threading.Thread(target=self._tracking_worker)
        self.tracking_thread.daemon = True
        self.tracking_thread.start()
        
        if self.logger:
            self.logger.info(f"Started tracking keywords: {self.tracking_keywords}")
            
        return True
    
    def stop_tracking(self):
        """توقف ردیابی"""
        self.is_running = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)
            self.tracking_thread = None
            
        if self.logger:
            self.logger.info("Stopped tracking")
            
        return True
    
    def _tracking_worker(self):
        """Worker thread برای ردیابی توییت‌ها"""
        from ..utils.text_processor import PersianTextProcessor
        
        # ایجاد پردازشگر متن
        text_processor = PersianTextProcessor()
        
        # بررسی وجود تحلیلگر آنتروپیک
        anthropic_analyzer = None
        if hasattr(current_app, 'extensions') and 'anthropic_analyzer' in current_app.extensions:
            anthropic_analyzer = current_app.extensions['anthropic_analyzer']
        
        # زمان آخرین بررسی
        last_check_time = time.time()
        
        # بازه زمانی بررسی
        interval_seconds = current_app.config.get('TRACKING_INTERVAL_SECONDS', 60)
        
        # آستانه امتیاز تعامل برای تحلیل پیشرفته
        engagement_threshold = current_app.config.get('ADVANCED_ANALYSIS_THRESHOLD', 100)
        
        while self.is_running:
            try:
                # بررسی هر کلمه کلیدی
                for keyword in self.tracking_keywords:
                    # جستجوی توییت‌ها
                    result = self.twitter_api.search_tweets(keyword)
                    
                    if result and 'tweets' in result:
                        tweets = result['tweets']
                        
                        if isinstance(tweets, dict) and 'results' in tweets:
                            tweets = tweets['results']
                        
                        # پردازش هر توییت
                        for tweet in tweets:
                            tweet_text = tweet.get('text', '')
                            tweet_id = tweet.get('id', '')
                            
                            # تحلیل اولیه با پردازشگر محلی
                            local_analysis = text_processor.analyze_content(tweet_text)
                            
                            # بررسی آمار توییت
                            engagement_score = (
                                tweet.get('likeCount', 0) + 
                                tweet.get('retweetCount', 0) * 2 + 
                                tweet.get('replyCount', 0) * 2
                            )
                            
                            # اطلاعات توییت
                            tweet_data = {
                                'id': tweet_id,
                                'text': tweet_text,
                                'user': tweet.get('author', {}).get('userName', ''),
                                'engagement_score': engagement_score,
                                'local_analysis': local_analysis
                            }
                            
                            # تحلیل پیشرفته اگر امتیاز تعامل بالا باشد
                            if engagement_score > engagement_threshold and anthropic_analyzer:
                                ai_analysis = anthropic_analyzer.analyze_sentiment(tweet_text)
                                tweet_data['ai_analysis'] = ai_analysis
                            
                            # ارسال به کلاینت‌های متصل
                            room = f"track_{keyword}"
                            socket.socketio.emit('tweet', tweet_data, room=room)
                
                # بروزرسانی زمان آخرین بررسی
                elapsed = time.time() - last_check_time
                sleep_time = max(0.1, interval_seconds - elapsed)
                time.sleep(sleep_time)
                last_check_time = time.time()
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in tracking worker: {e}", exc_info=True)
                time.sleep(5)  # تأخیر در صورت بروز خطا