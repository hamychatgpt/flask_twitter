from twitter_analyzer.utils.text_processor import PersianTextProcessor

# ایجاد نمونه از پردازشگر
processor = PersianTextProcessor()

# تست با چند متن نمونه
test_texts = [
    "این یک متن #آزمایشی برای @کاربر است.",
    "با این لینک https://example.com می‌توانید بیشتر بخوانید.",
    "کتاب‌ها و مقاله‌های علمی بسیار جالب هستند."
]

for text in test_texts:
    print("-" * 40)
    print(f"متن اصلی: {text}")
    print(f"متن پردازش شده: {processor.preprocess(text)}")
    print(f"هشتگ‌ها: {processor.extract_hashtags(text)}")
    print(f"منشن‌ها: {processor.extract_mentions(text)}")