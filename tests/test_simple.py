"""
اسکریپت عیب‌یابی برای مشکل پردازش متن
"""
import sys
import re

def debug_text_processing():
    print("=== آغاز عیب‌یابی پردازش متن ===")
    
    # بررسی امکان دسترسی به مدل‌ها
    try:
        from twitter_analyzer.models.tweet import Tweet
        from twitter_analyzer.models import db
        print("✅ مدل‌های دیتابیس با موفقیت import شدند")
    except Exception as e:
        print(f"❌ خطا در بارگذاری مدل‌ها: {str(e)}")
        return
    
    # بررسی وجود توییت‌ها
    try:
        tweet_count = Tweet.query.count()
        print(f"📊 تعداد توییت‌ها در دیتابیس: {tweet_count}")
        
        if tweet_count == 0:
            print("❌ هیچ توییتی در دیتابیس وجود ندارد!")
            return
            
        # بررسی اولین توییت
        first_tweet = Tweet.query.first()
        print(f"📝 اولین توییت (ID: {first_tweet.id}):")
        
        # بررسی متن توییت
        if hasattr(first_tweet, 'text'):
            if first_tweet.text:
                print(f"متن: '{first_tweet.text[:100]}...'")
                print(f"طول متن: {len(first_tweet.text)} کاراکتر")
            else:
                print("❌ متن توییت خالی است!")
        else:
            print("❌ فیلد 'text' در مدل Tweet وجود ندارد!")
            return
        
        # بررسی فیلد processed_text
        has_processed_field = hasattr(first_tweet, 'processed_text')
        print(f"آیا فیلد processed_text وجود دارد؟ {has_processed_field}")
        
        # آزمایش regex ساده روی متن
        if first_tweet.text:
            # تست 1: حذف URL
            test_url_removal = re.sub(r'https?://\S+', '', first_tweet.text)
            print(f"\n🔍 تست حذف URL:")
            print(f"نتیجه: '{test_url_removal[:100]}...'")
            
            # تست 2: حذف منشن‌ها
            test_mention_removal = re.sub(r'@\w+', '', first_tweet.text)
            print(f"\n🔍 تست حذف منشن:")
            print(f"نتیجه: '{test_mention_removal[:100]}...'")
            
            # تست 3: ساده regex emoji
            try:
                emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F]')
                test_emoji_removal = re.sub(emoji_pattern, '', first_tweet.text)
                print(f"\n✅ تست regex ایموجی موفق بود")
            except Exception as e:
                print(f"\n❌ خطا در الگوی regex ایموجی: {str(e)}")
                
        # اجرای تست روی ماژول NoiseRemover
        try:
            from twitter_analyzer.text_processing.noise_removal import NoiseRemover
            print("\n🔍 بررسی کلاس NoiseRemover:")
            remover = NoiseRemover()
            print("✅ کلاس NoiseRemover با موفقیت ایجاد شد")
        except Exception as e:
            print(f"❌ خطا در ایجاد NoiseRemover: {str(e)}")
            
    except Exception as e:
        print(f"❌ خطای کلی: {str(e)}")

if __name__ == "__main__":
    # اجرای با Flask context
    try:
        from flask import current_app
        from twitter_analyzer import create_app
        print("🔄 در حال راه‌اندازی Flask app...")
        app = create_app()
        
        with app.app_context():
            debug_text_processing()
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی Flask: {str(e)}")