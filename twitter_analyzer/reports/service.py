from flask import current_app
from datetime import datetime, timedelta
import os
import json
from sqlalchemy import func
from ..models import db
from ..models.tweet import Tweet
from ..models.hashtag import Hashtag
from ..models.mention import Mention

class ReportingService:
    """
    سرویس گزارش‌گیری
    """
    
    def __init__(self, app=None):
        """
        مقداردهی اولیه
        
        Args:
            app: نمونه برنامه Flask (اختیاری)
        """
        self.app = app
        self.logger = None
        
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
        
        app.extensions['reporting_service'] = self
        
        # ثبت کارهای زمان‌بندی شده
        self._register_scheduled_tasks()
    
    def _register_scheduled_tasks(self):
        """ثبت کارهای زمان‌بندی شده"""
        if not self.app.config.get('SCHEDULER_ENABLED', False):
            return
            
        from ..extensions import scheduler
        
        # گزارش‌گیری هر دقیقه - فقط برای تست
        if self.app.config.get('DEBUG', False) and self.app.config.get('ENABLE_MINUTE_REPORTS', False):
            scheduler.add_job(
                func=self.generate_minute_report,
                trigger='interval',
                minutes=1,
                id='minute_report'
            )
        
        # گزارش‌گیری هر ساعت
        scheduler.add_job(
            func=self.generate_hourly_report,
            trigger='interval',
            hours=1,
            id='hourly_report'
        )
        
        # گزارش‌گیری روزانه
        scheduler.add_job(
            func=self.generate_daily_report,
            trigger='cron',
            hour=0,
            minute=0,
            id='daily_report'
        )
    
    def generate_report(self, period='hour', keywords=None):
        """
        تولید گزارش براساس بازه زمانی
        
        Args:
            period: بازه زمانی (minute, hour, day)
            keywords: کلمات کلیدی (اختیاری)
            
        Returns:
            dict: گزارش
        """
        # زمان شروع بر اساس بازه زمانی
        now = datetime.utcnow()
        if period == 'minute':
            start_time = now - timedelta(minutes=1)
            period_name = "دقیقه گذشته"
        elif period == 'hour':
            start_time = now - timedelta(hours=1)
            period_name = "ساعت گذشته"
        elif period == 'day':
            start_time = now - timedelta(days=1)
            period_name = "روز گذشته"
        else:
            start_time = now - timedelta(hours=1)  # پیش‌فرض: ساعتی
            period_name = "ساعت گذشته"
        
        # کلمات کلیدی
        if keywords is None:
            keywords = self.app.config.get('TRACKING_KEYWORDS', [])
        
        # پایه کوئری
        base_query = Tweet.query.filter(Tweet.created_at >= start_time)
        
        # اعمال فیلتر کلمات کلیدی اگر ارائه شده باشد
        if keywords:
            from sqlalchemy import or_
            keyword_filters = []
            for keyword in keywords:
                keyword_filters.append(Tweet.text.ilike(f'%{keyword}%'))
            base_query = base_query.filter(or_(*keyword_filters))
        
        # تعداد کل توییت‌ها
        total_tweets = base_query.count()
        
        # توییت‌های با بیشترین تعامل
        top_engagement_tweets = base_query.order_by(
            (Tweet.likes_count + Tweet.retweets_count + Tweet.replies_count).desc()
        ).limit(10).all()
        
        # هشتگ‌های پرتکرار
        top_hashtags = db.session.query(
            Hashtag.text, func.count(Tweet.id)
        ).join(
            Tweet.hashtags
        ).filter(
            Tweet.created_at >= start_time
        ).group_by(
            Hashtag.text
        ).order_by(
            func.count(Tweet.id).desc()
        ).limit(10).all()
        
        # منشن‌های پرتکرار
        top_mentions = db.session.query(
            Mention.username, func.count(Tweet.id)
        ).join(
            Tweet.mentions
        ).filter(
            Tweet.created_at >= start_time
        ).group_by(
            Mention.username
        ).order_by(
            func.count(Tweet.id).desc()
        ).limit(10).all()
        
        # تحلیل احساسات
        sentiment_counts = db.session.query(
            Tweet.sentiment, func.count(Tweet.id)
        ).filter(
            Tweet.created_at >= start_time,
            Tweet.sentiment.isnot(None)
        ).group_by(
            Tweet.sentiment
        ).all()
        
        sentiment_data = {s if s else 'unknown': c for s, c in sentiment_counts}
        
        # آمار کلی
        stats = {
            'total_tweets': total_tweets,
            'total_likes': sum(t.likes_count or 0 for t in top_engagement_tweets),
            'total_retweets': sum(t.retweets_count or 0 for t in top_engagement_tweets),
            'total_replies': sum(t.replies_count or 0 for t in top_engagement_tweets),
            'sentiment': sentiment_data,
            'top_hashtags': [{'text': h, 'count': c} for h, c in top_hashtags],
            'top_mentions': [{'username': m, 'count': c} for m, c in top_mentions]
        }
        
        # تحلیل پیشرفته با AI
        if total_tweets > 0 and 'anthropic_analyzer' in self.app.extensions:
            try:
                # جمع‌آوری متن توییت‌ها برای تحلیل
                texts = [t.text for t in top_engagement_tweets[:5] if t.text]
                
                if texts:
                    # تحلیل با AI
                    analyzer = self.app.extensions['anthropic_analyzer']
                    ai_analysis = analyzer.analyze_text_full('\n\n'.join(texts))
                    
                    stats['ai_analysis'] = ai_analysis
            except Exception as e:
                self.logger.error(f"Error in AI analysis: {e}", exc_info=True)
        
        # گزارش نهایی
        report = {
            'period': period,
            'period_name': period_name,
            'start_time': start_time.isoformat(),
            'end_time': now.isoformat(),
            'keywords': keywords,
            'stats': stats,
            'top_tweets': [{
                'id': t.twitter_id,
                'text': t.text,
                'likes': t.likes_count,
                'retweets': t.retweets_count,
                'replies': t.replies_count,
                'sentiment': t.sentiment
            } for t in top_engagement_tweets]
        }
        
        # ذخیره گزارش
        self._save_report(report, period)
        
        return report
    
    def _save_report(self, report, period):
        """
        ذخیره گزارش در فایل
        
        Args:
            report: گزارش
            period: بازه زمانی
        """
        try:
            # ایجاد دایرکتوری reports اگر وجود نداشته باشد
            reports_dir = os.path.join(self.app.instance_path, 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            # نام فایل
            now = datetime.now()
            filename = f"report_{period}_{now.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(reports_dir, filename)
            
            # ذخیره گزارش
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Report saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving report: {e}", exc_info=True)
    
    def generate_minute_report(self):
        """تولید گزارش دقیقه‌ای - برای تست"""
        with self.app.app_context():
            self.logger.info("Generating minute report...")
            try:
                report = self.generate_report(period='minute')
                self.logger.info(f"Minute report generated with {report['stats']['total_tweets']} tweets")
            except Exception as e:
                self.logger.error(f"Error generating minute report: {e}", exc_info=True)
    
    def generate_hourly_report(self):
        """تولید گزارش ساعتی"""
        with self.app.app_context():
            self.logger.info("Generating hourly report...")
            try:
                report = self.generate_report(period='hour')
                self.logger.info(f"Hourly report generated with {report['stats']['total_tweets']} tweets")
            except Exception as e:
                self.logger.error(f"Error generating hourly report: {e}", exc_info=True)
    
    def generate_daily_report(self):
        """تولید گزارش روزانه"""
        with self.app.app_context():
            self.logger.info("Generating daily report...")
            try:
                report = self.generate_report(period='day')
                self.logger.info(f"Daily report generated with {report['stats']['total_tweets']} tweets")
            except Exception as e:
                self.logger.error(f"Error generating daily report: {e}", exc_info=True)