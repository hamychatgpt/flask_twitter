# twitter_analyzer/text_processing/stopwords.py
from typing import Set, Dict, Optional
import os
import hazm


# کلمات ایست فارسی اضافی برای توییتر
PERSIAN_TWITTER_STOPWORDS = {
    "rt", "فالو", "لایک", "ریتوییت", "فالوبک", "هشتگ", "توییت", "ریپلای", 
    "منشن", "ترند", "پروفایل", "کامنت", "فالور", "فالویینگ", "دی‌ام", "بیو",
    "فالوور", "آیدی", "یوزر", "یوزرنیم", "توییتر", "امروز", "اکنون", "الان",
    "کنید", "کرد", "کردند", "داره", "داشت", "دارد", "هست", "بود", "بودند",
    "شد", "شده", "شدند", "نیست", "باشد", "باشه", "باشید", "شده_است", "رفت",
    "رفتند", "می‌روم", "می‌رود", "می‌روند", "بیا", "بیاید", "آمد", "آمدند",
    "میاد", "میام", "اومد", "اومدم", "اومدن", "میگه", "میگم", "میگن", "گفت",
    "گفتم", "گفتند", "بگو", "بگه", "گف", "گفتش", "میدم", "میده", "میدن", "داد",
    "دادم", "دادند", "بده", "بدید", "میشه", "میشم", "میشن", "شدم", "شدیم", 
    "نمیشه", "خوب", "بد", "خوبه", "بده", "چرا", "چطور", "کجا", "چه", "چی"
}


def get_stopwords(language: str = 'fa', include_twitter: bool = True, 
                  custom_stopwords: Optional[Set[str]] = None) -> Set[str]:
    """
    دریافت کلمات ایست برای زبان مشخص شده با گزینه‌های سفارشی‌سازی
    
    Args:
        language: زبان ('fa' برای فارسی)
        include_twitter: آیا کلمات ایست خاص توییتر اضافه شوند
        custom_stopwords: کلمات ایست سفارشی اضافی
        
    Returns:
        مجموعه کلمات ایست
    """
    stopwords = set()
    
    if language == 'fa':
        # دریافت کلمات ایست فارسی از Hazm
        stopwords.update(hazm.stopwords_list())
        
        # اضافه کردن کلمات ایست ویژه توییتر فارسی
        if include_twitter:
            stopwords.update(PERSIAN_TWITTER_STOPWORDS)
    
    # افزودن کلمات ایست سفارشی
    if custom_stopwords:
        stopwords.update(custom_stopwords)
    
    return stopwords


def load_stopwords_from_file(filepath: str) -> Set[str]:
    """
    خواندن فایل کلمات ایست از مسیر مشخص شده
    
    Args:
        filepath: مسیر فایل کلمات ایست (هر کلمه در یک خط)
        
    Returns:
        مجموعه کلمات ایست
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    stopwords = set()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if word and not word.startswith('#'):  # نادیده گرفتن خطوط خالی و کامنت‌ها
                stopwords.add(word)
    
    return stopwords


def save_stopwords_to_file(stopwords: Set[str], filepath: str) -> None:
    """
    ذخیره کلمات ایست در فایل
    
    Args:
        stopwords: مجموعه کلمات ایست
        filepath: مسیر فایل برای ذخیره‌سازی
    """
    # اطمینان از وجود دایرکتوری
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# Stopwords list\n")
        for word in sorted(stopwords):
            f.write(f"{word}\n")


def add_stopwords(language: str = 'fa', words: Set[str] = None) -> Set[str]:
    """
    افزودن کلمات جدید به کلمات ایست
    
    Args:
        language: زبان ('fa' برای فارسی)
        words: کلمات برای افزودن
        
    Returns:
        مجموعه کلمات ایست به‌روز شده
    """
    stopwords = get_stopwords(language)
    
    if words:
        stopwords.update(words)
    
    return stopwords