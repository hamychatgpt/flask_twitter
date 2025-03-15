# twitter_analyzer/text_processing/processor.py
import re
import logging
from typing import List, Dict, Optional, Set, Union, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import emoji
import hazm
from flask import current_app

from .normalizer import TextNormalizer
from .tokenizer import TextTokenizer
from .stopwords import get_stopwords
from .noise_removal import NoiseRemover
from .content_filter import ContentFilter


class TextProcessor:
    """
    کلاس اصلی برای پردازش متن فارسی توییت‌ها

    این کلاس وظایف مختلف پردازش متن را هماهنگ می‌کند:
    - نرمال‌سازی متن فارسی
    - توکنیزه کردن
    - حذف کلمات ایست
    - حذف نویز (لینک، منشن، هشتگ، ایموجی)
    - فیلتر محتوای نامناسب

    همچنین قابلیت پردازش دسته‌ای برای کارایی بیشتر را فراهم می‌کند.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        مقداردهی اولیه کلاس TextProcessor
        
        Args:
            config: دیکشنری تنظیمات اختیاری برای سفارشی‌سازی عملکرد
        """
        self.logger = logging.getLogger("text_processor")
        self.config = config or {}
        
        # تنظیم زبان اصلی پردازش
        self.language = self.config.get('language', 'fa')
        
        # مقداردهی اولیه کامپوننت‌های پردازش متن
        self.normalizer = TextNormalizer(config=self.config.get('normalizer', {}))
        self.tokenizer = TextTokenizer(language=self.language)
        self.stopwords = get_stopwords(self.language)
        self.noise_remover = NoiseRemover(config=self.config.get('noise_remover', {}))
        self.content_filter = ContentFilter(config=self.config.get('content_filter', {}))
        
        # تنظیم پردازش موازی
        self.max_workers = self.config.get('max_workers', 4)
        
        # پیکربندی کش برای فانکشن‌های پرکاربرد
        self._configure_caching()
        
        self.logger.info(f"TextProcessor initialized with language: {self.language}")

    def _configure_caching(self):
        """پیکربندی کش برای بهبود عملکرد"""
        # تنظیم حجم کش برای توابع مختلف
        cache_size = self.config.get('cache_size', 1024)
        
        # اعمال کش برای توابع پرکاربرد
        self.normalize = lru_cache(maxsize=cache_size)(self.normalize)
        self.tokenize = lru_cache(maxsize=cache_size)(self.tokenize)
        self.is_appropriate = lru_cache(maxsize=cache_size)(self.is_appropriate)

    def preprocess(self, text: str, normalize: bool = True, remove_noise: bool = True, 
                   remove_stopwords: bool = True) -> str:
        """
        پیش‌پردازش کامل متن توییت
        
        Args:
            text: متن توییت ورودی
            normalize: آیا نرمال‌سازی انجام شود
            remove_noise: آیا نویز حذف شود
            remove_stopwords: آیا کلمات ایست حذف شوند
            
        Returns:
            متن پیش‌پردازش شده
        """
        if not text:
            return ""
        
        processed_text = text
        
        # مرحله 1: حذف نویز (لینک‌ها، ایموجی‌ها و...)
        if remove_noise:
            processed_text = self.noise_remover.remove_all_noise(processed_text)
        
        # مرحله 2: نرمال‌سازی متن
        if normalize:
            processed_text = self.normalizer.normalize(processed_text)
        
        # مرحله 3: حذف کلمات ایست
        if remove_stopwords:
            tokens = self.tokenizer.tokenize(processed_text)
            tokens = [t for t in tokens if t.strip() and t not in self.stopwords]
            processed_text = ' '.join(tokens)
        
        return processed_text

    def normalize(self, text: str) -> str:
        """
        نرمال‌سازی متن فارسی
        
        Args:
            text: متن ورودی
            
        Returns:
            متن نرمال‌شده
        """
        return self.normalizer.normalize(text)

    def tokenize(self, text: str, keep_stopwords: bool = False) -> List[str]:
        """
        توکنیزه کردن متن به کلمات
        
        Args:
            text: متن ورودی
            keep_stopwords: آیا کلمات ایست حفظ شوند
            
        Returns:
            لیست توکن‌ها (کلمات)
        """
        tokens = self.tokenizer.tokenize(text)
        
        if not keep_stopwords:
            tokens = [t for t in tokens if t not in self.stopwords]
            
        return tokens

    def remove_noise(self, text: str, remove_links: bool = True, remove_mentions: bool = True,
                    remove_hashtags: bool = True, remove_emojis: bool = True) -> str:
        """
        حذف نویز از متن
        
        Args:
            text: متن ورودی
            remove_links: آیا لینک‌ها حذف شوند
            remove_mentions: آیا منشن‌ها حذف شوند
            remove_hashtags: آیا هشتگ‌ها حذف شوند
            remove_emojis: آیا ایموجی‌ها حذف شوند
            
        Returns:
            متن تمیز شده
        """
        return self.noise_remover.remove_noise(
            text, 
            remove_links=remove_links,
            remove_mentions=remove_mentions,
            remove_hashtags=remove_hashtags,
            remove_emojis=remove_emojis
        )

    def extract_features(self, text: str) -> Dict[str, Any]:
        """
        استخراج ویژگی‌های متن
        
        Args:
            text: متن ورودی
            
        Returns:
            دیکشنری ویژگی‌های استخراج شده
        """
        if not text:
            return {
                'length': 0,
                'word_count': 0,
                'mentions': [],
                'hashtags': [],
                'urls': [],
                'emojis': []
            }
        
        # استخراج منشن‌ها
        mentions = re.findall(r'@(\w+)', text)
        
        # استخراج هشتگ‌ها
        hashtags = re.findall(r'#(\w+)', text)
        
        # استخراج لینک‌ها
        urls = re.findall(r'https?://\S+', text)
        
        # استخراج ایموجی‌ها
        emojis = [c for c in text if c in emoji.UNICODE_EMOJI['fa']]
        
        # پیش‌پردازش متن برای شمارش کلمات
        clean_text = self.preprocess(text)
        words = self.tokenize(clean_text, keep_stopwords=True)
        
        return {
            'length': len(text),
            'word_count': len(words),
            'mentions': mentions,
            'hashtags': hashtags,
            'urls': urls,
            'emojis': emojis
        }

    def is_appropriate(self, text: str) -> bool:
        """
        بررسی مناسب بودن محتوا
        
        Args:
            text: متن ورودی
            
        Returns:
            True اگر متن مناسب باشد، False در غیر این صورت
        """
        return self.content_filter.is_appropriate(text)

    def filter_inappropriate(self, text: str) -> str:
        """
        فیلتر محتوای نامناسب
        
        Args:
            text: متن ورودی
            
        Returns:
            متن فیلتر شده
        """
        return self.content_filter.filter_text(text)

    def process_batch(self, texts: List[str], preprocess: bool = True, 
                     extract_features: bool = False, filter_inappropriate: bool = False) -> List[Dict[str, Any]]:
        """
        پردازش دسته‌ای متون برای کارایی بیشتر
        
        Args:
            texts: لیست متن‌های ورودی
            preprocess: آیا پیش‌پردازش انجام شود
            extract_features: آیا ویژگی‌ها استخراج شوند
            filter_inappropriate: آیا محتوای نامناسب فیلتر شود
            
        Returns:
            لیستی از نتایج پردازش برای هر متن
        """
        results = []
        
        # پردازش موازی برای بهبود کارایی
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for text in texts:
                future = executor.submit(
                    self._process_single_text,
                    text,
                    preprocess,
                    extract_features,
                    filter_inappropriate
                )
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error in batch processing: {str(e)}")
                    # اضافه کردن نتیجه خطا
                    results.append({
                        'original': '',
                        'processed': '',
                        'error': str(e)
                    })
        
        return results

    def _process_single_text(self, text: str, preprocess: bool = True,
                            extract_features: bool = False, 
                            filter_inappropriate: bool = False) -> Dict[str, Any]:
        """
        پردازش یک متن تکی - استفاده شده توسط process_batch
        
        Args:
            text: متن ورودی
            preprocess: آیا پیش‌پردازش انجام شود
            extract_features: آیا ویژگی‌ها استخراج شوند
            filter_inappropriate: آیا محتوای نامناسب فیلتر شود
            
        Returns:
            دیکشنری نتایج پردازش
        """
        result = {'original': text}
        
        if filter_inappropriate:
            is_appropriate = self.is_appropriate(text)
            result['is_appropriate'] = is_appropriate
            
            if not is_appropriate:
                text = self.filter_inappropriate(text)
                result['filtered'] = text
        
        if preprocess:
            processed_text = self.preprocess(text)
            result['processed'] = processed_text
        
        if extract_features:
            features = self.extract_features(text)
            result['features'] = features
        
        return result
    
    def get_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        استخراج کلمات کلیدی از متن
        
        Args:
            text: متن ورودی
            top_n: تعداد کلمات کلیدی برتر
            
        Returns:
            لیست (کلمه، امتیاز) برای کلمات کلیدی
        """
        # پیش‌پردازش متن
        processed_text = self.preprocess(text)
        
        # توکنیزه کردن
        tokens = self.tokenize(processed_text, keep_stopwords=False)
        
        if not tokens:
            return []
        
        # شمارش فراوانی کلمات
        word_freq = {}
        for token in tokens:
            if len(token) > 1:  # حذف کاراکترهای تکی
                word_freq[token] = word_freq.get(token, 0) + 1
        
        # محاسبه TF (فراوانی کلمه)
        total_words = len(tokens)
        word_tf = {word: count/total_words for word, count in word_freq.items()}
        
        # مرتب‌سازی بر اساس TF
        sorted_keywords = sorted(word_tf.items(), key=lambda x: x[1], reverse=True)
        
        # بازگرداندن top_n کلمات کلیدی
        return sorted_keywords[:top_n]