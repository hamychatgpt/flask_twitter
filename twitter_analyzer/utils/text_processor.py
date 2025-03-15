import re
import string
import json
from functools import lru_cache
from collections import Counter
import os
from datetime import datetime

class PersianTextProcessor:
    """
    پردازشگر پیشرفته متن فارسی با قابلیت فیلترینگ اسپم و محتوای نامناسب
    """
    
    def __init__(self, app=None):
        # کلمات ایست فارسی
        self.stopwords = self._load_stopwords()
        
        # کلمات احساسی
        self.negative_words = self._load_negative_words()
        self.positive_words = self._load_positive_words()
        
        # کلمات و عبارات نامناسب
        self.inappropriate_words = self._load_inappropriate_words()
        
        # الگوهای اسپم
        self.spam_patterns = self._load_spam_patterns()
        
        # علائم نگارشی
        self.punctuations = string.punctuation + '،؛»«؟!' 
        self.punctuations = self.punctuations.replace('#', '').replace('@', '')
        self.punct_translator = str.maketrans('', '', self.punctuations)
        
        # جایگزینی حروف مشابه
        self.char_replacements = {
            'ي': 'ی', 'ك': 'ک', 'ة': 'ه', 
            '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
            '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
            'ـ': '', 'إ': 'ا', 'أ': 'ا', 'آ': 'ا'
        }
        
        # ذخیره تاریخچه پردازش
        self.processing_history = []
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.extensions['persian_content_analyzer'] = self
        
    def _load_stopwords(self):
        """بارگذاری کلمات ایست فارسی"""
        return {
            'و', 'در', 'به', 'از', 'که', 'این', 'را', 'با', 'است', 'برای', 
            'آن', 'یک', 'خود', 'تا', 'کرد', 'بر', 'هم', 'نیز', 'اما', 'شده', 
            'باید', 'می', 'ما', 'هر', 'آنها', 'او', 'شد', 'دارد', 'شود', 'بود',
            'دیگر', 'دو', 'بین', 'بسیار', 'چه', 'همه', 'گفت', 'نمی', 'پس', 'چند',
            'هستند', 'کند', 'وی', 'شما', 'آقای', 'درباره', 'اگر', 'ولی', 'چون', 'بی',
            'من', 'کنند', 'بخش', 'شوند', 'تان', 'همین', 'هایی', 'دارند', 'چرا'
        }
    
    def _load_negative_words(self):
        """بارگذاری کلمات منفی فارسی"""
        return {
            # کلمات منفی احساسی
            'بد', 'ضعیف', 'افتضاح', 'مزخرف', 'زشت', 'وحشتناک', 'ناراضی', 'نامناسب',
            'نارضایتی', 'مشکل', 'اختلال', 'قطعی', 'کند', 'تأخیر', 'گران', 'خراب',
            'داغون', 'نابود', 'کلاهبرداری', 'دزدی', 'غیرقانونی', 'ناعادلانه', 'نابرابر',
            'گرانفروشی', 'تحریم', 'تنبلی', 'فساد', 'دروغ', 'تقلب', 'سانسور', 'فیلتر',
            
            # کلمات منفی مرتبط با ارتباطات
            'قطع', 'اختلال', 'کندی', 'فیلترینگ', 'سرقت', 'هک', 'گرانی',
            'تحریم', 'ضعیف', 'آنتن‌دهی', 'آپلود', 'دانلود', 'پینگ', 'لترنسی',
            'پکت', 'لس', 'تعرفه', 'گرونی', 'نارضایتی', 'شکایت', 'انتقاد',
            
            # احساسات منفی
            'نگران', 'عصبانی', 'خشمگین', 'ناراحت', 'متأسف', 'متاسف', 'ناامید',
            'خسته', 'کلافه', 'عاصی', 'بیزار', 'متنفر', 'خشم', 'نفرت',
            'حسرت', 'اندوه', 'غم', 'درد', 'رنج', 'پشیمان'
        }
    
    def _load_positive_words(self):
        """بارگذاری کلمات مثبت فارسی"""
        return {
            # کلمات مثبت احساسی
            'خوب', 'عالی', 'بهترین', 'لذت', 'رضایت', 'مفید', 'کارآمد', 'سریع',
            'پیشرفت', 'توسعه', 'بهبود', 'کیفیت', 'برتر', 'ممتاز', 'ارزشمند',
            'کاربردی', 'مناسب', 'درست', 'تشکر', 'سپاس', 'قدردانی', 'تحسین',
            
            # کلمات مثبت مرتبط با ارتباطات
            'سرعت', 'پوشش', 'دسترسی', 'امنیت', 'پایداری', 'ارتقا', 'خدمات',
            'پشتیبانی', 'رایگان', 'هدیه', 'تخفیف', 'جایزه', 'همراه', 'ارزان',
            'پهنای‌باند', 'فناوری', 'موفقیت', 'طرح', 'جدید', 'نوآوری',
            
            # احساسات مثبت
            'خوشحال', 'راضی', 'خرسند', 'شاد', 'خشنود', 'امیدوار', 'سپاسگزار',
            'مشتاق', 'علاقه‌مند', 'دوست', 'عشق', 'محبت', 'همدلی', 'اعتماد',
            'اطمینان', 'خوشبین', 'خوشبختی', 'شادی', 'لذت', 'آسایش'
        }
    
    def _load_inappropriate_words(self):
        """بارگذاری کلمات و عبارات نامناسب فارسی"""
        # این لیست را می‌توانید با کلمات مناسب تکمیل کنید
        # برای رعایت اصول اخلاقی تنها چند نمونه کلی آورده شده است
        return {
            # فحش‌های فارسی (از آوردن موارد صریح خودداری شده)
            'فحش۱', 'فحش۲', 'فحش۳',
            
            # کلمات توهین‌آمیز 
            'احمق', 'نادان', 'بی‌شعور', 'بیشعور', 'عوضی', 'آشغال', 'کثافت',
            'بی‌سواد', 'بی‌فرهنگ', 'خفه', 'گمشو', 'دهنت', 
            
            # عبارات نامناسب مرتبط با مقامات
            'بی‌لیاقت', 'بی‌کفایت', 'دزد', 'اختلاس‌گر', 'رانت‌خوار',
            
            # الگوهای حروف جایگزین برای دور زدن فیلتر
            'ا.ح.م.ق', 'ب.ی.ش.ع.و.ر'
        }
    
    def _load_spam_patterns(self):
        """بارگذاری الگوهای اسپم فارسی"""
        return [
            # تبلیغات شبکه‌های اجتماعی و کانال‌ها
            r'(?:عضو شوید|فالو کنید|دنبال کنید|جوین شید|بپیوندید|جوین بدید)\s+(?:کانال|گروه|پیج)\s+(?:تلگرام|اینستاگرام|توییتر|روبیکا)',
            r'(?:کانال|گروه|پیج)\s+(?:تلگرام|اینستاگرام|توییتر|روبیکا)\s+(?:ما|من)\s+[^.]*(?:عضو|فالو|دنبال)',
            r'(?:لینک|آدرس)\s+(?:کانال|گروه|پیج)\s+(?:تلگرام|اینستاگرام|توییتر|روبیکا)',
            r'@\w+\s+(?:کانال|گروه|پیج)\s+(?:تلگرام|اینستاگرام|توییتر|روبیکا)',
            
            # تبلیغات فروش
            r'(?:فروش|خرید)\s+(?:ویژه|فوری|استثنایی|باورنکردنی)',
            r'(?:تخفیف|حراج)\s+(?:ویژه|باورنکردنی|استثنایی|فوق‌العاده)',
            r'(?:ارزان‌ترین|بهترین|مناسب‌ترین)\s+(?:قیمت|فروش)',
            r'(?:قیمت|هزینه)\s+(?:پایین|مناسب|ارزان|باورنکردنی)',
            
            # شماره تماس و آگهی
            r'(?:شماره|تلفن|موبایل)\s*(?:تماس|سفارش)[^.]*[۰-۹0-9]{10,}',
            r'[۰-۹0-9]{2,}[- ][۰-۹0-9]{8,}',
            r'[۰-۹0-9]{11}',
            
            # تبلیغات درآمدزایی
            r'(?:درآمد|پول|ثروت)\s+(?:آسان|راحت|سریع|میلیونی|بدون سرمایه)',
            r'(?:کسب درآمد|درآمدزایی|پولدار شوید)\s+(?:از|با|در)\s+(?:اینترنت|تلگرام|خانه)',
            r'(?:میلیون|میلیارد)\s+(?:تومان|تومن)\s+(?:درآمد|سود)',
            
            # تبلیغات سایت شرط‌بندی
            r'(?:شرط|بندی|پیش‌بینی)\s+(?:فوتبال|ورزشی|آنلاین|زنده)',
            r'(?:بازی|قمار|کازینو|پوکر)\s+(?:آنلاین|زنده)',
            r'(?:برد|سود)\s+(?:تضمینی|۱۰۰٪|صددرصد)',
            
            # تبلیغات محصولات خاص
            r'(?:لاغری|چاقی|رشد قد|رشد مو|زیبایی|جوانسازی|سفیدکننده)\s+(?:سریع|فوری|معجزه‌آسا|شگفت‌انگیز|باورنکردنی)',
            
            # دامنه‌های تبلیغاتی و لینک‌ها
            r'https?://(?:t\.me|bit\.ly|goo\.gl|tinyurl\.com)',
            r'https?://[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\S*'
        ]
    
    def normalize_text(self, text):
        """نرمال‌سازی متن فارسی"""
        if not text:
            return ""
            
        # جایگزینی حروف مشابه
        for old, new in self.char_replacements.items():
            text = text.replace(old, new)
            
        # حذف تشدید و علامت‌های غیرضروری
        text = re.sub(r'ّ|َ|ُ|ِ|ْ|ٌ|ٍ|ً|ء', '', text)
        
        # تبدیل فاصله‌های مجازی به فاصله عادی
        text = text.replace('\u200c', ' ').replace('\u200e', ' ')
        
        # حذف فاصله‌های اضافی
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @lru_cache(maxsize=1000)
    def preprocess(self, text, remove_stopwords=True, remove_urls=True, remove_punctuation=True):
        """
        پیش‌پردازش متن فارسی
        """
        if not text:
            return ""
        
        # نرمال‌سازی متن
        text = self.normalize_text(text)
        
        # حذف URLs
        if remove_urls:
            text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # حذف علائم نگارشی
        if remove_punctuation:
            text = text.translate(self.punct_translator)
        
        # حذف کلمات ایست
        if remove_stopwords:
            words = text.split()
            words = [word for word in words if word not in self.stopwords]
            text = ' '.join(words)
        
        # حذف فاصله‌های اضافی
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_hashtags(self, text):
        """استخراج هشتگ‌ها"""
        return re.findall(r'#([\w\u0600-\u06FF]+)', text)
    
    def extract_mentions(self, text):
        """استخراج منشن‌ها"""
        return re.findall(r'@([\w\u0600-\u06FF]+)', text)
    
    def detect_language(self, text):
        """تشخیص زبان متن (فارسی یا انگلیسی)"""
        persian_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if persian_chars > english_chars:
            return 'fa'
        elif english_chars > persian_chars:
            return 'en'
        else:
            return 'mixed'
    
    def analyze_sentiment(self, text):
        """
        تحلیل احساسات ساده متن فارسی
        
        Returns:
            tuple: (احساس، امتیاز، کلمات منفی یافت شده، کلمات مثبت یافت شده)
        """
        normalized_text = self.normalize_text(text.lower())
        words = re.findall(r'[\w\u0600-\u06FF]+', normalized_text)
        
        # شمارش کلمات مثبت و منفی
        negative_count = 0
        positive_count = 0
        
        found_negative_words = []
        found_positive_words = []
        
        for word in words:
            if word in self.negative_words:
                negative_count += 1
                found_negative_words.append(word)
            elif word in self.positive_words:
                positive_count += 1
                found_positive_words.append(word)
        
        # محاسبه امتیاز نهایی (-1 تا 1)
        total_words = len(words)
        if total_words == 0:
            return 'neutral', 0, [], []
        
        score = (positive_count - negative_count) / (positive_count + negative_count + 1)
        
        # تعیین احساس کلی
        if score > 0.1:
            sentiment = 'positive'
        elif score < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return sentiment, score, found_negative_words, found_positive_words
    
    def detect_inappropriate_content(self, text):
        """
        تشخیص محتوای نامناسب (توهین، فحش و ...)
        
        Returns:
            tuple: (آیا نامناسب است، کلمات نامناسب یافت شده)
        """
        normalized_text = self.normalize_text(text.lower())
        words = re.findall(r'[\w\u0600-\u06FF]+', normalized_text)
        
        found_inappropriate = []
        
        for word in words:
            if word in self.inappropriate_words:
                found_inappropriate.append(word)
        
        # بررسی الگوهای مخفی‌سازی فحش
        # برخی کاربران با گذاشتن نقطه یا فاصله بین حروف سعی می‌کنند فیلترها را دور بزنند
        suspicious_patterns = [
            r'\w\.\w\.\w\.\w',  # مثال: ف.ح.ش
            r'\w\s+\w\s+\w\s+\w'  # مثال: ف ح ش
        ]
        
        for pattern in suspicious_patterns:
            matches = re.findall(pattern, normalized_text)
            if matches:
                found_inappropriate.extend(matches)
        
        return len(found_inappropriate) > 0, found_inappropriate
    
    def is_spam(self, text):
        """
        تشخیص اسپم در متن فارسی
        
        Returns:
            tuple: (آیا اسپم است، نوع اسپم)
        """
        normalized_text = self.normalize_text(text.lower())
        
        # الگوهای اسپم
        spam_categories = {
            'تبلیغات کانال': [0, 1, 2, 3],
            'تبلیغات فروش': [4, 5, 6, 7],
            'تبلیغات با شماره تماس': [8, 9, 10],
            'وعده درآمدزایی': [11, 12, 13],
            'سایت شرط‌بندی': [14, 15, 16],
            'تبلیغات محصولات خاص': [17],
            'لینک مشکوک': [18, 19]
        }
        
        for category, pattern_indices in spam_categories.items():
            for idx in pattern_indices:
                if re.search(self.spam_patterns[idx], normalized_text):
                    return True, category
        
        # بررسی تعداد لینک‌ها و منشن‌ها
        url_count = len(re.findall(r'https?://\S+|www\.\S+', text))
        mention_count = len(re.findall(r'@\w+', text))
        
        # اگر تعداد لینک‌ها یا منشن‌ها زیاد باشد احتمالاً اسپم است
        if url_count > 2 or mention_count > 5:
            return True, 'تعداد زیاد لینک یا منشن'
        
        return False, None
    
    def analyze_content(self, text):
        """
        تحلیل کامل محتوای متن فارسی
        
        Returns:
            dict: نتایج تحلیل
        """
        # پردازش اولیه متن
        normalized_text = self.normalize_text(text)
        preprocessed_text = self.preprocess(text)
        
        # آنالیز زبان
        language = self.detect_language(text)
        
        # استخراج هشتگ‌ها و منشن‌ها
        hashtags = self.extract_hashtags(text)
        mentions = self.extract_mentions(text)
        
        # تحلیل احساسات
        sentiment, sentiment_score, negative_words, positive_words = self.analyze_sentiment(text)
        
        # بررسی محتوای نامناسب
        is_inappropriate, inappropriate_words = self.detect_inappropriate_content(text)
        
        # تشخیص اسپم
        is_spam, spam_type = self.is_spam(text)
        
        # ثبت در تاریخچه پردازش
        analysis_result = {
            'original_text': text,
            'normalized_text': normalized_text,
            'preprocessed_text': preprocessed_text,
            'language': language,
            'hashtags': hashtags,
            'mentions': mentions,
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'negative_words': negative_words,
            'positive_words': positive_words,
            'is_inappropriate': is_inappropriate,
            'inappropriate_words': inappropriate_words,
            'is_spam': is_spam,
            'spam_type': spam_type,
            'timestamp': datetime.now().isoformat()
        }
        
        self.processing_history.append(analysis_result)
        
        return analysis_result
    
    def generate_report(self, save_to_file=False):
        """
        گزارش‌گیری از تاریخچه پردازش
        
        Returns:
            dict: گزارش آماری
        """
        if not self.processing_history:
            return {"error": "تاریخچه پردازش خالی است"}
        
        total_processed = len(self.processing_history)
        spam_count = sum(1 for item in self.processing_history if item['is_spam'])
        inappropriate_count = sum(1 for item in self.processing_history if item['is_inappropriate'])
        
        # آمار احساسات
        sentiment_stats = {
            'positive': sum(1 for item in self.processing_history if item['sentiment'] == 'positive'),
            'negative': sum(1 for item in self.processing_history if item['sentiment'] == 'negative'),
            'neutral': sum(1 for item in self.processing_history if item['sentiment'] == 'neutral')
        }
        
        # آمار زبان
        language_stats = {
            'fa': sum(1 for item in self.processing_history if item['language'] == 'fa'),
            'en': sum(1 for item in self.processing_history if item['language'] == 'en'),
            'mixed': sum(1 for item in self.processing_history if item['language'] == 'mixed')
        }
        
        # آمار انواع اسپم
        spam_types = {}
        for item in self.processing_history:
            if item['is_spam'] and item['spam_type']:
                spam_types[item['spam_type']] = spam_types.get(item['spam_type'], 0) + 1
        
        # کلمات منفی و مثبت پرتکرار
        all_negative_words = []
        all_positive_words = []
        for item in self.processing_history:
            all_negative_words.extend(item['negative_words'])
            all_positive_words.extend(item['positive_words'])
        
        top_negative_words = Counter(all_negative_words).most_common(10)
        top_positive_words = Counter(all_positive_words).most_common(10)
        
        # هشتگ‌های پرتکرار
        all_hashtags = []
        for item in self.processing_history:
            all_hashtags.extend(item['hashtags'])
        
        top_hashtags = Counter(all_hashtags).most_common(10)
        
        report = {
            'total_processed': total_processed,
            'spam_count': spam_count,
            'spam_percentage': (spam_count / total_processed) * 100 if total_processed > 0 else 0,
            'inappropriate_count': inappropriate_count,
            'inappropriate_percentage': (inappropriate_count / total_processed) * 100 if total_processed > 0 else 0,
            'sentiment_stats': sentiment_stats,
            'language_stats': language_stats,
            'spam_types': spam_types,
            'top_negative_words': top_negative_words,
            'top_positive_words': top_positive_words,
            'top_hashtags': top_hashtags,
            'generated_at': datetime.now().isoformat()
        }
        
        
        
        if save_to_file:
            filename = f"content_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report