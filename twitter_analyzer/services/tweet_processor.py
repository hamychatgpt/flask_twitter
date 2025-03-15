from flask import current_app
from ..models import db
from ..models.tweet import Tweet
from ..utils.text_processor import PersianTextProcessor
from concurrent.futures import ThreadPoolExecutor
import logging
import time
from sqlalchemy import desc, and_
from datetime import datetime, timedelta

class TweetProcessor:
    """
    پردازنده توییت‌ها برای تحلیل محتوا و احساسات
    """
    
    def __init__(self, app=None):
        """
        مقداردهی اولیه
        
        Args:
            app: نمونه برنامه Flask (اختیاری)
        """
        self.app = app
        self.logger = None
        self.text_processor = None
        self.ai_analyzer = None
        self.processing_thread = None
        self.is_running = False
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        اتصال به برنامه Flask
        
        Args:
            app: نمونه برنامه Flask
        """
        self.app = app
        self.logger = app.logger
        
        # ایجاد پردازشگر متن
        self.text_processor = PersianTextProcessor(app)
        
        # تلاش برای یافتن تحلیلگر هوش مصنوعی
        if 'anthropic_analyzer' in app.extensions:
            self.ai_analyzer = app.extensions['anthropic_analyzer']
        
        app.extensions['tweet_processor'] = self
        
        # ثبت کارهای زمان‌بندی شده
        self._register_scheduled_tasks()
    
    def _register_scheduled_tasks(self):
        """ثبت کارهای زمان‌بندی شده"""
        if not self.app.config.get('SCHEDULER_ENABLED', False):
            return
            
        from ..extensions import scheduler
        
        # پردازش خودکار توییت‌ها هر ساعت
        scheduler.add_job(
            func=self.process_unprocessed_tweets,
            trigger='interval',
            hours=1,
            id='process_tweets'
        )
        
        # تحلیل پیشرفته توییت‌های پرتعامل هر 6 ساعت
        scheduler.add_job(
            func=self.analyze_high_engagement_tweets,
            trigger='interval',
            hours=6,
            id='analyze_top_tweets'
        )
    
    def process_unprocessed_tweets(self, limit=100):
        """
        پردازش توییت‌های پردازش نشده
        
        Args:
            limit: حداکثر تعداد توییت‌ها برای پردازش
            
        Returns:
            تعداد توییت‌های پردازش شده
        """
        with self.app.app_context():
            try:
                # یافتن توییت‌های پردازش نشده
                unprocessed_tweets = Tweet.query.filter_by(is_processed=False).limit(limit).all()
                
                processed_count = 0
                for tweet in unprocessed_tweets:
                    try:
                        # تحلیل محتوا
                        tweet.analyze_sentiment_with_local_processor(self.text_processor)
                        
                        # محاسبه امتیاز تعامل
                        tweet.calculate_engagement_score()
                        tweet.calculate_virality_score()
                        
                        # علامت‌گذاری به عنوان پردازش شده
                        tweet.is_processed = True
                        tweet.processing_date = datetime.utcnow()
                        
                        # ذخیره در پایگاه داده
                        db.session.add(tweet)
                        processed_count += 1
                        
                        # کامیت هر 10 توییت
                        if processed_count % 10 == 0:
                            db.session.commit()
                            
                    except Exception as e:
                        self.logger.error(f"Error processing tweet {tweet.id}: {e}", exc_info=True)
                
                # کامیت نهایی
                db.session.commit()
                
                if processed_count > 0:
                    self.logger.info(f"Processed {processed_count} tweets")
                
                return processed_count
                
            except Exception as e:
                self.logger.error(f"Error in batch processing tweets: {e}", exc_info=True)
                db.session.rollback()
                return 0
    
    def analyze_high_engagement_tweets(self, threshold=None, days=1, limit=20):
        """
        تحلیل پیشرفته توییت‌های با تعامل بالا
        
        Args:
            threshold: آستانه امتیاز تعامل (اختیاری)
            days: تعداد روزهای گذشته برای بررسی
            limit: حداکثر تعداد توییت‌ها برای تحلیل
            
        Returns:
            تعداد توییت‌های تحلیل شده
        """
        if not self.ai_analyzer:
            self.logger.warning("AI Analyzer not available for high engagement tweet analysis")
            return 0
        
        with self.app.app_context():
            try:
                # استفاده از آستانه پیش‌فرض برنامه اگر مشخص نشده باشد
                if threshold is None:
                    threshold = self.app.config.get('ADVANCED_ANALYSIS_THRESHOLD', 100)
                
                # محاسبه زمان شروع
                start_time = datetime.utcnow() - timedelta(days=days)
                
                # یافتن توییت‌های پرتعامل
                # - توییت‌هایی که امتیاز تعامل آنها بالاتر از آستانه است
                # - توییت‌هایی که هنوز تحلیل هوش مصنوعی نشده‌اند
                # - توییت‌هایی که در بازه زمانی مورد نظر هستند
                high_engagement_tweets = Tweet.query.filter(
                    and_(
                        Tweet.engagement_score >= threshold,
                        Tweet.has_ai_analysis == False,
                        Tweet.created_at >= start_time
                    )
                ).order_by(desc(Tweet.engagement_score)).limit(limit).all()
                
                analyzed_count = 0
                for tweet in high_engagement_tweets:
                    try:
                        # تحلیل با هوش مصنوعی
                        sentiment = tweet.analyze_sentiment_with_ai(force=True)
                        
                        if sentiment:
                            # علامت‌گذاری به عنوان تحلیل شده
                            tweet.has_ai_analysis = True
                            
                            # ذخیره در پایگاه داده
                            db.session.add(tweet)
                            analyzed_count += 1
                            
                            # کامیت هر 5 توییت
                            if analyzed_count % 5 == 0:
                                db.session.commit()
                        
                    except Exception as e:
                        self.logger.error(f"Error analyzing high engagement tweet {tweet.id}: {e}", exc_info=True)
                
                # کامیت نهایی
                db.session.commit()
                
                if analyzed_count > 0:
                    self.logger.info(f"AI-analyzed {analyzed_count} high engagement tweets")
                
                return analyzed_count
                
            except Exception as e:
                self.logger.error(f"Error in analyzing high engagement tweets: {e}", exc_info=True)
                db.session.rollback()
                return 0
    
    def start_background_processing(self, interval_seconds=300):
        """
        شروع پردازش خودکار توییت‌ها در پس‌زمینه
        
        Args:
            interval_seconds: فاصله زمانی بین اجراها (ثانیه)
            
        Returns:
            bool: آیا شروع شد
        """
        import threading
        
        if self.is_running:
            return False
        
        self.is_running = True
        
        def background_worker():
            """کارگر پس‌زمینه برای پردازش توییت‌ها"""
            self.logger.info("Background tweet processing started")
            
            while self.is_running:
                try:
                    with self.app.app_context():
                        # پردازش توییت‌های پردازش نشده
                        processed = self.process_unprocessed_tweets(limit=50)
                        
                        # تحلیل توییت‌های پرتعامل
                        if processed == 0:  # فقط وقتی توییت پردازش نشده‌ای نیست
                            self.analyze_high_engagement_tweets(limit=10)
                    
                except Exception as e:
                    self.logger.error(f"Error in background processing: {e}", exc_info=True)
                
                # انتظار تا اجرای بعدی
                time.sleep(interval_seconds)
            
            self.logger.info("Background tweet processing stopped")
        
        # شروع پردازش در یک thread جداگانه
        self.processing_thread = threading.Thread(target=background_worker)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        return True
    
    def stop_background_processing(self):
        """
        توقف پردازش خودکار توییت‌ها
        
        Returns:
            bool: آیا متوقف شد
        """
        if not self.is_running:
            return False
        
        self.is_running = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
            self.processing_thread = None
        
        return True
    
    def process_batch_with_ai(self, query_filter=None, limit=20, concurrency=3):
        """
        پردازش یک دسته از توییت‌ها با هوش مصنوعی به صورت موازی
        
        Args:
            query_filter: فیلتر کوئری برای انتخاب توییت‌ها (اختیاری)
            limit: حداکثر تعداد توییت‌ها
            concurrency: تعداد پردازش‌های همزمان
            
        Returns:
            تعداد توییت‌های پردازش شده
        """
        if not self.ai_analyzer:
            self.logger.warning("AI Analyzer not available for batch processing")
            return 0
        
        with self.app.app_context():
            try:
                # ساخت کوئری
                if query_filter:
                    query = Tweet.query.filter(query_filter)
                else:
                    # پیش‌فرض: توییت‌های پردازش شده محلی ولی بدون تحلیل هوش مصنوعی
                    query = Tweet.query.filter(
                        and_(
                            Tweet.is_processed == True,
                            Tweet.has_ai_analysis == False
                        )
                    )
                
                # مرتب‌سازی و محدودسازی
                tweets = query.order_by(desc(Tweet.engagement_score)).limit(limit).all()
                
                if not tweets:
                    return 0
                
                # پردازش موازی
                processed_count = 0
                
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [executor.submit(self._process_tweet_with_ai, tweet.id) for tweet in tweets]
                    
                    for future in futures:
                        try:
                            success = future.result()
                            if success:
                                processed_count += 1
                        except Exception as e:
                            self.logger.error(f"Error in parallel tweet processing: {e}", exc_info=True)
                
                return processed_count
                
            except Exception as e:
                self.logger.error(f"Error in batch processing with AI: {e}", exc_info=True)
                return 0
    
    def _process_tweet_with_ai(self, tweet_id):
        """
        پردازش یک توییت با هوش مصنوعی
        
        Args:
            tweet_id: شناسه توییت
            
        Returns:
            bool: آیا موفقیت‌آمیز بود
        """
        with self.app.app_context():
            try:
                tweet = Tweet.query.get(tweet_id)
                if not tweet:
                    return False
                
                # تحلیل با هوش مصنوعی
                sentiment = tweet.analyze_sentiment_with_ai(force=True)
                
                if sentiment:
                    # علامت‌گذاری به عنوان تحلیل شده
                    tweet.has_ai_analysis = True
                    
                    # ذخیره در پایگاه داده
                    db.session.add(tweet)
                    db.session.commit()
                    
                    return True
                
                return False
                
            except Exception as e:
                db.session.rollback()
                self.logger.error(f"Error processing tweet {tweet_id} with AI: {e}", exc_info=True)
                return False