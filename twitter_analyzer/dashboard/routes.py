from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from . import dashboard_bp
from twitter_analyzer.models.tweet import Tweet
from twitter_analyzer.twitter.twitter_api import TwitterAPI

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
    # دریافت پارامتر با بررسی پیش‌فرض
    query = request.args.get('q', '')
    
    # لاگ برای بررسی
    current_app.logger.info(f"Search query: {query}")
    current_app.logger.info(f"All args: {request.args}")
    
    if not query:
        current_app.logger.warning("No query provided")
        return render_template('dashboard/search.html', title='جستجوی توییت‌ها')
    
    try:
        # ایجاد نمونه TwitterAPI 
        twitter_api = TwitterAPI()
        
        # لاگ برای بررسی وضعیت API
        current_app.logger.info("Attempting to search tweets")
        
        results = twitter_api.search_tweets(query)
        
        # لاگ نتایج
        current_app.logger.info(f"Search results: {results}")
        
        return render_template('dashboard/search.html', 
                               title=f'جستجو: {query}', 
                               query=query, 
                               results=results)
    
    except Exception as e:
        # لاگ خطای دقیق
        current_app.logger.error(f"Full error details: {e}", exc_info=True)
        
        return render_template('dashboard/search.html', 
                               title='خطا در جستجو', 
                               error='امکان جستجو در حال حاضر وجود ندارد', 
                               query=query, 
                               results=[])