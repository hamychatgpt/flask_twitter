"""
تست‌های خودکار برای لایه ترجمه داده‌های API توییتر
"""

import unittest
from datetime import datetime
import json
import os
from twitter_analyzer.twitter.transformers import TwitterDataTransformer

class TestTwitterDataTransformer(unittest.TestCase):
    """آزمون‌ها برای کلاس TwitterDataTransformer"""
    
    def setUp(self):
        """تنظیمات قبل از اجرای هر آزمون"""
        self.transformer = TwitterDataTransformer()
        
        # بارگذاری داده‌های آزمون
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_data_path = os.path.join(current_dir, 'data', 'twitter_sample_data.json')
        
        with open(test_data_path, 'r', encoding='utf-8') as f:
            self.test_data = json.load(f)
    
    def test_transform_tweet_basic(self):
        """آزمون تبدیل پایه توییت"""
        sample_tweet = {
            "id": "1234567890",
            "text": "This is a test tweet",
            "created_at": "Wed Oct 10 20:19:24 +0000 2023",
            "author": {
                "id": "9876543210",
                "userName": "testuser",
                "displayName": "Test User",
                "profileImageUrl": "https://example.com/profile.jpg"
            }
        }
        
        result = self.transformer.transform_tweet(sample_tweet)
        
        # بررسی فیلدهای اصلی
        self.assertEqual(result["tweet_id"], "1234567890")
        self.assertEqual(result["text"], "This is a test tweet")
        self.assertIsInstance(result["created_at"], datetime)
        self.assertEqual(result["user"]["username"], "testuser")
    
    def test_transform_tweet_with_entities(self):
        """آزمون تبدیل توییت با entities"""
        sample_tweet = {
            "id": "1234567890",
            "text": "Test tweet with #hashtag and @mention",
            "created_at": "Wed Oct 10 20:19:24 +0000 2023",
            "author": {"userName": "testuser"},
            "entities": {
                "hashtags": [{"text": "hashtag"}],
                "user_mentions": [{"screen_name": "mention", "id": "5555555"}]
            }
        }
        
        result = self.transformer.transform_tweet(sample_tweet)
        
        # بررسی entities
        self.assertEqual(len(result["entities"]["hashtags"]), 1)
        self.assertEqual(result["entities"]["hashtags"][0]["text"], "hashtag")
        self.assertEqual(len(result["entities"]["mentions"]), 1)
        self.assertEqual(result["entities"]["mentions"][0]["username"], "mention")
    
    def test_transform_tweet_with_metrics(self):
        """آزمون تبدیل توییت با آمار"""
        sample_tweet = {
            "id": "1234567890",
            "text": "Test tweet with metrics",
            "author": {"userName": "testuser"},
            "likeCount": 10,
            "retweetCount": 5,
            "replyCount": 3,
            "quoteCount": 2
        }
        
        result = self.transformer.transform_tweet(sample_tweet)
        
        # بررسی metrics
        self.assertEqual(result["metrics"]["likes_count"], 10)
        self.assertEqual(result["metrics"]["retweets_count"], 5)
        self.assertEqual(result["metrics"]["replies_count"], 3)
        self.assertEqual(result["metrics"]["quotes_count"], 2)
    
    def test_transform_tweet_with_reply_info(self):
        """آزمون تبدیل توییت با اطلاعات پاسخ"""
        sample_tweet = {
            "id": "1234567890",
            "text": "Test reply",
            "author": {"userName": "testuser"},
            "in_reply_to_status_id": "9876543210",
            "in_reply_to_user_id": "5555555555",
            "in_reply_to_screen_name": "originaluser"
        }
        
        result = self.transformer.transform_tweet(sample_tweet)
        
        # بررسی اطلاعات پاسخ
        self.assertEqual(result["reply_info"]["in_reply_to_tweet_id"], "9876543210")
        self.assertEqual(result["reply_info"]["in_reply_to_user_id"], "5555555555")
        self.assertEqual(result["reply_info"]["in_reply_to_username"], "originaluser")
    
    def test_transform_tweet_with_media(self):
        """آزمون تبدیل توییت با رسانه"""
        sample_tweet = {
            "id": "1234567890",
            "text": "Test tweet with media",
            "author": {"userName": "testuser"},
            "entities": {
                "media": [
                    {
                        "media_url_https": "https://example.com/image.jpg",
                        "type": "photo",
                        "url": "https://t.co/shorturl"
                    }
                ]
            }
        }
        
        result = self.transformer.transform_tweet(sample_tweet)
        
        # بررسی رسانه
        self.assertEqual(len(result["entities"]["media"]), 1)
        self.assertEqual(result["entities"]["media"][0]["media_url"], "https://example.com/image.jpg")
        self.assertEqual(result["entities"]["media"][0]["type"], "photo")
    
    def test_extract_tweets_list_from_different_structures(self):
        """آزمون استخراج لیست توییت‌ها از ساختارهای مختلف"""
        # ساختار 1: لیست توییت‌ها
        struct1 = [{"id": "1"}, {"id": "2"}]
        result1 = self.transformer._extract_tweets_list(struct1)
        self.assertEqual(len(result1), 2)
        
        # ساختار 2: دیکشنری با کلید tweets
        struct2 = {"tweets": [{"id": "1"}, {"id": "2"}]}
        result2 = self.transformer._extract_tweets_list(struct2)
        self.assertEqual(len(result2), 2)
        
        # ساختار 3: دیکشنری پیچیده‌تر
        struct3 = {"tweets": {"results": [{"id": "1"}, {"id": "2"}]}}
        result3 = self.transformer._extract_tweets_list(struct3)
        self.assertEqual(len(result3), 2)
        
        # ساختار 4: توییت تکی
        struct4 = {"id": "1", "text": "Single tweet"}
        result4 = self.transformer._extract_tweets_list(struct4)
        self.assertEqual(len(result4), 1)
    
    def test_transform_user(self):
        """آزمون تبدیل کاربر"""
        sample_user = {
            "id": "1234567890",
            "userName": "testuser",
            "displayName": "Test User",
            "description": "This is a test user bio",
            "location": "Test Location",
            "followers": 100,
            "following": 50,
            "profileImageUrl": "https://example.com/profile.jpg",
            "isBlueVerified": True
        }
        
        result = self.transformer.transform_user(sample_user)
        
        # بررسی اطلاعات کاربر
        self.assertEqual(result["user_id"], "1234567890")
        self.assertEqual(result["username"], "testuser")
        self.assertEqual(result["display_name"], "Test User")
        self.assertEqual(result["bio"], "This is a test user bio")
        self.assertEqual(result["location"], "Test Location")
        self.assertEqual(result["followers_count"], 100)
        self.assertEqual(result["following_count"], 50)
        self.assertEqual(result["profile_image_url"], "https://example.com/profile.jpg")
        self.assertTrue(result["verified"])
    
    def test_parse_different_date_formats(self):
        """آزمون تبدیل فرمت‌های مختلف تاریخ"""
        # فرمت 1: توییتر کلاسیک
        date1 = "Wed Oct 10 20:19:24 +0000 2023"
        result1 = self.transformer._parse_date(date1)
        self.assertIsInstance(result1, datetime)
        self.assertEqual(result1.year, 2023)
        self.assertEqual(result1.month, 10)
        self.assertEqual(result1.day, 10)
        
        # فرمت 2: ISO با میلی‌ثانیه
        date2 = "2023-10-10T20:19:24.000Z"
        result2 = self.transformer._parse_date(date2)
        self.assertIsInstance(result2, datetime)
        self.assertEqual(result2.year, 2023)
        self.assertEqual(result2.month, 10)
        self.assertEqual(result2.day, 10)
        
        # فرمت 3: ISO بدون میلی‌ثانیه
        date3 = "2023-10-10T20:19:24Z"
        result3 = self.transformer._parse_date(date3)
        self.assertIsInstance(result3, datetime)
        self.assertEqual(result3.year, 2023)
        self.assertEqual(result3.month, 10)
        self.assertEqual(result3.day, 10)
        
        # فرمت 4: تاریخ و زمان ساده
        date4 = "2023-10-10 20:19:24"
        result4 = self.transformer._parse_date(date4)
        self.assertIsInstance(result4, datetime)
        self.assertEqual(result4.year, 2023)
        self.assertEqual(result4.month, 10)
        self.assertEqual(result4.day, 10)

if __name__ == '__main__':
    unittest.main()