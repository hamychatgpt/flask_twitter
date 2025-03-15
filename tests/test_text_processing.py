# test_text_processing.py
from twitter_analyzer.text_processing import TextProcessor, NoiseRemover

# تست NoiseRemover
remover = NoiseRemover()
sample_text = "این یک متن نمونه با لینک https://example.com و منشن @user و هشتگ #هشتگ است 😊"
print("Original:", sample_text)
print("Removed URLs:", remover.remove_urls(sample_text))
print("Removed mentions:", remover.remove_mentions(sample_text))
print("Removed hashtags:", remover.remove_hashtags(sample_text))
print("Removed emojis:", remover.remove_emojis(sample_text))
print("Removed all:", remover.remove_all_noise(sample_text))

# تست کامل پردازش متن
processor = TextProcessor()
processed = processor.preprocess(sample_text)
print("\nFull preprocessing:", processed)

# تست فیچرهای استخراج شده
features = processor.extract_features(sample_text)
print("\nExtracted features:", features)