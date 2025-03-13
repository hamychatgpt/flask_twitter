from flask import jsonify, request
from . import api_bp
from twitter_analyzer.twitter.twitter_api import TwitterAPI

@api_bp.route('/stats')
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
    
    return jsonify(stats)

@api_bp.route('/search')
def search():
    """API برای جستجوی توییت‌ها"""
    query = request.args.get('q', '')
    count = request.args.get('count', 10, type=int)
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # استفاده از API توییتر
    twitter_api = TwitterAPI()
    results = twitter_api.search_tweets(query)
    
    return jsonify(results)
