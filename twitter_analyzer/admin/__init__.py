from flask_admin import Admin, AdminIndexView, BaseView
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, render_template
from flask_admin.base import expose
from flask_login import current_user
from .. import db
from ..models.tweet import Tweet
from ..models.hashtag import Hashtag
from ..models.mention import Mention
from ..models.collection import Collection, CollectionRule
from ..models.user import User
from .views import CollectorAdminView

class MyAdminIndexView(AdminIndexView):
    """نمای سفارشی برای صفحه اصلی پنل مدیریت"""
    @expose('/')
    def index(self):
        # جمع‌آوری داده‌های لازم برای صفحه اصلی پنل مدیریت
        data = {
            'total_tweets': Tweet.query.count(),
            'total_users': User.query.count(),
            'recent_activities': [
                'ورود به سیستم مدیریت',
                'به‌روزرسانی اطلاعات پایگاه داده',
                'اجرای فرآیند جمع‌آوری توییت‌ها'
            ]  # مثال‌هایی از فعالیت‌های اخیر
        }
        
        return self.render('admin/index.html', data=data)
    
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

class TweetsManagementView(BaseView):
    """نمای سفارشی برای مدیریت توییت‌ها"""
    @expose('/')
    def index(self):
        # دریافت پارامترهای جستجو و فیلتر
        from flask import request, current_app
        page = request.args.get('page', 1, type=int)
        per_page = 20  # تعداد توییت در هر صفحه
        keyword = request.args.get('keyword', '')
        username = request.args.get('username', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # ساخت کوئری پایه
        query = Tweet.query
        
        # اعمال فیلترها
        filter_applied = False
        
        # لاگ برای دیباگ
        current_app.logger.debug(f"فیلترها: keyword='{keyword}', username='{username}', date_from='{date_from}', date_to='{date_to}'")
        
        # فیلتر کلیدواژه
        if keyword:
            query = query.filter(Tweet.text.ilike(f'%{keyword}%'))
            filter_applied = True
            current_app.logger.debug(f"فیلتر کلیدواژه اعمال شد: '{keyword}'")
        
        # فیلتر نام کاربری
        if username:
            from ..models.twitter_user import TwitterUser
            from sqlalchemy import or_
            
            # حذف @ از ابتدای نام کاربری اگر وجود داشته باشد
            clean_username = username.strip()
            if clean_username.startswith('@'):
                clean_username = clean_username[1:]
            
            query = query.join(TwitterUser, Tweet.twitter_user_id == TwitterUser.id)
            
            # جستجو در نام کاربری و نام نمایشی
            query = query.filter(or_(
                TwitterUser.username.ilike(f'%{clean_username}%'),
                TwitterUser.display_name.ilike(f'%{clean_username}%')
            ))
            
            filter_applied = True
            current_app.logger.debug(f"فیلتر نام کاربری اعمال شد: '{clean_username}'")
        
        # فیلتر تاریخ
        from datetime import datetime, timedelta
        
        # بررسی هر دو فیلد تاریخ ساخت در توییتر و تاریخ ثبت در سیستم
        from sqlalchemy import or_, and_
        date_filter_conditions = []
        
        # از تاریخ
        if date_from:
            try:
                # تبدیل به تاریخ با ساعت 00:00:00
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                
                # اضافه کردن فیلتر برای هر دو فیلد تاریخ با در نظر گرفتن null
                date_filter_conditions.append(
                    or_(
                        Tweet.twitter_created_at >= from_date,
                        and_(Tweet.twitter_created_at.is_(None), Tweet.created_at >= from_date)
                    )
                )
                
                filter_applied = True
                current_app.logger.debug(f"فیلتر از تاریخ اعمال شد: {from_date.strftime('%Y-%m-%d')}")
            except ValueError as e:
                current_app.logger.error(f"خطا در تبدیل تاریخ: {date_from} - {str(e)}")
        
        # تا تاریخ
        if date_to:
            try:
                # تبدیل به تاریخ با ساعت 23:59:59
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                to_date = to_date + timedelta(days=1) - timedelta(seconds=1)
                
                # اضافه کردن فیلتر برای هر دو فیلد تاریخ با در نظر گرفتن null
                date_filter_conditions.append(
                    or_(
                        Tweet.twitter_created_at <= to_date,
                        and_(Tweet.twitter_created_at.is_(None), Tweet.created_at <= to_date)
                    )
                )
                
                filter_applied = True
                current_app.logger.debug(f"فیلتر تا تاریخ اعمال شد: {to_date.strftime('%Y-%m-%d %H:%M:%S')}")
            except ValueError as e:
                current_app.logger.error(f"خطا در تبدیل تاریخ: {date_to} - {str(e)}")
        
        # اعمال فیلترهای تاریخ
        if date_filter_conditions:
            for condition in date_filter_conditions:
                query = query.filter(condition)
        
        # شمارش کل توییت‌های منطبق با فیلتر
        try:
            total_count = query.count()
            current_app.logger.debug(f"تعداد توییت‌های یافت شده: {total_count}")
        except Exception as e:
            current_app.logger.error(f"خطا در شمارش توییت‌ها: {str(e)}")
            total_count = 0
        
        # پیجینیشن
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        page = max(1, min(page, total_pages))
        
        # بازیابی توییت‌ها با مرتب‌سازی براساس تاریخ (با در نظر گرفتن null)
        from sqlalchemy import desc, nullslast
        try:
            tweets = query.order_by(
                nullslast(desc(Tweet.twitter_created_at)),
                desc(Tweet.created_at)
            ).offset((page-1)*per_page).limit(per_page).all()
            
            current_app.logger.debug(f"تعداد توییت‌های بازیابی شده: {len(tweets)}")
        except Exception as e:
            current_app.logger.error(f"خطا در بازیابی توییت‌ها: {str(e)}")
            tweets = []
        
        # تبدیل به فرمت مناسب برای قالب
        tweets_data = []
        for tweet in tweets:
            username_val = ''
            if tweet.twitter_user:
                username_val = tweet.twitter_user.username
            
            display_date = None
            if tweet.twitter_created_at:
                display_date = tweet.twitter_created_at
            elif tweet.created_at:
                display_date = tweet.created_at
            
            tweets_data.append({
                'id': tweet.id,
                'text': tweet.text,
                'username': username_val,
                'created': display_date
            })
        
        return self.render(
            'admin/tweets.html',
            tweets=tweets_data,
            total_pages=total_pages,
            page=page,
            keyword=keyword,
            username=username,
            date_from=date_from,
            date_to=date_to,
            filter_applied=filter_applied
        )
    
    @expose('/delete/<int:tweet_id>', methods=['POST'])
    def delete_tweet(self, tweet_id):
        """حذف یک توییت"""
        from flask import flash, request, jsonify
        
        tweet = Tweet.query.get_or_404(tweet_id)
        try:
            # جدا کردن روابط قبل از حذف
            tweet.hashtags = []
            tweet.mentions = []
            db.session.add(tweet)
            db.session.flush()
            
            db.session.delete(tweet)
            db.session.commit()
            
            if request.is_json:
                return jsonify({"status": "success", "message": "توییت با موفقیت حذف شد"})
            
            flash("توییت با موفقیت حذف شد.", "success")
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({"status": "error", "message": f"خطا در حذف توییت: {str(e)}"})
            
            flash(f"خطا در حذف توییت: {str(e)}", "error")
        
        if request.is_json:
            return jsonify({"status": "error", "message": "خطای ناشناخته"})
        
        return redirect(url_for('manage_tweets.index'))
    
    @expose('/view/<int:tweet_id>')
    def view_tweet(self, tweet_id):
        """مشاهده جزئیات یک توییت"""
        from flask import jsonify
        
        tweet = Tweet.query.get_or_404(tweet_id)
        username = ''
        if tweet.twitter_user:
            username = tweet.twitter_user.username
            
        tweet_data = {
            'id': tweet.id,
            'twitter_id': tweet.twitter_id,
            'text': tweet.text,
            'username': username,
            'created_at': tweet.twitter_created_at.strftime('%Y-%m-%d %H:%M:%S') if tweet.twitter_created_at else '',
            'likes_count': tweet.likes_count or 0,
            'retweets_count': tweet.retweets_count or 0,
            'replies_count': tweet.replies_count or 0,
            'language': tweet.language or ''
        }
        
        return jsonify(tweet_data)
    
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))
    
class UserManagementView(BaseView):
    """نمای سفارشی برای مدیریت کاربران"""
    @expose('/')
    def index(self):
        users = User.query.all()
        return self.render('admin/users.html', users=users)
    
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

class SettingsView(BaseView):
    """نمای سفارشی برای تنظیمات سیستم"""
    @expose('/')
    def index(self):
        return self.render('admin/settings.html')
    
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))
              
# ایجاد نمونه Admin با قالب پایه سفارشی و نمای سفارشی برای صفحه اصلی
admin = Admin(name='تحلیلگر توییتر', 
              template_mode='bootstrap3', 
              base_template='admin/custom_base.html',
              index_view=MyAdminIndexView())
              
class SecureModelView(ModelView):
    """کلاس پایه برای محافظت از بخش Admin"""
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

def init_app(app):
    # ثبت مدل‌ها در Admin
    admin.add_view(SecureModelView(Tweet, db.session, name='توییت‌ها'))
    admin.add_view(SecureModelView(Hashtag, db.session, name='هشتگ‌ها'))
    admin.add_view(SecureModelView(Mention, db.session, name='منشن‌ها'))
    admin.add_view(SecureModelView(Collection, db.session, name='جمع‌آوری‌ها'))
    admin.add_view(SecureModelView(CollectionRule, db.session, name='قواعد جمع‌آوری'))
    
    # افزودن نماهای سفارشی
    admin.add_view(TweetsManagementView(name='مدیریت توییت‌ها', endpoint='manage_tweets'))
    admin.add_view(UserManagementView(name='مدیریت کاربران', endpoint='manage_users'))
    admin.add_view(SettingsView(name='تنظیمات سیستم', endpoint='settings'))
    
    # افزودن نمای جدید جمع‌آوری توییت‌ها
    admin.add_view(CollectorAdminView(name='جمع‌آوری توییت‌ها', endpoint='collection_admin'))
    
    admin.init_app(app)