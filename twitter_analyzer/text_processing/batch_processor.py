# twitter_analyzer/text_processing/batch_processor.py
import logging
from typing import List, Dict, Any, Optional, Callable, Tuple, Union
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import pandas as pd
from . import processor

class BatchProcessor:
    """
    کلاس پردازش دسته‌ای توییت‌ها

    این کلاس امکان پردازش دسته‌ای بزرگی از توییت‌ها را با کارایی بالا فراهم می‌کند.
    امکان استفاده از پردازش موازی با Thread و Process را دارد.
    """

    def __init__(self, text_processor=None, config: Optional[Dict[str, Any]] = None):
        """
        مقداردهی اولیه کلاس BatchProcessor

        Args:
            text_processor: نمونه کلاس TextProcessor (اختیاری)
            config: دیکشنری تنظیمات
        """
        self.logger = logging.getLogger("batch_processor")
        self.config = config or {}
        
        # مقداردهی اولیه پردازشگر متن
        self.text_processor = text_processor or processor.TextProcessor()
        
        # تنظیمات پردازش موازی
        self.parallel_type = self.config.get('parallel_type', 'thread')  # 'thread' یا 'process'
        self.max_workers = self.config.get('max_workers', 4)
        self.batch_size = self.config.get('batch_size', 1000)
        self.progress_callback = None
        
        # آمار پردازش
        self.stats = {
            'total_items': 0,
            'processed_items': 0,
            'error_count': 0,
            'processing_time': 0
        }

    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """
        تنظیم تابع callback برای گزارش پیشرفت
        
        Args:
            callback: تابع callback که دو پارامتر (تعداد پردازش شده، کل) دریافت می‌کند
        """
        self.progress_callback = callback

    def _update_progress(self, processed_count: int, total_count: int):
        """
        به‌روزرسانی پیشرفت پردازش
        
        Args:
            processed_count: تعداد آیتم‌های پردازش شده
            total_count: تعداد کل آیتم‌ها
        """
        # به‌روزرسانی آمار
        self.stats['processed_items'] = processed_count
        self.stats['total_items'] = total_count
        
        # فراخوانی callback
        if self.progress_callback:
            self.progress_callback(processed_count, total_count)

    def process_texts(self, texts: List[str], **processor_kwargs) -> List[Dict[str, Any]]:
        """
        پردازش لیستی از متن‌ها
        
        Args:
            texts: لیست متن‌ها برای پردازش
            **processor_kwargs: پارامترهای اضافی برای تابع پردازش
            
        Returns:
            لیست نتایج پردازش
        """
        if not texts:
            return []
            
        start_time = time.time()
        
        # تنظیم آمار
        self.stats['total_items'] = len(texts)
        self.stats['processed_items'] = 0
        self.stats['error_count'] = 0
        
        results = []
        
        # انتخاب روش پردازش موازی
        if self.parallel_type == 'process' and len(texts) > 100:
            # استفاده از ProcessPoolExecutor برای حجم بالای داده
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                results = self._process_with_executor(executor, texts, **processor_kwargs)
        else:
            # استفاده از ThreadPoolExecutor (پیش‌فرض)
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = self._process_with_executor(executor, texts, **processor_kwargs)
        
        # ثبت زمان پردازش
        self.stats['processing_time'] = time.time() - start_time
        
        return results

    def _process_with_executor(self, executor, texts: List[str], **processor_kwargs) -> List[Dict[str, Any]]:
        """
        پردازش متون با استفاده از executor
        
        Args:
            executor: نمونه ThreadPoolExecutor یا ProcessPoolExecutor
            texts: لیست متن‌ها
            **processor_kwargs: پارامترهای اضافی برای تابع پردازش
            
        Returns:
            لیست نتایج پردازش
        """
        results = []
        futures = {}
        
        # تقسیم به batch‌های کوچکتر برای مدیریت بهتر حافظه و گزارش پیشرفت
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i+self.batch_size]
            future = executor.submit(self._process_batch, batch, **processor_kwargs)
            futures[future] = i
        
        # جمع‌آوری نتایج
        processed_count = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_results = future.result()
                results.extend(batch_results)
                
                # به‌روزرسانی پیشرفت
                processed_count += len(batch_results)
                self._update_progress(processed_count, len(texts))
                
            except Exception as e:
                self.logger.error(f"Error processing batch: {str(e)}")
                self.stats['error_count'] += 1
        
        # مرتب‌سازی نتایج بر اساس ترتیب اصلی
        if 'original_index' in results[0]:
            results.sort(key=lambda x: x['original_index'])
            # حذف شاخص اصلی
            for result in results:
                if 'original_index' in result:
                    del result['original_index']
        
        return results

    def _process_batch(self, batch: List[str], **processor_kwargs) -> List[Dict[str, Any]]:
        """
        پردازش یک batch از متن‌ها
        
        Args:
            batch: لیست متن‌ها
            **processor_kwargs: پارامترهای اضافی برای تابع پردازش
            
        Returns:
            لیست نتایج پردازش
        """
        # ایجاد نمونه TextProcessor در صورت نیاز (برای ProcessPoolExecutor)
        text_proc = self.text_processor
        if self.parallel_type == 'process':
            text_proc = processor.TextProcessor()
        
        results = []
        for i, text in enumerate(batch):
            try:
                # پردازش متن با TextProcessor
                result = text_proc._process_single_text(text, **processor_kwargs)
                
                # افزودن شاخص اصلی برای حفظ ترتیب
                result['original_index'] = i
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error processing text {i}: {str(e)}")
                results.append({
                    'original_index': i,
                    'original': text,
                    'error': str(e)
                })
        
        return results

    def process_dataframe(self, df: pd.DataFrame, text_column: str, 
                         **processor_kwargs) -> pd.DataFrame:
        """
        پردازش ستون متن در DataFrame
        
        Args:
            df: داده‌های پاندا DataFrame
            text_column: نام ستون متن
            **processor_kwargs: پارامترهای اضافی برای تابع پردازش
            
        Returns:
            DataFrame با اضافه شدن نتایج پردازش
        """
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in DataFrame")
        
        # استخراج متون
        texts = df[text_column].tolist()
        
        # پردازش متون
        results = self.process_texts(texts, **processor_kwargs)
        
        # ایجاد DataFrame نتایج
        results_df = pd.DataFrame(results)
        
        # حذف ستون 'original' برای جلوگیری از تکرار
        if 'original' in results_df.columns:
            results_df = results_df.drop('original', axis=1)
        
        # ترکیب با DataFrame اصلی
        return pd.concat([df, results_df], axis=1)

    def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار پردازش
        
        Returns:
            دیکشنری آمار پردازش
        """
        # محاسبه آمار اضافی
        stats = self.stats.copy()
        
        if stats['total_items'] > 0:
            stats['completion_percentage'] = (stats['processed_items'] / stats['total_items']) * 100
        else:
            stats['completion_percentage'] = 0
            
        if stats['processing_time'] > 0 and stats['processed_items'] > 0:
            stats['items_per_second'] = stats['processed_items'] / stats['processing_time']
        else:
            stats['items_per_second'] = 0
            
        return stats

    def process_tweets(self, tweets: List[Dict[str, Any]], text_key: str = 'text',
                      add_results_to_tweets: bool = True, **processor_kwargs) -> List[Dict[str, Any]]:
        """
        پردازش متن توییت‌ها
        
        Args:
            tweets: لیست توییت‌ها (هر توییت یک دیکشنری)
            text_key: کلید متن در دیکشنری توییت
            add_results_to_tweets: آیا نتایج به توییت‌های اصلی اضافه شوند
            **processor_kwargs: پارامترهای اضافی برای تابع پردازش
            
        Returns:
            لیست توییت‌ها با اضافه شدن نتایج پردازش
        """
        if not tweets:
            return []
            
        # استخراج متون
        texts = [tweet.get(text_key, '') for tweet in tweets]
        
        # پردازش متون
        results = self.process_texts(texts, **processor_kwargs)
        
        if add_results_to_tweets:
            # اضافه کردن نتایج به توییت‌های اصلی
            processed_tweets = []
            for i, tweet in enumerate(tweets):
                # کپی توییت اصلی
                processed_tweet = tweet.copy()
                
                if i < len(results):
                    # حذف 'original' برای جلوگیری از تکرار
                    result_copy = results[i].copy()
                    if 'original' in result_copy:
                        del result_copy['original']
                    
                    # اضافه کردن نتایج پردازش
                    processed_tweet['processed_text'] = result_copy
                
                processed_tweets.append(processed_tweet)
            
            return processed_tweets
        else:
            # بازگرداندن نتایج به طور مستقیم
            return results