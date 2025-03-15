# twitter_analyzer/text_processing/cli.py
import click
from flask.cli import with_appcontext
from flask import current_app
from ..models.tweet import Tweet
from ..models import db
from .processor import TextProcessor
from datetime import datetime


@click.group(name='text')
def text_commands():
    """دستورات مرتبط با پردازش متن"""
    pass


@text_commands.command('preprocess')
@click.option('--limit', default=1000, help='حداکثر تعداد توییت برای پردازش')
@click.option('--batch-size', default=100, help='اندازه هر دسته برای پردازش')
@click.option('--reset', is_flag=True, help='نادیده گرفتن توییت‌های قبلا پردازش شده')
@with_appcontext
def preprocess_tweets_command(limit, batch_size, reset):
    """پیش‌پردازش توییت‌های ذخیره شده در دیتابیس"""
    # ایجاد نمونه TextProcessor
    processor = TextProcessor()
    
    # دریافت توییت‌های پردازش نشده
    query = Tweet.query
    if not reset:
        query = query.filter(Tweet.is_processed == False)
    
    tweets = query.limit(limit).all()
    
    click.echo(f"Found {len(tweets)} tweets to process")
    
    # پردازش در دسته‌ها
    total_processed = 0
    
    with click.progressbar(length=len(tweets), label='پردازش توییت‌ها') as bar:
        for i in range(0, len(tweets), batch_size):
            batch = tweets[i:i+batch_size]
            
            # استخراج متن توییت‌ها
            tweet_texts = [tweet.text for tweet in batch]
            
            # پردازش متن‌ها
            processed_results = processor.process_batch(
                tweet_texts,
                preprocess=True,
                extract_features=True,
                filter_inappropriate=True
            )
            
            # به‌روزرسانی توییت‌ها در دیتابیس
            for j, tweet in enumerate(batch):
                if j < len(processed_results):
                    result = processed_results[j]
                    
                    # بررسی وجود خطا
                    if 'error' in result:
                        current_app.logger.error(f"Error processing tweet {tweet.id}: {result['error']}")
                        continue
                    
                    # ذخیره متن پیش‌پردازش شده
                    tweet.processed_text = result.get('processed', '')
                    
                    # ذخیره ویژگی‌های استخراج شده
                    if 'features' in result:
                        # ذخیره تعداد کلمات
                        tweet.word_count = result['features'].get('word_count', 0)
                        
                        # هشتگ‌ها و منشن‌ها در مدل اصلی ذخیره می‌شوند
                    
                    # بررسی مناسب بودن محتوا
                    if 'is_appropriate' in result:
                        tweet.is_appropriate = result['is_appropriate']
                        
                        # فیلترینگ محتوای نامناسب
                        if not tweet.is_appropriate:
                            tweet.is_filtered = True
                            tweet.filter_reason = "inappropriate_content"
                    
                    # علامت‌گذاری توییت به عنوان پردازش شده
                    tweet.is_processed = True
                    
                    # ذخیره تاریخ پردازش
                    tweet.processing_date = datetime.utcnow()
                    
                    total_processed += 1
            
            # ذخیره تغییرات در دیتابیس
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error saving processed tweets to database: {str(e)}")
            
            # به‌روزرسانی نوار پیشرفت
            bar.update(len(batch))
    
    click.echo(f"Successfully processed {total_processed} tweets")


@text_commands.command('extract-keywords')
@click.option('--collection-id', type=int, help='شناسه مجموعه برای استخراج کلمات کلیدی')
@with_appcontext
def extract_keywords_command(collection_id):
    """استخراج کلمات کلیدی از توییت‌های یک مجموعه"""
    # ایجاد نمونه TextProcessor
    processor = TextProcessor()
    
    # دریافت مجموعه و توییت‌های آن
    from ..models.collection import Collection
    collection = Collection.query.get(collection_id)
    
    if not collection:
        click.echo(f"Collection with ID {collection_id} not found", err=True)
        return
    
    # دریافت توییت‌های مجموعه
    tweets = Tweet.query.filter_by(collection_id=collection_id).all()
    
    if not tweets:
        click.echo(f"No tweets found in collection: {collection.name}", err=True)
        return
    
    click.echo(f"Extracting keywords from {len(tweets)} tweets in collection: {collection.name}")
    
    # ترکیب متن همه توییت‌ها
    all_text = " ".join([tweet.processed_text or tweet.text for tweet in tweets])
    
    # استخراج کلمات کلیدی
    keywords = processor.get_keywords(all_text, top_n=20)
    
    # نمایش کلمات کلیدی
    click.echo("\nTop keywords:")
    for keyword, score in keywords:
        click.echo(f"{keyword}: {score:.4f}")


@text_commands.command('filter-inappropriate')
@click.option('--collection-id', type=int, help='شناسه مجموعه برای فیلتر محتوای نامناسب')
@with_appcontext
def filter_inappropriate_command(collection_id):
    """فیلتر توییت‌های با محتوای نامناسب"""
    # ایجاد نمونه ContentFilter
    from .content_filter import ContentFilter
    content_filter = ContentFilter()
    
    # دریافت مجموعه و توییت‌های آن
    from ..models.collection import Collection
    collection = Collection.query.get(collection_id)
    
    if not collection:
        click.echo(f"Collection with ID {collection_id} not found", err=True)
        return
    
    # دریافت توییت‌های مجموعه
    tweets = Tweet.query.filter_by(collection_id=collection_id, is_filtered=False).all()
    
    if not tweets:
        click.echo(f"No unfiltered tweets found in collection: {collection.name}", err=True)
        return
    
    click.echo(f"Checking {len(tweets)} tweets for inappropriate content in collection: {collection.name}")
    
    # بررسی محتوای نامناسب
    inappropriate_count = 0
    
    with click.progressbar(tweets, label='بررسی محتوا') as bar:
        for tweet in bar:
            # بررسی مناسب بودن محتوا
            is_appropriate = content_filter.is_appropriate(tweet.text)
            
            # به‌روزرسانی توییت
            tweet.is_appropriate = is_appropriate
            
            # فیلتر کردن توییت‌های نامناسب
            if not is_appropriate:
                tweet.is_filtered = True
                tweet.filter_reason = "inappropriate_content"
                inappropriate_count += 1
    
    # ذخیره تغییرات
    try:
        db.session.commit()
        click.echo(f"Found and filtered {inappropriate_count} inappropriate tweets")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error saving filtered tweets: {str(e)}", err=True)


def init_app(app):
    """افزودن دستورات CLI به برنامه"""
    app.cli.add_command(text_commands)