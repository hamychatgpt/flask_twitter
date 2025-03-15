# twitter_analyzer/text_processing/content_filter.py
import re
import os
import json
import logging
from typing import Dict, Any, Optional, Set, List, Tuple
from pathlib import Path


class ContentFilter:
    """
    کلاس فیلتر محتوای نامناسب در متن فارسی

    این کلاس قابلیت‌های تشخیص و فیلتر محتوای نامناسب را ارائه می‌کند:
    - تشخیص کلمات زشت و توهین‌آمیز
    - فیلتر کردن محتوای نامناسب (سانسور یا حذف)
    - امکان افزودن فهرست‌های سفارشی
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        مقداردهی اولیه کلاس ContentFilter

        Args:
            config: دیکشنری تنظیمات
        """
        self.logger = logging.getLogger("content_filter")
        self.config = config or {}
        
        # بارگذاری فهرست‌های کلمات نامناسب
        self.inappropriate_words = set()
        self.censored_replacements = {}
        
        # تنظیمات فیلتر
        self.censoring_char = self.config.get('censoring_char', '*')
        self.min_inappropriate_threshold = self.config.get('min_inappropriate_threshold', 0.1)
        self.custom_words_path = self.config.get('custom_words_path', None)
        
        # بارگذاری کلمات نامناسب پیش‌فرض
        self._load_default_inappropriate_words()
        
        # بارگذاری فهرست سفارشی اگر وجود داشته باشد
        if self.custom_words_path:
            self._load_custom_inappropriate_words(self.custom_words_path)
        
        # کامپایل الگوهای رجکس
        self._compile_patterns()

    def _load_default_inappropriate_words(self):
        """بارگذاری فهرست پیش‌فرض کلمات نامناسب فارسی"""
        # فهرست اولیه از کلمات نامناسب فارسی شامل فحش، توهین و کلمات زشت
        # این فهرست به صورت پیش‌فرض محدود است و باید با فهرست سفارشی تکمیل شود
        default_inappropriate_words = {
            "فحش", "توهین", "زشت", "احمق", "نفهم", "بی‌شعور", "بیشعور", 
            "عوضی", "آشغال", "کثافت", "لجن", "بی‌خاصیت", "بی‌لیاقت", "جاکش", 
            "بی‌ناموس", "بیناموس", "حرامزاده", "قرتی", "گاو", "خر", "الاغ", 
            "حیوان", "بی‌شرف", "بی‌وجدان", "کودن", "نادان", "ابله", "گوساله",
        }
        
        # اضافه کردن به فهرست اصلی
        self.inappropriate_words.update(default_inappropriate_words)
        
        # تعریف جایگزین‌ها برای سانسور
        for word in default_inappropriate_words:
            self.censored_replacements[word] = self.censoring_char * len(word)

    def _load_custom_inappropriate_words(self, filepath: str):
        """
        بارگذاری فهرست سفارشی کلمات نامناسب از فایل JSON
        
        Args:
            filepath: مسیر فایل JSON حاوی کلمات نامناسب
        """
        if not os.path.exists(filepath):
            self.logger.warning(f"Custom inappropriate words file not found: {filepath}")
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                custom_words = json.load(f)
                
                # اضافه کردن کلمات ساده
                if 'words' in custom_words and isinstance(custom_words['words'], list):
                    self.inappropriate_words.update(custom_words['words'])
                    
                    # تعریف جایگزین‌ها برای سانسور
                    for word in custom_words['words']:
                        self.censored_replacements[word] = self.censoring_char * len(word)
                
                # اضافه کردن جایگزین‌های سفارشی
                if 'replacements' in custom_words and isinstance(custom_words['replacements'], dict):
                    for word, replacement in custom_words['replacements'].items():
                        self.inappropriate_words.add(word)
                        self.censored_replacements[word] = replacement
                        
        except Exception as e:
            self.logger.error(f"Error loading custom inappropriate words: {e}")

    def _compile_patterns(self):
        """کامپایل الگوهای رجکس برای تشخیص کارآمدتر"""
        # ایجاد الگوی رجکس برای کلمات نامناسب
        pattern_parts = []
        for word in self.inappropriate_words:
            # escape کردن کاراکترهای خاص
            escaped_word = re.escape(word)
            # اضافه کردن مرز کلمه برای جلوگیری از تطبیق بخشی از کلمات
            pattern_parts.append(r'\b' + escaped_word + r'\b')
            
        if pattern_parts:
            pattern_str = '|'.join(pattern_parts)
            self.inappropriate_pattern = re.compile(pattern_str, re.IGNORECASE)
        else:
            # الگوی خالی که هیچوقت تطبیق نمی‌کند
            self.inappropriate_pattern = re.compile(r'^\b$')

    def is_appropriate(self, text: str) -> bool:
        """
        بررسی مناسب بودن محتوا
        
        Args:
            text: متن ورودی
            
        Returns:
            True اگر متن مناسب باشد، False در غیر این صورت
        """
        if not text:
            return True
            
        # بررسی وجود کلمات نامناسب
        inappropriate_matches = self.inappropriate_pattern.findall(text)
        
        # تشخیص بر اساس تعداد کلمات نامناسب و آستانه
        if inappropriate_matches:
            total_words = len(text.split())
            inappropriate_ratio = len(inappropriate_matches) / total_words
            
            return inappropriate_ratio < self.min_inappropriate_threshold
            
        return True

    def filter_text(self, text: str, replacement_method: str = 'censor') -> str:
        """
        فیلتر محتوای نامناسب
        
        Args:
            text: متن ورودی
            replacement_method: روش جایگزینی ('censor', 'remove', 'custom')
            
        Returns:
            متن فیلتر شده
        """
        if not text:
            return ""
            
        filtered_text = text
        
        if replacement_method == 'remove':
            # حذف کامل کلمات نامناسب
            filtered_text = self.inappropriate_pattern.sub('', filtered_text)
            
        elif replacement_method == 'custom':
            # استفاده از جایگزین‌های سفارشی
            for word, replacement in self.censored_replacements.items():
                pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                filtered_text = pattern.sub(replacement, filtered_text)
                
        else:  # 'censor' (پیش‌فرض)
            # سانسور کلمات نامناسب
            def replace_with_censored(match):
                word = match.group(0)
                return self.censoring_char * len(word)
                
            filtered_text = self.inappropriate_pattern.sub(replace_with_censored, filtered_text)
        
        # حذف فاصله‌های اضافی
        filtered_text = re.sub(r'\s+', ' ', filtered_text).strip()
        
        return filtered_text

    def get_inappropriate_words(self, text: str) -> List[str]:
        """
        استخراج کلمات نامناسب از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            لیست کلمات نامناسب یافت شده
        """
        if not text:
            return []
            
        return self.inappropriate_pattern.findall(text)

    def add_inappropriate_words(self, words: List[str], save_to_custom: bool = False) -> None:
        """
        افزودن کلمات نامناسب جدید به فهرست
        
        Args:
            words: لیست کلمات برای افزودن
            save_to_custom: آیا به فایل سفارشی ذخیره شود
        """
        # افزودن کلمات به فهرست
        self.inappropriate_words.update(words)
        
        # تعریف جایگزین‌ها برای سانسور
        for word in words:
            if word not in self.censored_replacements:
                self.censored_replacements[word] = self.censoring_char * len(word)
        
        # کامپایل مجدد الگوها
        self._compile_patterns()
        
        # ذخیره به فایل سفارشی
        if save_to_custom and self.custom_words_path:
            self._save_to_custom_file()

    def _save_to_custom_file(self) -> None:
        """ذخیره فهرست کلمات نامناسب به فایل سفارشی"""
        if not self.custom_words_path:
            self.logger.warning("Custom words path not specified. Cannot save.")
            return
            
        try:
            # اطمینان از وجود دایرکتوری
            os.makedirs(os.path.dirname(self.custom_words_path), exist_ok=True)
            
            # آماده‌سازی داده
            custom_words_data = {
                "words": list(self.inappropriate_words),
                "replacements": self.censored_replacements
            }
            
            # ذخیره‌سازی
            with open(self.custom_words_path, 'w', encoding='utf-8') as f:
                json.dump(custom_words_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Custom inappropriate words saved to {self.custom_words_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving custom inappropriate words: {e}")

    def get_inappropriate_score(self, text: str) -> float:
        """
        محاسبه امتیاز نامناسب بودن متن (بین 0 تا 1)
        
        Args:
            text: متن ورودی
            
        Returns:
            امتیاز نامناسب بودن
        """
        if not text:
            return 0.0
            
        # شمارش کلمات نامناسب
        inappropriate_words = self.get_inappropriate_words(text)
        if not inappropriate_words:
            return 0.0
            
        # محاسبه امتیاز بر اساس نسبت کلمات نامناسب به کل کلمات
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
            
        return min(1.0, len(inappropriate_words) / total_words)