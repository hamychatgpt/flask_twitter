from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from . import api_bp
from ..models.collection import Collection
from ..models.tweet import Tweet
from .utils import api_response, handle_api_error


@api_bp.route('/collections')
@login_required
@handle_api_error
def get_collections():
    """API برای دریافت لیست مجموعه‌های جمع‌آوری شده"""
    # دریافت فهرست مجموعه‌های کاربر
    collections = Collection.query.filter_by(user_id=current_user.id).order_by(Collection.created_at.desc()).limit(10).all()
    
    collections_data = []
    for collection in collections:
        # استخراج نوع جمع‌آوری از اولین قاعده
        rule_type = None
        if collection.rules.count() > 0:
            rule_type = collection.rules.first().rule_type
        
        # تبدیل به فرمت قابل ارسال
        collections_data.append({
            'id': collection.id,
            'name': collection.name,
            'description': collection.description,
            'status': collection.status,
            'started_at': collection.started_at.isoformat() if collection.started_at else None,
            'finished_at': collection.finished_at.isoformat() if collection.finished_at else None,
            'total_tweets': collection.total_tweets,
            'rule_type': rule_type
        })
    
    return api_response(collections=collections_data)


@api_bp.route('/collections/<int:collection_id>')
@login_required
@handle_api_error
def get_collection(collection_id):
    """API برای دریافت اطلاعات یک مجموعه"""
    collection = Collection.query.get_or_404(collection_id)
    
    # بررسی دسترسی کاربر
    if collection.user_id != current_user.id and not current_user.is_admin:
        return api_response(status="error", message="شما اجازه دسترسی به این مجموعه را ندارید", code=403)
    
    # استخراج اطلاعات قواعد
    rules = []
    for rule in collection.rules:
        rules.append({
            'id': rule.id,
            'rule_type': rule.rule_type,
            'value': rule.value
        })
    
    # دریافت تعداد توییت‌ها
    tweets_count = Tweet.query.filter_by(collection_id=collection_id).count()
    
    collection_data = {
        'id': collection.id,
        'name': collection.name,
        'description': collection.description,
        'status': collection.status,
        'started_at': collection.started_at.isoformat() if collection.started_at else None,
        'finished_at': collection.finished_at.isoformat() if collection.finished_at else None,
        'total_tweets': collection.total_tweets,
        'max_tweets': collection.max_tweets,
        'rules': rules,
        'tweets_count': tweets_count
    }
    
    return api_response(collection=collection_data)


@api_bp.route('/collections/<int:collection_id>/tweets')
@login_required
@handle_api_error
def get_collection_tweets(collection_id):
    """API برای دریافت توییت‌های یک مجموعه"""
    collection = Collection.query.get_or_404(collection_id)
    
    # بررسی دسترسی کاربر
    if collection.user_id != current_user.id and not current_user.is_admin:
        return api_response(status="error", message="شما اجازه دسترسی به این مجموعه را ندارید", code=403)
    
    # پارامترهای پیجینیشن
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # پارامتر جستجو
    search = request.args.get('search', '')
    
    # ساخت کوئری
    query = Tweet.query.filter_by(collection_id=collection_id)
    
    # اعمال فیلتر جستجو
    if search:
        query = query.filter(Tweet.text.ilike(f'%{search}%'))
    
    # پیجینیشن
    pagination = query.order_by(Tweet.twitter_created_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    # تبدیل به فرمت قابل ارسال
    tweets_data = []
    for tweet in pagination.items:
        # اطلاعات کاربر توییتر
        user_data = None
        if tweet.twitter_user:
            user_data = {
                'id': tweet.twitter_user.id,
                'username': tweet.twitter_user.username,
                'display_name': tweet.twitter_user.display_name,
                'profile_image_url': tweet.twitter_user.profile_image_url
            }
        
        # هشتگ‌ها
        hashtags = [{'id': hashtag.id, 'text': hashtag.text} for hashtag in tweet.hashtags]
        
        # منشن‌ها
        mentions = [{'id': mention.id, 'username': mention.username} for mention in tweet.mentions]
        
        tweets_data.append({
            'id': tweet.id,
            'twitter_id': tweet.twitter_id,
            'text': tweet.text,
            'created_at': tweet.twitter_created_at.isoformat() if tweet.twitter_created_at else None,
            'user': user_data,
            'likes_count': tweet.likes_count,
            'retweets_count': tweet.retweets_count,
            'replies_count': tweet.replies_count,
            'quotes_count': tweet.quotes_count,
            'language': tweet.language,
            'has_media': tweet.has_media,
            'hashtags': hashtags,
            'mentions': mentions
        })
    
    return api_response(
        tweets=tweets_data,
        pagination={
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'next_num': pagination.next_num,
            'prev_num': pagination.prev_num
        }
    )


@api_bp.route('/test-text-processor', methods=['GET'])
def test_text_processor():
    """Route آزمایشی برای تست پردازشگر متن فارسی"""
    from ..utils.text_processor import PersianTextProcessor
    
    # ایجاد نمونه پردازشگر
    processor = PersianTextProcessor()
    
    # متن‌های آزمایشی
    test_texts = [
        "این یک متن #آزمایشی برای @کاربر است.",
        "کتاب‌ها و مقاله‌های علمی بسیار جالب هستند.",
        "کانال تلگرام ما را دنبال کنید برای تخفیف ویژه!",
        "This is a test text with #hashtag and @mention."
    ]
    
    results = []
    for text in test_texts:
        result = {
            'original': text,
            'processed': processor.preprocess(text),
            'hashtags': processor.extract_hashtags(text),
            'mentions': processor.extract_mentions(text),
            'language': processor.detect_language(text),
            'is_spam': processor.is_spam(text)[0],
            'spam_reason': processor.is_spam(text)[1]
        }
        results.append(result)
    
    return jsonify(results)