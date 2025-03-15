# twitter_analyzer/text_processing/noise_removal.py
import re
import emoji
from typing import Dict, Any, Optional, List, Set


class NoiseRemover:
    """
    کلاس حذف نویز از متن توییت‌ها

    این کلاس توابعی برای حذف نویزهای رایج در توییت‌ها را فراهم می‌کند:
    - لینک‌ها
    - منشن‌ها
    - هشتگ‌ها
    - ایموجی‌ها
    - کاراکترهای خاص
    - تب‌ها و فاصله‌های اضافی
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        مقداردهی اولیه کلاس NoiseRemover

        Args:
            config: دیکشنری تنظیمات
        """
        self.config = config or {}
        
        # کامپایل الگوهای رجکس پرکاربرد
        self.url_pattern = re.compile(r'https?://\S+')
        self.mention_pattern = re.compile(r'@\w+')
        self.hashtag_pattern = re.compile(r'#\w+')
        self.emoji_pattern = re.compile(
            r'['
            r'\U0001F1E0-\U0001F1FF'  # پرچم‌های کشورها
            r'\U0001F300-\U0001F5FF'  # نمادها و اشیاء
            r'\U0001F600-\U0001F64F'  # ایموجی‌های صورت
            r'\U0001F680-\U0001F6FF'  # نمادهای متفرقه
            r'\U0001F700-\U0001F77F'  # نمادهای الفبایی
            r'\U0001F780-\U0001F7FF'  # نمادهای هندسی
            r'\U0001F800-\U0001F8FF'  # نمادهای تکمیلی
            r'\U0001F900-\U0001F9FF'  # نمادهای تکمیلی-۲
            r'\U0001FA00-\U0001FA6F'  # نمادهای موضوعی
            r'\U0001FA70-\U0001FAFF'  # نمادهای موضوعی-۲
            r'\U00002702-\U000027B0'  # نمادهای Dingbats
            r'\U000024C2-\U0001F251'  # نمادهای متفرقه
            r']'
        )
        self.special_chars_pattern = re.compile(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\{\}\'\"\-\_]')
        self.extra_spaces_pattern = re.compile(r'\s+')
        self.digits_pattern = re.compile(r'\d+')
        self.multiple_dots_pattern = re.compile(r'\.{2,}')
        self.rtretweet_pattern = re.compile(r'\brt\b', re.IGNORECASE)
        
        # تنظیمات حذف نویز
        self.preserve_emoji_length = self.config.get('preserve_emoji_length', False)
        self.preserve_hashtag_content = self.config.get('preserve_hashtag_content', True)
        self.preserve_digits = self.config.get('preserve_digits', True)

    def remove_all_noise(self, text: str) -> str:
        """
        حذف تمام انواع نویزها از متن

        Args:
            text: متن ورودی

        Returns:
            متن تمیز شده
        """
        if not text:
            return ""
            
        # حذف تمام انواع نویزها
        return self.remove_noise(
            text, 
            remove_links=True,
            remove_mentions=True,
            remove_hashtags=True,
            remove_emojis=True,
            remove_special_chars=True,
            remove_extra_spaces=True,
            remove_digits=not self.preserve_digits,
            remove_rt=True
        )

    def remove_noise(self, text: str, remove_links: bool = True, remove_mentions: bool = True,
                    remove_hashtags: bool = True, remove_emojis: bool = True,
                    remove_special_chars: bool = False, remove_extra_spaces: bool = True,
                    remove_digits: bool = False, remove_rt: bool = True) -> str:
        """
        حذف انواع نویزهای انتخابی از متن

        Args:
            text: متن ورودی
            remove_links: آیا لینک‌ها حذف شوند
            remove_mentions: آیا منشن‌ها حذف شوند
            remove_hashtags: آیا هشتگ‌ها حذف شوند
            remove_emojis: آیا ایموجی‌ها حذف شوند
            remove_special_chars: آیا کاراکترهای خاص حذف شوند
            remove_extra_spaces: آیا فاصله‌های اضافی حذف شوند
            remove_digits: آیا اعداد حذف شوند
            remove_rt: آیا RT و Retweet حذف شوند

        Returns:
            متن تمیز شده
        """
        if not text:
            return ""
        
        clean_text = text
        
        # حذف لینک‌ها
        if remove_links:
            clean_text = self.remove_urls(clean_text)
        
        # حذف RT و Retweet
        if remove_rt:
            clean_text = self.remove_retweets(clean_text)
        
        # حذف منشن‌ها
        if remove_mentions:
            clean_text = self.remove_mentions(clean_text)
        
        # حذف هشتگ‌ها
        if remove_hashtags:
            clean_text = self.remove_hashtags(clean_text, preserve_content=self.preserve_hashtag_content)
        
        # حذف ایموجی‌ها
        if remove_emojis:
            clean_text = self.remove_emojis(clean_text, preserve_length=self.preserve_emoji_length)
        
        # حذف کاراکترهای خاص
        if remove_special_chars:
            clean_text = self.remove_special_chars(clean_text)
        
        # حذف اعداد
        if remove_digits:
            clean_text = self.remove_digits(clean_text)
        
        # حذف نقطه‌های متوالی
        clean_text = self.multiple_dots_pattern.sub(' ... ', clean_text)
        
        # حذف فاصله‌های اضافی
        if remove_extra_spaces:
            clean_text = self.remove_extra_spaces(clean_text)
        
        return clean_text.strip()

    def remove_urls(self, text: str) -> str:
        """
        حذف لینک‌ها از متن

        Args:
            text: متن ورودی

        Returns:
            متن بدون لینک
        """
        return self.url_pattern.sub(' ', text)

    def remove_mentions(self, text: str) -> str:
        """
        حذف منشن‌ها (@username) از متن

        Args:
            text: متن ورودی

        Returns:
            متن بدون منشن
        """
        return self.mention_pattern.sub(' ', text)

    def remove_hashtags(self, text: str, preserve_content: bool = True) -> str:
        """
        حذف هشتگ‌ها از متن

        Args:
            text: متن ورودی
            preserve_content: آیا محتوای هشتگ حفظ شود (فقط علامت # حذف شود)

        Returns:
            متن بدون هشتگ
        """
        if preserve_content:
            # فقط علامت # را حذف می‌کند
            return re.sub(r'#(\w+)', r'\1', text)
        else:
            # کل هشتگ را حذف می‌کند
            return self.hashtag_pattern.sub(' ', text)

    def remove_emojis(self, text: str, preserve_length: bool = False) -> str:
        """
        حذف ایموجی‌ها از متن

        Args:
            text: متن ورودی
            preserve_length: آیا طول متن حفظ شود (ایموجی با فاصله جایگزین شود)

        Returns:
            متن بدون ایموجی
        """
        if preserve_length:
            # جایگزینی هر ایموجی با یک فاصله
            return ''.join(' ' if c in emoji.UNICODE_EMOJI['fa'] else c for c in text)
        else:
            # حذف کامل ایموجی‌ها
            return self.emoji_pattern.sub('', text)

    def remove_special_chars(self, text: str) -> str:
        """
        حذف کاراکترهای خاص (غیر از حروف، اعداد و فاصله)

        Args:
            text: متن ورودی

        Returns:
            متن بدون کاراکترهای خاص
        """
        return self.special_chars_pattern.sub(' ', text)

    def remove_extra_spaces(self, text: str) -> str:
        """
        حذف فاصله‌های اضافی و تب‌ها و تبدیل آنها به یک فاصله

        Args:
            text: متن ورودی

        Returns:
            متن با فاصله‌های نرمال
        """
        # ابتدا مطمئن می‌شویم تمام فاصله‌ها، تب‌ها، و خطوط جدید به فاصله تبدیل شده‌اند
        normalized = text.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
        
        # سپس چندین فاصله متوالی را به یک فاصله تبدیل می‌کنیم
        return self.extra_spaces_pattern.sub(' ', normalized)

    def remove_digits(self, text: str) -> str:
        """
        حذف اعداد از متن

        Args:
            text: متن ورودی

        Returns:
            متن بدون اعداد
        """
        return self.digits_pattern.sub(' ', text)
    
    def remove_retweets(self, text: str) -> str:
        """
        حذف علامت‌های RT و Retweet از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            متن بدون علامت‌های RT
        """
        # حذف RT از ابتدای متن
        clean_text = re.sub(r'^RT\s+', '', text)
        
        # حذف RT در هر جای متن
        clean_text = self.rtretweet_pattern.sub(' ', clean_text)
        
        # حذف واژه retweet
        clean_text = re.sub(r'\bretweet\b', ' ', clean_text, flags=re.IGNORECASE)
        
        return clean_text

    def extract_urls(self, text: str) -> List[str]:
        """
        استخراج لینک‌ها از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            لیست لینک‌های استخراج شده
        """
        if not text:
            return []
            
        return self.url_pattern.findall(text)
    
    def extract_mentions(self, text: str) -> List[str]:
        """
        استخراج منشن‌ها از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            لیست منشن‌های استخراج شده
        """
        if not text:
            return []
            
        return self.mention_pattern.findall(text)
    
    def extract_hashtags(self, text: str) -> List[str]:
        """
        استخراج هشتگ‌ها از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            لیست هشتگ‌های استخراج شده
        """
        if not text:
            return []
            
        return self.hashtag_pattern.findall(text)
    
    def extract_emojis(self, text: str) -> List[str]:
        """
        استخراج ایموجی‌ها از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            لیست ایموجی‌های استخراج شده
        """
        if not text:
            return []
            
        return [c for c in text if c in emoji.UNICODE_EMOJI['fa']]