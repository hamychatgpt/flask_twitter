"""
آزمون‌های پردازش متن فارسی برای تحلیلگر توییتر با استفاده از pytest
"""

import pytest
import os
import sys

# اضافه کردن مسیر پروژه به sys.path برای import کردن ماژول‌ها
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from twitter_analyzer.text_processing import (
    TextProcessor, 
    TextNormalizer, 
    TextTokenizer, 
    NoiseRemover,
    ContentFilter,
    BatchProcessor,
    get_stopwords
)

# نمونه متن‌های فارسی برای تست
SAMPLE_TEXTS = [
    "سلام دنیا! این یک متن تست فارسی برای پردازش است. #تست @مثال https://example.com",
    "این متن شامل هشتگ‌های #بررسی و #آزمایش است. لطفا @کاربر را منشن کنید 😊",
    "RT @کاربر: این یک ریتوییت است که شامل لینک http://t.co/abc123 می‌باشد",
    "متن شامل کلمات نامناسب مانند احمق و بی‌شعور",
    "لورم ایپسوم متن ساختگی با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک است. #لورم #متن"
]

@pytest.fixture
def text_processor():
    """فیکسچر برای ایجاد نمونه TextProcessor"""
    config = {
        'language': 'fa',
        'normalizer': {
            'remove_diacritics': True,
            'affix_spacing': True,
            'punctuation_spacing': True
        },
        'noise_remover': {
            'preserve_emoji_length': False,
            'preserve_hashtag_content': True
        },
        'content_filter': {
            'censoring_char': '*',
            'min_inappropriate_threshold': 0.1
        }
    }
    
    return TextProcessor(config=config)

@pytest.fixture
def normalizer():
    """فیکسچر برای ایجاد نمونه TextNormalizer"""
    return TextNormalizer()

@pytest.fixture
def tokenizer():
    """فیکسچر برای ایجاد نمونه TextTokenizer"""
    return TextTokenizer(language='fa')

@pytest.fixture
def noise_remover():
    """فیکسچر برای ایجاد نمونه NoiseRemover"""
    return NoiseRemover()

@pytest.fixture
def content_filter():
    """فیکسچر برای ایجاد نمونه ContentFilter"""
    return ContentFilter()

@pytest.fixture
def batch_processor(text_processor):
    """فیکسچر برای ایجاد نمونه BatchProcessor"""
    return BatchProcessor(text_processor=text_processor)

# آزمون‌های TextNormalizer
def test_normalizer_initialization():
    """آزمون مقداردهی اولیه TextNormalizer"""
    normalizer = TextNormalizer()
    assert normalizer is not None
    assert hasattr(normalizer, 'normalize')
    
def test_normalizer_normalize(normalizer):
    """آزمون نرمال‌سازی متن فارسی"""
    for text in SAMPLE_TEXTS:
        normalized = normalizer.normalize(text)
        assert isinstance(normalized, str)
        assert len(normalized) > 0

# آزمون‌های TextTokenizer
def test_tokenizer_initialization():
    """آزمون مقداردهی اولیه TextTokenizer"""
    tokenizer = TextTokenizer(language='fa')
    assert tokenizer is not None
    assert tokenizer.language == 'fa'
    
def test_tokenizer_tokenize(tokenizer):
    """آزمون توکنیزه کردن متن"""
    for text in SAMPLE_TEXTS:
        tokens = tokenizer.tokenize(text)
        assert isinstance(tokens, list)
        # بررسی اینکه توکن‌ها رشته هستند
        assert all(isinstance(token, str) for token in tokens)
        
def test_tokenizer_sentences(tokenizer):
    """آزمون تقسیم متن به جملات"""
    for text in SAMPLE_TEXTS:
        sentences = tokenizer.tokenize_sentences(text)
        assert isinstance(sentences, list)
        assert all(isinstance(sentence, str) for sentence in sentences)

# آزمون‌های NoiseRemover
def test_noise_remover_initialization():
    """آزمون مقداردهی اولیه NoiseRemover"""
    noise_remover = NoiseRemover()
    assert noise_remover is not None
    assert hasattr(noise_remover, 'remove_all_noise')
    
def test_remove_urls(noise_remover):
    """آزمون حذف لینک‌ها"""
    text_with_url = "این متن شامل یک لینک https://example.com است"
    text_without_url = noise_remover.remove_urls(text_with_url)
    assert "https://example.com" not in text_without_url
    
def test_remove_mentions(noise_remover):
    """آزمون حذف منشن‌ها"""
    text_with_mention = "لطفا @کاربر را منشن کنید"
    text_without_mention = noise_remover.remove_mentions(text_with_mention)
    assert "@کاربر" not in text_without_mention
    
def test_remove_hashtags(noise_remover):
    """آزمون حذف هشتگ‌ها"""
    text_with_hashtag = "این متن شامل هشتگ #تست است"
    
    # حالت حفظ محتوا
    text_preserved = noise_remover.remove_hashtags(text_with_hashtag, preserve_content=True)
    assert "#تست" not in text_preserved
    assert "تست" in text_preserved
    
    # حالت حذف کامل
    text_removed = noise_remover.remove_hashtags(text_with_hashtag, preserve_content=False)
    assert "#تست" not in text_removed
    assert "تست" not in text_removed
    
def test_remove_all_noise(noise_remover):
    """آزمون حذف تمام نویزها"""
    text_with_noise = "RT @کاربر: این یک متن نویزدار #هشتگ با لینک https://example.com است 😊"
    text_without_noise = noise_remover.remove_all_noise(text_with_noise)
    
    assert "RT" not in text_without_noise
    assert "@کاربر" not in text_without_noise
    assert "#هشتگ" not in text_without_noise
    assert "https://example.com" not in text_without_noise
    assert "😊" not in text_without_noise

# آزمون‌های ContentFilter
def test_content_filter_initialization():
    """آزمون مقداردهی اولیه ContentFilter"""
    content_filter = ContentFilter()
    assert content_filter is not None
    assert hasattr(content_filter, 'is_appropriate')
    
def test_inappropriate_words(content_filter):
    """آزمون تشخیص کلمات نامناسب"""
    clean_text = "این یک متن مناسب است"
    inappropriate_text = "این متن شامل کلمه نامناسب احمق است"
    
    # بررسی مناسب بودن
    assert content_filter.is_appropriate(clean_text)
    
    # بررسی نامناسب بودن
    inappropriate_words = content_filter.get_inappropriate_words(inappropriate_text)
    assert len(inappropriate_words) > 0
    assert "احمق" in inappropriate_words
    
def test_filter_text(content_filter):
    """آزمون فیلتر کردن متن نامناسب"""
    inappropriate_text = "این متن شامل کلمه نامناسب احمق است"
    
    # سانسور
    censored_text = content_filter.filter_text(inappropriate_text, replacement_method='censor')
    assert "احمق" not in censored_text
    assert "****" in censored_text
    
    # حذف
    removed_text = content_filter.filter_text(inappropriate_text, replacement_method='remove')
    assert "احمق" not in removed_text
    assert "****" not in removed_text

# آزمون‌های TextProcessor
def test_text_processor_initialization():
    """آزمون مقداردهی اولیه TextProcessor"""
    processor = TextProcessor()
    assert processor is not None
    assert hasattr(processor, 'preprocess')
    
def test_preprocess(text_processor):
    """آزمون پیش‌پردازش متن"""
    for text in SAMPLE_TEXTS:
        preprocessed = text_processor.preprocess(text)
        assert isinstance(preprocessed, str)
        
def test_extract_features(text_processor):
    """آزمون استخراج ویژگی‌ها"""
    text = "سلام دنیا! این یک متن تست #آزمایش برای @کاربر است https://example.com 😊"
    features = text_processor.extract_features(text)
    
    assert isinstance(features, dict)
    assert 'length' in features
    assert 'word_count' in features
    assert 'mentions' in features
    assert 'hashtags' in features
    assert 'urls' in features
    assert 'emojis' in features
    
    assert features['length'] > 0
    assert features['word_count'] > 0
    assert '@کاربر' in ' '.join(features['mentions']) or 'کاربر' in ' '.join(features['mentions'])
    assert '#آزمایش' in ' '.join(features['hashtags']) or 'آزمایش' in ' '.join(features['hashtags'])
    assert 'https://example.com' in ' '.join(features['urls'])
    
def test_get_keywords(text_processor):
    """آزمون استخراج کلمات کلیدی"""
    text = "این یک متن طولانی برای تست کلمات کلیدی است. متن طولانی شامل کلمات تکراری برای تست استخراج کلیدواژه‌ها است."
    keywords = text_processor.get_keywords(text, top_n=3)
    
    assert isinstance(keywords, list)
    assert len(keywords) <= 3  # ممکن است کمتر از 3 باشد اگر کلمات کافی نباشند
    assert all(isinstance(item, tuple) and len(item) == 2 for item in keywords)

# آزمون‌های BatchProcessor
def test_batch_processor_initialization(text_processor):
    """آزمون مقداردهی اولیه BatchProcessor"""
    batch_processor = BatchProcessor(text_processor=text_processor)
    assert batch_processor is not None
    assert batch_processor.text_processor == text_processor
    
def test_process_texts(batch_processor):
    """آزمون پردازش دسته‌ای متون"""
    results = batch_processor.process_texts(
        SAMPLE_TEXTS[:2],  # فقط دو متن برای سرعت بیشتر
        preprocess=True,
        extract_features=True,
        filter_inappropriate=True
    )
    
    assert isinstance(results, list)
    assert len(results) == 2
    assert all(isinstance(result, dict) for result in results)
    assert all('original' in result for result in results)
    
def test_get_stats(batch_processor):
    """آزمون دریافت آمار پردازش"""
    # ابتدا یک پردازش انجام می‌دهیم
    batch_processor.process_texts(SAMPLE_TEXTS[:2])
    
    # سپس آمار را دریافت می‌کنیم
    stats = batch_processor.get_stats()
    
    assert isinstance(stats, dict)
    assert 'total_items' in stats
    assert 'processed_items' in stats
    assert 'processing_time' in stats
    assert stats['total_items'] == 2  # تعداد متون پردازش شده
    assert stats['processed_items'] == 2  # تعداد متون پردازش شده