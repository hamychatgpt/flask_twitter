from flask import render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from . import collector_bp
from .service import CollectorService
from ..models.collection import Collection
from ..models.tweet import Tweet

@collector_bp.route('/')
@login_required
def index():
    """صفحه اصلی بخش جمع‌آوری"""
    # دریافت فهرست جمع‌آوری‌های کاربر
    collections = Collection.query.filter_by(user_id=current_user.id).order_by(Collection.created_at.desc()).limit(10).all()
    return render_template('collector/index.html', collections=collections)

@collector_bp.route('/keyword', methods=['POST'])
@login_required
def collect_keyword():
    """جمع‌آوری توییت‌ها با کلمه کلیدی"""
    if request.content_type == 'application/json':
        data = request.get_json()
        keyword = data.get('keyword')
        max_tweets = data.get('max_tweets', 100)
    else:
        keyword = request.form.get('keyword')
        max_tweets = request.form.get('max_tweets', 100, type=int)
    
    if not keyword:
        if request.content_type == 'application/json' or request.is_xhr:
            return jsonify({'status': 'error', 'message': 'کلمه کلیدی وارد نشده است'}), 400
        flash('لطفاً کلمه کلیدی را وارد کنید', 'error')
        return redirect(url_for('collector.index'))
    
    service = CollectorService()
    try:
        collection, count = service.collect_by_keyword(keyword, max_tweets)
        
        # اگر درخواست AJAX باشد، JSON برگردان
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': f'{count} توییت جمع‌آوری شد',
                'collection_id': collection.id
            })
        
        flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
        return redirect(url_for('collector.index'))
    
    except Exception as e:
        current_app.logger.error(f"خطا در جمع‌آوری با کلمه کلیدی: {str(e)}", exc_info=True)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
        flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
        return redirect(url_for('collector.index'))

@collector_bp.route('/username', methods=['POST'])
@login_required
def collect_username():
    """جمع‌آوری توییت‌های یک کاربر"""
    if request.content_type == 'application/json':
        data = request.get_json()
        username = data.get('username')
        max_tweets = data.get('max_tweets', 100)
    else:
        username = request.form.get('username')
        max_tweets = request.form.get('max_tweets', 100, type=int)
    
    if not username:
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'نام کاربری وارد نشده است'}), 400
        flash('لطفاً نام کاربری را وارد کنید', 'error')
        return redirect(url_for('collector.index'))
    
    service = CollectorService()
    try:
        collection, count = service.collect_by_username(username, max_tweets)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': f'{count} توییت جمع‌آوری شد',
                'collection_id': collection.id
            })
        
        flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
        return redirect(url_for('collector.index'))
    
    except Exception as e:
        current_app.logger.error(f"خطا در جمع‌آوری با نام کاربری: {str(e)}", exc_info=True)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
        flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
        return redirect(url_for('collector.index'))

@collector_bp.route('/hashtag', methods=['POST'])
@login_required
def collect_hashtag():
    """جمع‌آوری توییت‌ها با هشتگ"""
    if request.content_type == 'application/json':
        data = request.get_json()
        hashtag = data.get('hashtag')
        max_tweets = data.get('max_tweets', 100)
    else:
        hashtag = request.form.get('hashtag')
        max_tweets = request.form.get('max_tweets', 100, type=int)
    
    if not hashtag:
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'هشتگ وارد نشده است'}), 400
        flash('لطفاً هشتگ را وارد کنید', 'error')
        return redirect(url_for('collector.index'))
    
    service = CollectorService()
    try:
        collection, count = service.collect_by_hashtag(hashtag, max_tweets)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': f'{count} توییت جمع‌آوری شد',
                'collection_id': collection.id
            })
        
        flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
        return redirect(url_for('collector.index'))
    
    except Exception as e:
        current_app.logger.error(f"خطا در جمع‌آوری با هشتگ: {str(e)}", exc_info=True)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
        flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
        return redirect(url_for('collector.index'))

@collector_bp.route('/mentions', methods=['POST'])
@login_required
def collect_mentions():
    """جمع‌آوری توییت‌ها با منشن‌کردن کاربر"""
    if request.content_type == 'application/json':
        data = request.get_json()
        username = data.get('username')
        max_tweets = data.get('max_tweets', 100)
    else:
        username = request.form.get('username')
        max_tweets = request.form.get('max_tweets', 100, type=int)
    
    if not username:
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'نام کاربری وارد نشده است'}), 400
        flash('لطفاً نام کاربری را وارد کنید', 'error')
        return redirect(url_for('collector.index'))
    
    service = CollectorService()
    try:
        collection, count = service.collect_by_mentions(username, max_tweets)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': f'{count} توییت جمع‌آوری شد',
                'collection_id': collection.id
            })
        
        flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
        return redirect(url_for('collector.index'))
    
    except Exception as e:
        current_app.logger.error(f"خطا در جمع‌آوری منشن‌ها: {str(e)}", exc_info=True)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
        flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
        return redirect(url_for('collector.index'))

@collector_bp.route('/list-tweets', methods=['POST'])
@login_required
def collect_list_tweets():
    """جمع‌آوری توییت‌های یک لیست"""
    if request.content_type == 'application/json':
        data = request.get_json()
        list_id = data.get('list_id')
        max_tweets = data.get('max_tweets', 100)
    else:
        list_id = request.form.get('list_id')
        max_tweets = request.form.get('max_tweets', 100, type=int)
    
    if not list_id:
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'شناسه لیست وارد نشده است'}), 400
        flash('لطفاً شناسه لیست را وارد کنید', 'error')
        return redirect(url_for('collector.index'))
    
    service = CollectorService()
    try:
        collection, count = service.collect_list_tweets(list_id, max_tweets)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': f'{count} توییت جمع‌آوری شد',
                'collection_id': collection.id
            })
        
        flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
        return redirect(url_for('collector.index'))
    
    except Exception as e:
        current_app.logger.error(f"خطا در جمع‌آوری توییت‌های لیست: {str(e)}", exc_info=True)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
        flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
        return redirect(url_for('collector.index'))

@collector_bp.route('/tweet-replies', methods=['POST'])
@login_required
def collect_tweet_replies():
    """جمع‌آوری پاسخ‌های یک توییت"""
    if request.content_type == 'application/json':
        data = request.get_json()
        tweet_id = data.get('tweet_id')
        max_tweets = data.get('max_tweets', 100)
    else:
        tweet_id = request.form.get('tweet_id')
        max_tweets = request.form.get('max_tweets', 100, type=int)
    
    if not tweet_id:
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'شناسه توییت وارد نشده است'}), 400
        flash('لطفاً شناسه توییت را وارد کنید', 'error')
        return redirect(url_for('collector.index'))
    
    service = CollectorService()
    try:
        collection, count = service.collect_tweet_replies(tweet_id, max_tweets)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': f'{count} توییت جمع‌آوری شد',
                'collection_id': collection.id
            })
        
        flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
        return redirect(url_for('collector.index'))
    
    except Exception as e:
        current_app.logger.error(f"خطا در جمع‌آوری پاسخ‌های توییت: {str(e)}", exc_info=True)
        
        if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
        flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
        return redirect(url_for('collector.index'))

@collector_bp.route('/collections/<int:collection_id>', methods=['GET'])
@login_required
def view_collection(collection_id):
    """مشاهده جزئیات یک مجموعه جمع‌آوری شده"""
    collection = Collection.query.get_or_404(collection_id)
    
    # اطمینان از دسترسی کاربر
    if collection.user_id != current_user.id and not current_user.is_admin:
        flash('شما اجازه دسترسی به این مجموعه را ندارید', 'error')
        return redirect(url_for('collector.index'))
    
    # دریافت توییت‌های مجموعه با پیجینیشن
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    tweets_query = Tweet.query.filter_by(collection_id=collection_id)
    
    # پارامتر جستجو
    search = request.args.get('search', '')
    if search:
        tweets_query = tweets_query.filter(Tweet.text.ilike(f'%{search}%'))
    
    tweets_pagination = tweets_query.order_by(Tweet.twitter_created_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    return render_template(
        'collector/view_collection.html',
        collection=collection,
        tweets=tweets_pagination.items,
        pagination=tweets_pagination,
        search=search
    )

@collector_bp.route('/collections/<int:collection_id>/delete', methods=['POST'])
@login_required
def delete_collection(collection_id):
    """حذف یک مجموعه جمع‌آوری شده"""
    collection = Collection.query.get_or_404(collection_id)
    
    # اطمینان از دسترسی کاربر
    if collection.user_id != current_user.id and not current_user.is_admin:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'شما اجازه حذف این مجموعه را ندارید'}), 403
        flash('شما اجازه حذف این مجموعه را ندارید', 'error')
        return redirect(url_for('collector.index'))
    
    try:
        # حذف مجموعه و توییت‌های مرتبط
        tweets = Tweet.query.filter_by(collection_id=collection_id).all()
        for tweet in tweets:
            # جدا کردن روابط قبل از حذف
            tweet.hashtags = []
            tweet.mentions = []
        
        # اکنون توییت‌ها را حذف کنید
        Tweet.query.filter_by(collection_id=collection_id).delete()
        
        # حذف مجموعه
        collection_name = collection.name
        Collection.query.filter_by(id=collection_id).delete()
        
        # ذخیره تغییرات
        from ..models import db
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'message': f'مجموعه "{collection_name}" با موفقیت حذف شد'
            })
        
        flash(f'مجموعه "{collection_name}" با موفقیت حذف شد', 'success')
        return redirect(url_for('collector.index'))
    
    except Exception as e:
        current_app.logger.error(f"خطا در حذف مجموعه: {str(e)}", exc_info=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': f'خطا در حذف مجموعه: {str(e)}'}), 500
        
        flash(f'خطا در حذف مجموعه: {str(e)}', 'error')
        return redirect(url_for('collector.index'))