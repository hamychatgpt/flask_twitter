from flask_admin import BaseView, expose
from flask import redirect, url_for, request, flash, render_template, jsonify, current_app
from flask_login import current_user, login_required
from ..collector.service import CollectorService
from ..models.collection import Collection, CollectionRule
from ..models.tweet import Tweet
from ..models import db

class CollectorAdminView(BaseView):
    """نمای مدیریت جمع‌آوری توییت‌ها در پنل ادمین"""
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))
    
    @expose('/')
    def index(self):
        """صفحه اصلی بخش جمع‌آوری در پنل ادمین"""
        collections = Collection.query.order_by(Collection.created_at.desc()).limit(10).all()
        return self.render('admin/collector/index.html', collections=collections)
    
    @expose('/keyword', methods=['GET', 'POST'])
    def collect_keyword(self):
        """جمع‌آوری براساس کلمه کلیدی"""
        if request.method == 'POST':
            keyword = request.form.get('keyword')
            max_tweets = request.form.get('max_tweets', 100, type=int)
            
            if not keyword:
                flash('لطفاً کلمه کلیدی را وارد کنید', 'error')
                return redirect(url_for('.collect_keyword'))
            
            service = CollectorService()
            try:
                collection, count = service.collect_by_keyword(keyword, max_tweets)
                flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
                return redirect(url_for('.view_collection', collection_id=collection.id))
            except Exception as e:
                flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
                current_app.logger.error(f"Error in keyword collection: {str(e)}", exc_info=True)
                return redirect(url_for('.collect_keyword'))
                
        return self.render('admin/collector/keyword.html')
    
    @expose('/username', methods=['GET', 'POST'])
    def collect_username(self):
        """جمع‌آوری براساس نام کاربری"""
        if request.method == 'POST':
            username = request.form.get('username')
            max_tweets = request.form.get('max_tweets', 100, type=int)
            
            if not username:
                flash('لطفاً نام کاربری را وارد کنید', 'error')
                return redirect(url_for('.collect_username'))
            
            # حذف @ از ابتدای نام کاربری در صورت وجود
            if username.startswith('@'):
                username = username[1:]
            
            service = CollectorService()
            try:
                collection, count = service.collect_by_username(username, max_tweets)
                flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
                return redirect(url_for('.view_collection', collection_id=collection.id))
            except Exception as e:
                flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
                current_app.logger.error(f"Error in username collection: {str(e)}", exc_info=True)
                return redirect(url_for('.collect_username'))
                
        return self.render('admin/collector/username.html')
    
    @expose('/hashtag', methods=['GET', 'POST'])
    def collect_hashtag(self):
        """جمع‌آوری براساس هشتگ"""
        if request.method == 'POST':
            hashtag = request.form.get('hashtag')
            max_tweets = request.form.get('max_tweets', 100, type=int)
            
            if not hashtag:
                flash('لطفاً هشتگ را وارد کنید', 'error')
                return redirect(url_for('.collect_hashtag'))
            
            # حذف # از ابتدای هشتگ در صورت وجود
            if hashtag.startswith('#'):
                hashtag = hashtag[1:]
            
            service = CollectorService()
            try:
                collection, count = service.collect_by_hashtag(hashtag, max_tweets)
                flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
                return redirect(url_for('.view_collection', collection_id=collection.id))
            except Exception as e:
                flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
                current_app.logger.error(f"Error in hashtag collection: {str(e)}", exc_info=True)
                return redirect(url_for('.collect_hashtag'))
                
        return self.render('admin/collector/hashtag.html')
    
    @expose('/mentions', methods=['GET', 'POST'])
    def collect_mentions(self):
        """جمع‌آوری منشن‌های یک کاربر"""
        if request.method == 'POST':
            username = request.form.get('username')
            max_tweets = request.form.get('max_tweets', 100, type=int)
            
            if not username:
                flash('لطفاً نام کاربری را وارد کنید', 'error')
                return redirect(url_for('.collect_mentions'))
            
            # حذف @ از ابتدای نام کاربری در صورت وجود
            if username.startswith('@'):
                username = username[1:]
            
            service = CollectorService()
            try:
                collection, count = service.collect_by_mentions(username, max_tweets)
                flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
                return redirect(url_for('.view_collection', collection_id=collection.id))
            except Exception as e:
                flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
                current_app.logger.error(f"Error in mentions collection: {str(e)}", exc_info=True)
                return redirect(url_for('.collect_mentions'))
                
        return self.render('admin/collector/mentions.html')
    
    @expose('/list', methods=['GET', 'POST'])
    def collect_list(self):
        """جمع‌آوری توییت‌های یک لیست"""
        if request.method == 'POST':
            list_id = request.form.get('list_id')
            max_tweets = request.form.get('max_tweets', 100, type=int)
            
            if not list_id:
                flash('لطفاً شناسه لیست را وارد کنید', 'error')
                return redirect(url_for('.collect_list'))
            
            service = CollectorService()
            try:
                collection, count = service.collect_list_tweets(list_id, max_tweets)
                flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
                return redirect(url_for('.view_collection', collection_id=collection.id))
            except Exception as e:
                flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
                current_app.logger.error(f"Error in list collection: {str(e)}", exc_info=True)
                return redirect(url_for('.collect_list'))
                
        return self.render('admin/collector/list.html')
    
    @expose('/tweet-replies', methods=['GET', 'POST'])
    def collect_tweet_replies(self):
        """جمع‌آوری پاسخ‌های یک توییت"""
        if request.method == 'POST':
            tweet_id = request.form.get('tweet_id')
            max_tweets = request.form.get('max_tweets', 100, type=int)
            
            if not tweet_id:
                flash('لطفاً شناسه توییت را وارد کنید', 'error')
                return redirect(url_for('.collect_tweet_replies'))
            
            service = CollectorService()
            try:
                collection, count = service.collect_tweet_replies(tweet_id, max_tweets)
                flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
                return redirect(url_for('.view_collection', collection_id=collection.id))
            except Exception as e:
                flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
                current_app.logger.error(f"Error in tweet replies collection: {str(e)}", exc_info=True)
                return redirect(url_for('.collect_tweet_replies'))
                
        return self.render('admin/collector/tweet_replies.html')
    
    @expose('/collections')
    def collections(self):
        """نمایش همه مجموعه‌های جمع‌آوری شده"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Collection.query
        
        # اعمال فیلترها
        filter_name = request.args.get('name', '')
        filter_type = request.args.get('type', '')
        filter_status = request.args.get('status', '')
        
        if filter_name:
            query = query.filter(Collection.name.like(f'%{filter_name}%'))
            
        if filter_type:
            query = query.join(CollectionRule).filter(CollectionRule.rule_type == filter_type)
            
        if filter_status:
            query = query.filter(Collection.status == filter_status)
        
        # پیجینیشن
        pagination = query.order_by(Collection.created_at.desc()).paginate(page=page, per_page=per_page)
        
        return self.render('admin/collector/collections.html', 
                          collections=pagination.items,
                          pagination=pagination,
                          filter_name=filter_name,
                          filter_type=filter_type,
                          filter_status=filter_status)
    
    @expose('/collections/<int:collection_id>')
    def view_collection(self, collection_id):
        """نمایش جزئیات یک مجموعه"""
        collection = Collection.query.get_or_404(collection_id)
        
        # دریافت توییت‌ها با پیجینیشن
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        tweets_query = Tweet.query.filter_by(collection_id=collection_id)
        
        # اعمال جستجو
        search = request.args.get('search', '')
        if search:
            tweets_query = tweets_query.filter(Tweet.text.like(f'%{search}%'))
        
        tweets_pagination = tweets_query.order_by(Tweet.twitter_created_at.desc()).paginate(
            page=page, per_page=per_page
        )
        
        return self.render('admin/collector/view_collection.html',
                          collection=collection,
                          tweets=tweets_pagination.items,
                          pagination=tweets_pagination,
                          search=search)
    
    @expose('/collections/<int:collection_id>/delete', methods=['POST'])
    def delete_collection(self, collection_id):
        """حذف یک مجموعه"""
        collection = Collection.query.get_or_404(collection_id)
        
        try:
            # حذف توییت‌های مجموعه
            tweets = Tweet.query.filter_by(collection_id=collection_id).all()
            for tweet in tweets:
                # جدا کردن روابط قبل از حذف
                tweet.hashtags = []
                tweet.mentions = []
                db.session.add(tweet)
            
            db.session.flush()
            
            # حذف توییت‌ها
            Tweet.query.filter_by(collection_id=collection_id).delete()
            
            # حذف قواعد جمع‌آوری
            CollectionRule.query.filter_by(collection_id=collection_id).delete()
            
            # حذف مجموعه
            db.session.delete(collection)
            db.session.commit()
            
            flash(f'مجموعه "{collection.name}" با موفقیت حذف شد.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting collection: {str(e)}", exc_info=True)
            flash(f'خطا در حذف مجموعه: {str(e)}', 'error')
        
        return redirect(url_for('.collections'))
    
    @expose('/api/stats')
    def collection_stats(self):
        """آمار جمع‌آوری توییت‌ها"""
        try:
            # تعداد کل مجموعه‌ها
            total_collections = Collection.query.count()
            
            # تعداد کل توییت‌ها
            total_tweets = Tweet.query.count()
            
            # آمار به تفکیک روش جمع‌آوری
            collection_methods = db.session.query(
                CollectionRule.rule_type, 
                db.func.count(CollectionRule.id)
            ).group_by(CollectionRule.rule_type).all()
            
            methods_stats = {rule_type: count for rule_type, count in collection_methods}
            
            # آمار وضعیت مجموعه‌ها
            status_stats = db.session.query(
                Collection.status, 
                db.func.count(Collection.id)
            ).group_by(Collection.status).all()
            
            status_data = {status: count for status, count in status_stats}
            
            return jsonify({
                'total_collections': total_collections,
                'total_tweets': total_tweets,
                'methods': methods_stats,
                'status': status_data
            })
            
        except Exception as e:
            current_app.logger.error(f"Error getting collection stats: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500