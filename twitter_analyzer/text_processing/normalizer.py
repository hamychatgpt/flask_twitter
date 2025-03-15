# twitter_analyzer/text_processing/normalizer.py
import re
from typing import Dict, Any, Optional
import hazm


class TextNormalizer:
    """
    کلاس نرمال‌سازی متن فارسی

    این کلاس قابلیت‌های نرمال‌سازی متن فارسی را فراهم می‌کند:
    - یکسان‌سازی کاراکترها
    - تبدیل اعداد به فرمت استاندارد
    - حذف کاراکترهای تکراری
    - استاندارد‌سازی فاصله‌ها
    - اصلاح نیم‌فاصله‌ها
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        مقداردهی اولیه کلاس TextNormalizer

        Args:
            config: دیکشنری تنظیمات
        """
        self.config = config or {}
        
        # ایجاد نرمال‌ساز hazm
        self.hazm_normalizer = hazm.Normalizer()
        
        # تنظیم گزینه‌های نرمال‌سازی
        self.fix_spacing = self.config.get('fix_spacing', True)
        self.fix_arabic_letters = self.config.get('fix_arabic_letters', True)
        self.fix_english_numbers = self.config.get('fix_english_numbers', True)
        self.fix_arabic_numbers = self.config.get('fix_arabic_numbers', True)
        self.remove_diacritics = self.config.get('remove_diacritics', True)
        self.remove_repeats = self.config.get('remove_repeats', True)
        self.max_repeat = self.config.get('max_repeat', 2)
        
        # الگوهای رجکس برای نرمال‌سازی
        self._compile_patterns()

    def _compile_patterns(self):
        """کامپایل الگوهای رجکس برای استفاده مجدد کارآمد"""
        # الگوی کاراکترهای عربی که باید به معادل فارسی تبدیل شوند
        self.arabic_chars_pattern = re.compile(r'[يكﮑﮐﮏﮎﻜﻛﻚﻙ]')
        
        # الگوی اعداد انگلیسی و عربی
        self.english_numbers_pattern = re.compile(r'[0-9]')
        self.arabic_numbers_pattern = re.compile(r'[٠-٩]')
        
        # الگوی اعراب و تشدید
        self.diacritics_pattern = re.compile(r'[\u064B-\u065F\u0670]')
        
        # الگوی کاراکترهای تکراری
        self.repeats_pattern = re.compile(r'(.)\1{2,}')

    def normalize(self, text: str) -> str:
        """
        نرمال‌سازی متن فارسی

        Args:
            text: متن ورودی

        Returns:
            متن نرمال‌شده
        """
        if not text:
            return ""
        
        # استفاده از نرمال‌ساز پایه Hazm
        normalized = self.hazm_normalizer.normalize(text)
        
        # بهبودهای اضافی برای نرمال‌سازی
        
        # تبدیل کاراکترهای عربی به فارسی
        if self.fix_arabic_letters:
            normalized = self._fix_arabic_letters(normalized)
        
        # تبدیل اعداد انگلیسی به فارسی
        if self.fix_english_numbers:
            normalized = self._fix_english_numbers(normalized)
        
        # تبدیل اعداد عربی به فارسی
        if self.fix_arabic_numbers:
            normalized = self._fix_arabic_numbers(normalized)
        
        # حذف اعراب و تشدید
        if self.remove_diacritics:
            normalized = self._remove_diacritics(normalized)
        
        # حذف کاراکترهای تکراری
        if self.remove_repeats:
            normalized = self._remove_repeats(normalized, self.max_repeat)
        
        # اصلاح فاصله‌ها - باید آخرین مرحله باشد
        if self.fix_spacing:
            normalized = self._fix_spacing(normalized)
        
        return normalized

    def _fix_arabic_letters(self, text: str) -> str:
        """تبدیل کاراکترهای عربی به معادل فارسی"""
        # جایگزینی کاراکترهای عربی با معادل فارسی
        replacements = {
            'ي': 'ی',
            'كﮑﮐﮏﮎﻜﻛﻚﻙ': 'ک',
            '١': '۱',
            '٢': '۲',
            '٣': '۳',
            '٤': '۴',
            '٥': '۵',
            '٦': '۶',
            '٧': '۷',
            '٨': '۸',
            '٩': '۹',
            '٠': '۰'
        }
        
        pattern = '|'.join(replacements.keys())
        for arabic, persian in replacements.items():
            text = text.replace(arabic, persian)
        
        return text

    def _fix_english_numbers(self, text: str) -> str:
        """تبدیل اعداد انگلیسی به فارسی"""
        en_to_fa_digits = {
            '0': '۰',
            '1': '۱',
            '2': '۲',
            '3': '۳',
            '4': '۴',
            '5': '۵',
            '6': '۶',
            '7': '۷',
            '8': '۸',
            '9': '۹'
        }
        
        for en_digit, fa_digit in en_to_fa_digits.items():
            text = text.replace(en_digit, fa_digit)
        
        return text

    def _fix_arabic_numbers(self, text: str) -> str:
        """تبدیل اعداد عربی به فارسی"""
        ar_to_fa_digits = {
            '٠': '۰',
            '١': '۱',
            '٢': '۲',
            '٣': '۳',
            '٤': '۴',
            '٥': '۵',
            '٦': '۶',
            '٧': '۷',
            '٨': '۸',
            '٩': '۹'
        }
        
        for ar_digit, fa_digit in ar_to_fa_digits.items():
            text = text.replace(ar_digit, fa_digit)
        
        return text

    def _remove_diacritics(self, text: str) -> str:
        """حذف اعراب و تشدید"""
        return self.diacritics_pattern.sub('', text)

    def _remove_repeats(self, text: str, max_repeat: int = 2) -> str:
        """
        حذف کاراکترهای تکراری

        Args:
            text: متن ورودی
            max_repeat: حداکثر تعداد تکرار مجاز

        Returns:
            متن با کاراکترهای تکراری اصلاح شده
        """
        def _replace_repeat(match):
            char = match.group(1)
            return char * max_repeat
        
        return self.repeats_pattern.sub(_replace_repeat, text)

    def _fix_spacing(self, text: str) -> str:
        """اصلاح فاصله‌ها و نیم‌فاصله‌ها"""
        # اصلاح نیم‌فاصله‌ها برای کلمات مرکب
        # بهبود نیم‌فاصله برای پیشوندها و پسوندهای رایج
        prefixes = ['می', 'نمی']
        for prefix in prefixes:
            text = text.replace(f'{prefix} ', f'{prefix}\u200c')
        
        # تبدیل چندین فاصله به یک فاصله
        text = re.sub(r'\s+', ' ', text)
        
        # اصلاح فاصله قبل از نقطه گذاری‌ها
        punctuations = ['\.', '،', '؛', ':', '؟', '!', '»', ')', ']', '}']
        for punct in punctuations:
            text = re.sub(rf'\s+({punct})', r'\1', text)
        
        # اصلاح فاصله بعد از نقطه گذاری‌ها
        punctuations = ['\.', '،', '؛', ':', '؟', '!', '«', '(', '[', '{']
        for punct in punctuations:
            text = re.sub(rf'({punct})(?!\s)', r'\1 ', text)
        
        # تنظیم نهایی
        text = text.strip()
        
        return text