from flask import jsonify, request, current_app
from flask_login import login_required
from . import api_bp
from .utils import api_response, handle_api_error, get_twitter_api_stats
from ..extensions import cache
from ..twitter.twitter_api import TwitterAPI

@api_bp.route('/stats')
@handle_api_error
def get_stats():
    """API برای دریافت آمار کلی"""
    # داده‌های نمونه - در پروژه واقعی این داده‌ها از پایگاه داده می‌آیند
    stats = {
        'tweet_count': 125,
        'sentiment': {
            'positive': 45,
            'neutral': 65,
            'negative': 15
        },
        'top_hashtags': ['#پایتون', '#فلسک', '#توسعه_وب', '#داده_کاوی', '#هوش_مصنوعی']
    }
    
    return api_response(stats)

@api_bp.route('/search')
@handle_api_error
def search():
    """API برای جستجوی توییت‌ها"""
    query = request.args.get('q', '')
    count = request.args.get('count', 10, type=int)
    cache_buster = request.args.get('no_cache', False, type=bool)
    
    if not query:
        return api_response(status="error", message="No query provided", code=400)
    
    # استفاده از API توییتر
    twitter_api = current_app.extensions.get('twitter_api')
    
    # استفاده از کش برای جستجوهای تکراری
    cache_key = f"search_tweets_{query}_{count}"
    
    if not cache_buster:
        # سعی در دریافت از کش
        cached_results = cache.get(cache_key)
        if cached_results:
            current_app.logger.info(f"Using cached results for query: {query}")
            return api_response(cached_results)
    
    # اگر نتایج در کش نباشد، جستجو را اجرا می‌کنیم
    current_app.logger.info(f"Performing search for query: {query}")
    results = twitter_api.search_tweets(query)
    
    # ذخیره در کش با TTL کوتاه (1 دقیقه)
    cache.set(cache_key, results, timeout=60)
    
    return api_response(results)

@api_bp.route('/twitter/api-stats')
@login_required
@handle_api_error
def twitter_api_stats():
    """API برای دریافت آمار TwitterAPI"""
    return api_response(get_twitter_api_stats())

@api_bp.route('/cache/clear', methods=['POST'])
@login_required
@handle_api_error
def clear_cache():
    """API برای پاکسازی کش"""
    pattern = request.json.get('pattern') if request.is_json else None
    
    twitter_api = current_app.extensions.get('twitter_api')
    result = twitter_api.clear_cache(pattern)
    
    return api_response(message=result)

@api_bp.route('/rate-limit/reset', methods=['POST'])
@login_required
@handle_api_error
def reset_rate_limit_stats():
    """API برای بازنشانی آمار Rate Limit"""
    twitter_api = current_app.extensions.get('twitter_api')
    result = twitter_api.reset_rate_limit_stats()
    
    return api_response(message=result)