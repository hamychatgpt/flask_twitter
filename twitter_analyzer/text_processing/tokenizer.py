# twitter_analyzer/text_processing/tokenizer.py
import re
from typing import List, Dict, Any, Optional
import hazm


class TextTokenizer:
    """
    کلاس توکنیزه کردن متن فارسی

    این کلاس توابع مختلف برای تبدیل متن فارسی به توکن‌ها (کلمات و جملات) را فراهم می‌کند.
    """

    def __init__(self, language: str = 'fa', config: Optional[Dict[str, Any]] = None):
        """
        مقداردهی اولیه کلاس TextTokenizer

        Args:
            language: زبان اصلی ('fa' برای فارسی)
            config: دیکشنری تنظیمات
        """
        self.language = language
        self.config = config or {}
        
        # برای متن فارسی از Hazm استفاده می‌کنیم
        if self.language == 'fa':
            self.word_tokenizer = hazm.word_tokenize
            self.sent_tokenizer = hazm.sent_tokenize
            self.lemmatizer = hazm.Lemmatizer()
            self.stemmer = hazm.Stemmer()
        else:
            # برای زبان‌های دیگر می‌توان کتابخانه‌های مناسب را اضافه کرد
            self.word_tokenizer = lambda text: text.split()
            self.sent_tokenizer = lambda text: re.split(r'[.!?]', text)
            self.lemmatizer = None
            self.stemmer = None
        
        # تنظیمات اضافی
        self.join_multiword_expr = self.config.get('join_multiword_expr', True)
        self.min_word_length = self.config.get('min_word_length', 2)
        
        # جملات و عبارات چند کلمه‌ای فارسی که باید به عنوان یک توکن پردازش شوند
        self.multiword_expressions = [
            'علی رغم', 'با وجود این', 'با این حال', 'به طوری که', 'از آنجایی که', 
            'به دلیل', 'از این رو', 'با توجه به', 'بر اساس', 'بر طبق', 'به منظور',
            'به عنوان', 'به نظر می رسد', 'به همین دلیل', 'علاوه بر این', 'در واقع',
            'در نتیجه', 'اگرچه', 'با این وجود', 'در حالی که', 'به طور کلی',
            'به عبارت دیگر', 'به عبارتی'
        ]
        
        # کامپایل الگوهای رجکس پرکاربرد
        self.multiword_pattern = self._compile_multiword_pattern()

    def _compile_multiword_pattern(self):
        """
        کامپایل الگوی رجکس برای تشخیص عبارات چند کلمه‌ای

        Returns:
            الگوی رجکس کامپایل شده
        """
        # مرتب‌سازی بر اساس طول (طولانی‌ترها اول) برای تطبیق صحیح
        sorted_expressions = sorted(self.multiword_expressions, key=len, reverse=True)
        
        # ساخت الگوی رجکس با escape کردن کاراکترهای خاص
        pattern_str = '|'.join(re.escape(expr) for expr in sorted_expressions)
        
        return re.compile(rf'({pattern_str})')

    def tokenize(self, text: str) -> List[str]:
        """
        متن را به توکن‌ها (کلمات) تبدیل می‌کند

        Args:
            text: متن ورودی

        Returns:
            لیست توکن‌ها (کلمات)
        """
        if not text:
            return []
        
        # پیش‌پردازش متن برای عبارات چند کلمه‌ای
        if self.join_multiword_expr:
            text = self._join_multiword_expressions(text)
        
        # توکنیزه کردن متن
        tokens = self.word_tokenizer(text)
        
        # فیلتر کردن توکن‌های کوتاه
        tokens = [t for t in tokens if len(t) >= self.min_word_length]
        
        return tokens

    def _join_multiword_expressions(self, text: str) -> str:
        """
        عبارات چند کلمه‌ای را به یکدیگر متصل می‌کند

        Args:
            text: متن ورودی

        Returns:
            متن با عبارات چند کلمه‌ای متصل شده
        """
        # جایگزینی فاصله‌ها در عبارات چند کلمه‌ای با زیرخط
        def replace_spaces(match):
            expr = match.group(0)
            return expr.replace(' ', '_')
        
        # اعمال الگو روی متن
        return self.multiword_pattern.sub(replace_spaces, text)

    def tokenize_sentences(self, text: str) -> List[str]:
        """
        متن را به جملات تبدیل می‌کند

        Args:
            text: متن ورودی

        Returns:
            لیست جملات
        """
        if not text:
            return []
            
        return self.sent_tokenizer(text)

    def lemmatize(self, tokens: List[str]) -> List[str]:
        """
        ریشه‌یابی کلمات با استفاده از lemmatizer

        Args:
            tokens: لیست توکن‌ها

        Returns:
            لیست کلمات ریشه‌یابی شده
        """
        if not tokens or not self.lemmatizer:
            return tokens
            
        return [self.lemmatizer.lemmatize(token) for token in tokens]

    def stem(self, tokens: List[str]) -> List[str]:
        """
        ریشه‌یابی کلمات با استفاده از stemmer

        Args:
            tokens: لیست توکن‌ها

        Returns:
            لیست کلمات ریشه‌یابی شده
        """
        if not tokens or not self.stemmer:
            return tokens
            
        return [self.stemmer.stem(token) for token in tokens]

    def get_n_grams(self, tokens: List[str], n: int = 2) -> List[str]:
        """
        ساخت n-grams از توکن‌ها

        Args:
            tokens: لیست توکن‌ها
            n: تعداد توکن‌ها در هر n-gram

        Returns:
            لیست n-grams
        """
        if not tokens or n <= 0 or n > len(tokens):
            return []
            
        return [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]