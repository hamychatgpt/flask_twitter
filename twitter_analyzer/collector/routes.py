from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import collector_bp
from .service import CollectorService
from ..models.collection import Collection

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
        if request.content_type == 'application/json':
            return jsonify({'status': 'error', 'message': 'کلمه کلیدی وارد نشده است'}), 400
        flash('لطفاً کلمه کلیدی را وارد کنید', 'error')
        return redirect(url_for('collector.index'))
    
    service = CollectorService()
    try:
        collection, count = service.collect_by_keyword(keyword, max_tweets)
        
        if request.content_type == 'application/json':
            return jsonify({
                'status': 'success',
                'message': f'{count} توییت جمع‌آوری شد',
                'collection_id': collection.id
            })
        
        flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
        return redirect(url_for('collector.index'))
    
    except Exception as e:
        if request.content_type == 'application/json':
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
        if request.content_type == 'application/json':
            return jsonify({'status': 'error', 'message': 'نام کاربری وارد نشده است'}), 400
        flash('لطفاً نام کاربری را وارد کنید', 'error')
        return redirect(url_for('collector.index'))
    
    service = CollectorService()
    try:
        collection, count = service.collect_by_username(username, max_tweets)
        
        if request.content_type == 'application/json':
            return jsonify({
                'status': 'success',
                'message': f'{count} توییت جمع‌آوری شد',
                'collection_id': collection.id
            })
        
        flash(f'جمع‌آوری با موفقیت انجام شد. {count} توییت جمع‌آوری شد.', 'success')
        return redirect(url_for('collector.index'))
    
    except Exception as e:
        if request.content_type == 'application/json':
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
        flash(f'خطا در جمع‌آوری: {str(e)}', 'error')
        return redirect(url_for('collector.index'))