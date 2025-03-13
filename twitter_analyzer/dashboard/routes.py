from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from . import dashboard_bp
from twitter_analyzer.models.tweet import Tweet
from twitter_analyzer.twitter.twitter_api_old_version import TwitterAPI

@dashboard_bp.route('/')
def index():
    """صفحه اصلی داشبورد"""
    # داده‌های نمونه - در یک پروژه واقعی، این داده‌ها از پایگاه داده می‌آیند
    sample_data = {
        'total_tweets': 125,
        'sentiment': {
            'positive': 45,
            'neutral': 65,
            'negative': 15
        },
        'top_hashtags': ['#پایتون', '#فلسک', '#توسعه_وب', '#داده_کاوی', '#هوش_مصنوعی']
    }
    
    return render_template('dashboard/index.html', title='داشبورد', data=sample_data)

@dashboard_bp.route('/analysis')
@login_required
def analysis():
    """صفحه تحلیل توییت‌ها"""
    return render_template('dashboard/analysis.html', title='تحلیل توییت‌ها')

@dashboard_bp.route('/search')
@login_required
def search():
    """جستجوی توییت‌ها"""
    query = request.args.get('q', '')
    
    if not query:
        return render_template('dashboard/search.html', title='جستجوی توییت‌ها')
    
    # در پروژه واقعی، اینجا از API توییتر استفاده می‌کنیم
    twitter_api = TwitterAPI()
    results = twitter_api.search_tweets(query)
    
    return render_template('dashboard/search.html', title=f'جستجو: {query}', query=query, results=results)


