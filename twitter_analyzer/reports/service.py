from flask import current_app
from datetime import datetime, timedelta
import os
import json
from sqlalchemy import func, desc
from ..models import db
from ..models.tweet import Tweet
from ..models.hashtag import Hashtag
from ..models.mention import Mention
import traceback

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
        
        # ایجاد دایرکتوری reports اگر وجود نداشته باشد
        try:
            reports_dir = os.path.join(app.instance_path, 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            self.logger.info(f"Reports directory created/verified at: {reports_dir}")
        except Exception as e:
            self.logger.error(f"Error creating reports directory: {e}")
        
        app.extensions['reporting_service'] = self
        
        # ثبت کارهای زمان‌بندی شده
        self._register_scheduled_tasks()
    
    def _register_scheduled_tasks(self):
        """ثبت کارهای زمان‌بندی شده"""
        if not self.app.config.get('SCHEDULER_ENABLED', False):
            self.logger.info("Scheduler is disabled, skipping scheduled tasks registration")
            return
            
        try:
            from ..extensions import scheduler
            
            # گزارش‌گیری هر دقیقه - فقط برای تست
            if self.app.config.get('DEBUG', False) and self.app.config.get('ENABLE_MINUTE_REPORTS', False):
                scheduler.add_job(
                    func=self.generate_minute_report,
                    trigger='interval',
                    minutes=1,
                    id='minute_report'
                )
                self.logger.info("Registered minute report job")
            
            # گزارش‌گیری هر ساعت
            scheduler.add_job(
                func=self.generate_hourly_report,
                trigger='interval',
                hours=1,
                id='hourly_report'
            )
            self.logger.info("Registered hourly report job")
            
            # گزارش‌گیری روزانه
            scheduler.add_job(
                func=self.generate_daily_report,
                trigger='cron',
                hour=0,
                minute=0,
                id='daily_report'
            )
            self.logger.info("Registered daily report job")
        except Exception as e:
            self.logger.error(f"Error registering scheduled tasks: {e}", exc_info=True)
    
    def generate_report(self, period='hour', keywords=None):
        """
        تولید گزارش براساس بازه زمانی
        
        Args:
            period: بازه زمانی (minute, hour, day)
            keywords: کلمات کلیدی (اختیاری)
            
        Returns:
            dict: گزارش
        """
        self.logger.info(f"Generating {period} report" + (f" with keywords: {keywords}" if keywords else ""))
        try:
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
            self.logger.info(f"Found {total_tweets} tweets for {period} report")
            
            # توییت‌های با بیشترین تعامل
            top_engagement_tweets = base_query.order_by(
                desc(Tweet.engagement_score)
            ).limit(10).all()
            
            # هشتگ‌های پرتکرار
            top_hashtags = db.session.query(
                Hashtag.text, func.count(Tweet.id).label('count')
            ).join(
                Tweet.hashtags
            ).filter(
                Tweet.created_at >= start_time
            ).group_by(
                Hashtag.text
            ).order_by(
                desc('count')
            ).limit(10).all()
            
            # منشن‌های پرتکرار
            top_mentions = db.session.query(
                Mention.username, func.count(Tweet.id).label('count')
            ).join(
                Tweet.mentions
            ).filter(
                Tweet.created_at >= start_time
            ).group_by(
                Mention.username
            ).order_by(
                desc('count')
            ).limit(10).all()
            
            # تحلیل احساسات
            sentiment_counts = db.session.query(
                Tweet.sentiment, func.count(Tweet.id).label('count')
            ).filter(
                Tweet.created_at >= start_time,
                Tweet.sentiment.isnot(None)
            ).group_by(
                Tweet.sentiment
            ).all()
            
            sentiment_data = {}
            for sentiment, count in sentiment_counts:
                sentiment_key = sentiment if sentiment else 'unknown'
                sentiment_data[sentiment_key] = count
            
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
                    stats['ai_analysis_error'] = str(e)
            
            # گزارش نهایی
            report = {
                'period': period,
                'period_name': period_name,
                'start_time': start_time.isoformat(),
                'end_time': now.isoformat(),
                'keywords': keywords,
                'stats': stats,
                'top_tweets': [{
                    'id': t.id,
                    'twitter_id': t.twitter_id,
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
        
        except Exception as e:
            error_details = traceback.format_exc()
            self.logger.error(f"Error generating {period} report: {e}\n{error_details}")
            
            # بازگرداندن گزارش خطا
            return {
                'period': period,
                'period_name': f"گزارش {period} (خطا)",
                'start_time': datetime.utcnow().isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'keywords': keywords,
                'stats': {
                    'total_tweets': 0,
                    'error': str(e),
                },
                'error': str(e),
                'error_details': error_details
            }
    
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
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving report: {e}", exc_info=True)
            return None
    
    def generate_minute_report(self):
        """تولید گزارش دقیقه‌ای - برای تست"""
        with self.app.app_context():
            self.logger.info("Generating minute report...")
            try:
                report = self.generate_report(period='minute')
                self.logger.info(f"Minute report generated with {report.get('stats', {}).get('total_tweets', 0)} tweets")
                return report
            except Exception as e:
                self.logger.error(f"Error generating minute report: {e}", exc_info=True)
                return None
    
    def generate_hourly_report(self):
        """تولید گزارش ساعتی"""
        with self.app.app_context():
            self.logger.info("Generating hourly report...")
            try:
                report = self.generate_report(period='hour')
                self.logger.info(f"Hourly report generated with {report.get('stats', {}).get('total_tweets', 0)} tweets")
                return report
            except Exception as e:
                self.logger.error(f"Error generating hourly report: {e}", exc_info=True)
                return None
    
    def generate_daily_report(self):
        """تولید گزارش روزانه"""
        with self.app.app_context():
            self.logger.info("Generating daily report...")
            try:
                report = self.generate_report(period='day')
                self.logger.info(f"Daily report generated with {report.get('stats', {}).get('total_tweets', 0)} tweets")
                return report
            except Exception as e:
                self.logger.error(f"Error generating daily report: {e}", exc_info=True)
                return None

    def get_reports_list(self, limit=None):
        """
        دریافت لیست گزارش‌های موجود
        
        Args:
            limit: محدودیت تعداد گزارش‌ها (اختیاری)
            
        Returns:
            list: لیست گزارش‌ها
        """
        try:
            reports_dir = os.path.join(self.app.instance_path, 'reports')
            if not os.path.exists(reports_dir):
                return []
            
            reports = []
            for filename in os.listdir(reports_dir):
                if filename.endswith('.json') and filename.startswith('report_'):
                    try:
                        filepath = os.path.join(reports_dir, filename)
                        
                        # استخراج بازه زمانی و تاریخ از نام فایل
                        parts = filename.replace('.json', '').split('_')
                        period = parts[1]
                        date_str = '_'.join(parts[2:])
                        
                        # تبدیل رشته تاریخ به شیء datetime
                        try:
                            created_at = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                        except:
                            created_at = datetime.fromtimestamp(os.path.getctime(filepath))
                        
                        # خواندن بخشی از فایل برای دریافت اطلاعات پایه
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        reports.append({
                            'id': filename.replace('.json', ''),
                            'filename': filename,
                            'period': period,
                            'period_name': data.get('period_name', period),
                            'created_at': created_at.isoformat(),
                            'start_time': data.get('start_time'),
                            'end_time': data.get('end_time'),
                            'total_tweets': data.get('stats', {}).get('total_tweets', 0),
                            'keywords': data.get('keywords', [])
                        })
                        
                    except Exception as e:
                        self.logger.error(f"Error reading report {filename}: {e}")
            
            # مرتب‌سازی براساس تاریخ (جدیدترین اول)
            reports.sort(key=lambda x: x['created_at'], reverse=True)
            
            # اعمال محدودیت تعداد
            if limit is not None and int(limit) > 0:
                reports = reports[:int(limit)]
            
            return reports
        except Exception as e:
            self.logger.error(f"Error getting reports list: {e}", exc_info=True)
            return []