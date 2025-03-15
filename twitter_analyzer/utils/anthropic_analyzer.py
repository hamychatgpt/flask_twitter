import anthropic
import logging
import json
from typing import Dict, List, Tuple, Optional, Any, Union
from functools import lru_cache
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class AnthropicTextAnalyzer:
    """
    ماژول تحلیل متن و تحلیل احساسات با استفاده از Anthropic API
    این ماژول از استراتژی کاهش هزینه با استفاده از مدل‌های مختلف استفاده می‌کند
    """
    
    def __init__(self, api_key=None, app=None):
        """
        مقداردهی اولیه آنالایزر با کلید API و پارامترهای اختیاری
        
        Args:
            api_key: کلید API آنتروپیک (اختیاری)
            app: نمونه برنامه فلسک (اختیاری)
        """
        # تنظیم کلید API
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required. Set it as an environment variable or pass it to the constructor.")
        
        # ایجاد کلاینت آنتروپیک
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # مدل‌ها برای تحلیل‌های مختلف
        self.screening_model = "claude-3-5-haiku-20241022"  # مدل ارزان برای بررسی اولیه
        self.analysis_model = "claude-3-5-haiku-20241022"  # مدل ارزان برای تحلیل عمیق‌تر
        self.reporting_model = "claude-3-5-sonnet-20241022"  # مدل متوسط برای گزارش‌های نهایی
        
        # تنظیم لاگر
        self.logger = logging.getLogger("anthropic_analyzer")
        
        # ذخیره تاریخچه تحلیل‌ها
        self.analysis_history = []
        
        # کش‌کردن برخی عملیات‌های پرتکرار
        self._cached_prompts = {}
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """اتصال آنالایزر به برنامه Flask"""
        app.extensions['anthropic_analyzer'] = self
        
        # تنظیم config‌های برنامه
        if hasattr(app, 'config'):
            if 'ANTHROPIC_API_KEY' in app.config:
                self.api_key = app.config['ANTHROPIC_API_KEY']
                self.client = anthropic.Anthropic(api_key=self.api_key)
            
            if 'ANTHROPIC_SCREENING_MODEL' in app.config:
                self.screening_model = app.config['ANTHROPIC_SCREENING_MODEL']
            
            if 'ANTHROPIC_ANALYSIS_MODEL' in app.config:
                self.analysis_model = app.config['ANTHROPIC_ANALYSIS_MODEL']
            
            if 'ANTHROPIC_REPORTING_MODEL' in app.config:
                self.reporting_model = app.config['ANTHROPIC_REPORTING_MODEL']
        
        # تنظیم لاگر برنامه
        if app.logger:
            self.logger = app.logger
    
    @lru_cache(maxsize=100)
    def _count_tokens(self, model: str, text: str) -> int:
        """
        تخمین تعداد توکن‌های یک متن
        
        Args:
            model: نام مدل برای تخمین توکن
            text: متن برای شمارش توکن
            
        Returns:
            تعداد تخمینی توکن‌ها
        """
        try:
            count = self.client.messages.count_tokens(
                model=model,
                messages=[{"role": "user", "content": text}]
            )
            return count.input_tokens
        except Exception as e:
            self.logger.error(f"Token counting error: {str(e)}")
            # تخمین ساده: هر 4 کاراکتر تقریباً یک توکن
            return len(text) // 4
    
    def _create_system_prompt(self, analysis_type: str) -> str:
        """
        ایجاد پرامپت سیستمی مناسب برای نوع تحلیل
        
        Args:
            analysis_type: نوع تحلیل (screening, sentiment, spam, inappropriate, full)
            
        Returns:
            پرامپت سیستمی مناسب
        """
        if analysis_type == "screening":
            return """You are a content screening assistant. Your task is ONLY to determine if text needs further analysis.
            Return a JSON with a single "needs_analysis" field set to true if the text:
            1. Contains strong sentiment (very positive or negative)
            2. Contains potentially inappropriate content
            3. Appears to be spam or promotional
            4. Contains sensitive topics
            Otherwise, return {"needs_analysis": false}. ONLY output valid JSON."""
        
        elif analysis_type == "sentiment":
            return """You are a sentiment analysis assistant. Analyze the emotional tone of the given text.
            Return a JSON object with these fields:
            - sentiment: "positive", "negative", or "neutral"
            - confidence: a float from 0 to 1 indicating your confidence
            - intensity: a float from 0 to 1 indicating sentiment strength
            - primary_emotion: the main emotion detected (joy, anger, sadness, etc.)
            - emotional_words: list of emotion-laden words found in the text
            ONLY output valid JSON."""
        
        elif analysis_type == "spam":
            return """You are a spam detection assistant. Determine if the given text is spam.
            Return a JSON object with these fields:
            - is_spam: boolean
            - confidence: a float from 0 to 1 indicating your confidence
            - spam_type: the type of spam if detected (ad, scam, promotional, etc.)
            - spam_indicators: list of patterns or words that indicate spam
            ONLY output valid JSON."""
        
        elif analysis_type == "inappropriate":
            return """You are a content moderation assistant. Check if the text contains inappropriate content.
            Return a JSON object with these fields:
            - is_inappropriate: boolean
            - confidence: a float from 0 to 1 indicating your confidence
            - categories: list of detected content categories (profanity, hate_speech, violence, sexual, etc.)
            - problematic_phrases: list of problematic phrases or terms
            ONLY output valid JSON."""
        
        elif analysis_type == "full":
            return """You are an advanced text analysis assistant. Provide a comprehensive analysis of the text.
            Return a JSON object with these fields:
            - summary: brief 1-2 sentence summary of the content
            - sentiment: object with sentiment analysis results
            - content_flags: object with any content moderation flags
            - spam_score: score from 0 to 1 indicating spam likelihood
            - tone: detected tone (formal, informal, aggressive, friendly, etc.)
            - language: detected language with ISO code
            - key_phrases: list of important phrases
            - topics: list of detected topics
            ONLY output valid JSON."""
        
        else:
            return "You are a text analysis assistant. Provide an analysis of the given text."
    
    async def _call_model_async(self, model: str, system: str, text: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        فراخوانی ناهمزمان مدل کلود
        
        Args:
            model: مدل مورد استفاده
            system: پرامپت سیستمی
            text: متن ورودی
            max_tokens: حداکثر توکن‌های خروجی
            
        Returns:
            پاسخ مدل
        """
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[
                    {"role": "user", "content": text}
                ]
            )
            
            # استخراج پاسخ متنی
            response_text = response.content[0].text if response.content else ""
            
            # تلاش برای پارس JSON
            try:
                if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
                    return json.loads(response_text)
                else:
                    # جستجوی بلوک JSON در پاسخ
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(1))
                    
                    # تلاش دوباره با یافتن اولین { و آخرین }
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        return json.loads(response_text[start_idx:end_idx+1])
            except json.JSONDecodeError:
                pass
            
            # اگر پارس JSON شکست خورد، پاسخ متنی برگردانده می‌شود
            return {"raw_response": response_text}
            
        except Exception as e:
            self.logger.error(f"Model call error: {str(e)}")
            return {"error": str(e)}
    
    def _call_model(self, model: str, system: str, text: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        فراخوانی همزمان مدل کلود
        
        Args:
            model: مدل مورد استفاده
            system: پرامپت سیستمی
            text: متن ورودی
            max_tokens: حداکثر توکن‌های خروجی
            
        Returns:
            پاسخ مدل
        """
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[
                    {"role": "user", "content": text}
                ]
            )
            
            # استخراج پاسخ متنی
            response_text = response.content[0].text if response.content else ""
            
            # تلاش برای پارس JSON
            try:
                if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
                    return json.loads(response_text)
                else:
                    # جستجوی بلوک JSON در پاسخ
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(1))
                    
                    # تلاش دوباره با یافتن اولین { و آخرین }
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        return json.loads(response_text[start_idx:end_idx+1])
            except json.JSONDecodeError:
                pass
            
            # اگر پارس JSON شکست خورد، پاسخ متنی برگردانده می‌شود
            return {"raw_response": response_text}
            
        except Exception as e:
            self.logger.error(f"Model call error: {str(e)}")
            return {"error": str(e)}
    
    def _screen_text(self, text: str) -> bool:
        """
        بررسی اولیه متن برای تشخیص نیاز به تحلیل عمیق‌تر
        از مدل ارزان‌تر استفاده می‌کند
        
        Args:
            text: متن برای بررسی
            
        Returns:
            آیا متن نیاز به تحلیل بیشتر دارد
        """
        system = self._create_system_prompt("screening")
        
        # ساخت نسخه کوتاه از متن اگر متن طولانی باشد
        if len(text) > 500:
            sample = text[:250] + "..." + text[-250:]
        else:
            sample = text
        
        result = self._call_model(
            model=self.screening_model,
            system=system,
            text=sample,
            max_tokens=100  # پاسخ کوتاه کافی است
        )
        
        return result.get("needs_analysis", True)  # در صورت هر گونه خطا، True برمی‌گرداند
    
    def analyze_sentiment(self, text: str, force_full_analysis: bool = False) -> Dict[str, Any]:
        """
        تحلیل احساسات متن
        از استراتژی بهینه‌سازی هزینه استفاده می‌کند
        
        Args:
            text: متن برای تحلیل
            force_full_analysis: اجبار به تحلیل کامل بدون بررسی اولیه
            
        Returns:
            نتایج تحلیل احساسات
        """
        # بررسی اولیه متن با مدل ارزان
        needs_analysis = force_full_analysis or self._screen_text(text)
        
        if not needs_analysis:
            # اگر متن نیاز به تحلیل بیشتر نداشته باشد، یک نتیجه ساده برمی‌گرداند
            return {
                "sentiment": "neutral",
                "confidence": 0.9,
                "intensity": 0.1,
                "primary_emotion": "none",
                "emotional_words": [],
                "screening": "passed",
                "model_used": self.screening_model
            }
        
        # تحلیل کامل احساسات با مدل ارزان‌تر
        system = self._create_system_prompt("sentiment")
        result = self._call_model(
            model=self.analysis_model,
            system=system,
            text=text,
            max_tokens=500
        )
        
        # اضافه کردن اطلاعات اضافی به نتیجه
        result["analysis_timestamp"] = datetime.now().isoformat()
        result["model_used"] = self.analysis_model
        
        # ذخیره در تاریخچه
        self.analysis_history.append({
            "type": "sentiment",
            "text": text[:100] + "..." if len(text) > 100 else text,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    def analyze_spam(self, text: str, force_full_analysis: bool = False) -> Dict[str, Any]:
        """
        تحلیل متن برای تشخیص اسپم
        
        Args:
            text: متن برای تحلیل
            force_full_analysis: اجبار به تحلیل کامل بدون بررسی اولیه
            
        Returns:
            نتایج تحلیل اسپم
        """
        # بررسی اولیه متن با مدل ارزان
        needs_analysis = force_full_analysis or self._screen_text(text)
        
        if not needs_analysis:
            # اگر متن نیاز به تحلیل بیشتر نداشته باشد، یک نتیجه ساده برمی‌گرداند
            return {
                "is_spam": False,
                "confidence": 0.9,
                "spam_type": None,
                "spam_indicators": [],
                "screening": "passed",
                "model_used": self.screening_model
            }
        
        # تحلیل کامل اسپم با مدل ارزان‌تر
        system = self._create_system_prompt("spam")
        result = self._call_model(
            model=self.analysis_model,
            system=system,
            text=text,
            max_tokens=500
        )
        
        # اضافه کردن اطلاعات اضافی به نتیجه
        result["analysis_timestamp"] = datetime.now().isoformat()
        result["model_used"] = self.analysis_model
        
        # ذخیره در تاریخچه
        self.analysis_history.append({
            "type": "spam",
            "text": text[:100] + "..." if len(text) > 100 else text,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    def analyze_inappropriate_content(self, text: str, force_full_analysis: bool = False) -> Dict[str, Any]:
        """
        تحلیل متن برای تشخیص محتوای نامناسب
        
        Args:
            text: متن برای تحلیل
            force_full_analysis: اجبار به تحلیل کامل بدون بررسی اولیه
            
        Returns:
            نتایج تحلیل محتوای نامناسب
        """
        # بررسی اولیه متن با مدل ارزان
        needs_analysis = force_full_analysis or self._screen_text(text)
        
        if not needs_analysis:
            # اگر متن نیاز به تحلیل بیشتر نداشته باشد، یک نتیجه ساده برمی‌گرداند
            return {
                "is_inappropriate": False,
                "confidence": 0.9,
                "categories": [],
                "problematic_phrases": [],
                "screening": "passed",
                "model_used": self.screening_model
            }
        
        # تحلیل کامل محتوای نامناسب با مدل ارزان‌تر
        system = self._create_system_prompt("inappropriate")
        result = self._call_model(
            model=self.analysis_model,
            system=system,
            text=text,
            max_tokens=500
        )
        
        # اضافه کردن اطلاعات اضافی به نتیجه
        result["analysis_timestamp"] = datetime.now().isoformat()
        result["model_used"] = self.analysis_model
        
        # ذخیره در تاریخچه
        self.analysis_history.append({
            "type": "inappropriate",
            "text": text[:100] + "..." if len(text) > 100 else text,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    def analyze_text_full(self, text: str) -> Dict[str, Any]:
        """
        تحلیل کامل متن (احساسات، اسپم، و محتوای نامناسب)
        از اجرای موازی تحلیل‌ها استفاده می‌کند
        
        Args:
            text: متن برای تحلیل
            
        Returns:
            نتایج کامل تحلیل
        """
        # بررسی اولیه متن با مدل ارزان
        needs_analysis = self._screen_text(text)
        
        if not needs_analysis:
            # اگر متن نیاز به تحلیل بیشتر نداشته باشد، یک نتیجه ساده برمی‌گرداند
            return {
                "summary": "متن خنثی بدون علامت خاص",
                "screening": "passed",
                "sentiment": {
                    "sentiment": "neutral",
                    "confidence": 0.9,
                    "intensity": 0.1
                },
                "content_flags": {
                    "is_inappropriate": False,
                    "categories": []
                },
                "spam_score": 0.1,
                "model_used": self.screening_model
            }
        
        # انجام تحلیل‌های موازی برای بهینه‌سازی زمان
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_sentiment = executor.submit(self.analyze_sentiment, text, True)
            future_spam = executor.submit(self.analyze_spam, text, True)
            future_inappropriate = executor.submit(self.analyze_inappropriate_content, text, True)
            
            sentiment_result = future_sentiment.result()
            spam_result = future_spam.result()
            inappropriate_result = future_inappropriate.result()
        
        # ترکیب نتایج
        full_result = {
            "sentiment": sentiment_result,
            "spam": spam_result,
            "inappropriate_content": inappropriate_result,
            "analysis_timestamp": datetime.now().isoformat(),
            "models_used": {
                "sentiment": sentiment_result.get("model_used"),
                "spam": spam_result.get("model_used"),
                "inappropriate": inappropriate_result.get("model_used")
            }
        }
        
        # ذخیره در تاریخچه
        self.analysis_history.append({
            "type": "full",
            "text": text[:100] + "..." if len(text) > 100 else text,
            "result": full_result,
            "timestamp": datetime.now().isoformat()
        })
        
        return full_result
    
    def generate_analysis_report(self, texts: List[str], report_type: str = "text") -> Dict[str, Any]:
        """
        تولید گزارش تحلیلی برای مجموعه‌ای از متن‌ها
        از مدل متوسط یا بهتر استفاده می‌کند
        
        Args:
            texts: لیست متن‌ها برای تحلیل
            report_type: نوع گزارش (text, json، html)
            
        Returns:
            گزارش تحلیلی
        """
        # تحلیل هر متن با استفاده از مدل ارزان‌تر
        analysis_results = []
        for text in texts:
            # از تحلیل سریع استفاده می‌کنیم
            if len(text) < 100:
                # متن‌های کوتاه را مستقیماً تحلیل می‌کنیم
                result = self.analyze_text_full(text)
            else:
                # بررسی اولیه متن
                needs_analysis = self._screen_text(text)
                if not needs_analysis:
                    # اگر نیاز به تحلیل نباشد، نتیجه ساده می‌دهیم
                    result = {
                        "summary": "متن خنثی بدون علامت خاص",
                        "screening": "passed",
                        "sentiment": "neutral",
                        "spam_score": 0.1,
                        "inappropriate": False
                    }
                else:
                    # تحلیل کامل
                    result = self.analyze_text_full(text)
            
            analysis_results.append({
                "text": text[:100] + "..." if len(text) > 100 else text,
                "analysis": result
            })
        
        # اضافه کردن آمار کلی
        stats = self._calculate_aggregate_stats(analysis_results)
        
        # ساخت درخواست برای مدل متوسط یا بهتر
        system_prompt = """You are an expert text analysis reporter. Generate a comprehensive analysis report based on the provided data.
        Your report should include:
        1. An executive summary
        2. Detailed sentiment analysis
        3. Content safety analysis
        4. Spam detection results
        5. Key insights and patterns
        6. Recommended actions based on the analysis
        
        Format the report according to the requested output type."""
        
        request_data = {
            "analysis_results": analysis_results,
            "aggregate_stats": stats,
            "report_type": report_type
        }
        
        # استفاده از مدل متوسط یا بهتر برای تولید گزارش
        report_response = self._call_model(
            model=self.reporting_model,
            system=system_prompt,
            text=json.dumps(request_data),
            max_tokens=4000  # گزارش دقیق و کامل
        )
        
        if "raw_response" in report_response:
            # پردازش گزارش متنی
            report_text = report_response["raw_response"]
            
            if report_type == "json":
                # تلاش برای استخراج JSON از پاسخ
                try:
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', report_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(1))
                    
                    # تلاش برای پارس کل متن به عنوان JSON
                    return json.loads(report_text)
                except:
                    # برگرداندن گزارش به صورت متنی در صورت شکست
                    return {"report": report_text, "format": "text"}
            
            elif report_type == "html":
                # تلاش برای استخراج HTML از پاسخ
                import re
                html_match = re.search(r'```html\s*(.*?)\s*```', report_text, re.DOTALL)
                if html_match:
                    return {"report": html_match.group(1), "format": "html"}
                
                # اگر HTML پیدا نشد، گزارش متنی را برمی‌گرداند
                return {"report": report_text, "format": "text"}
            
            else:
                # گزارش متنی
                return {"report": report_text, "format": "text"}
        else:
            # برگرداندن گزارش به شکل اصلی
            return {"report": report_response, "format": "json"}
    
    def _calculate_aggregate_stats(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        محاسبه آمار تجمعی از نتایج تحلیل
        
        Args:
            analysis_results: لیست نتایج تحلیل
            
        Returns:
            آمار تجمعی
        """
        total_items = len(analysis_results)
        if total_items == 0:
            return {"error": "No analysis results provided"}
        
        # شمارش‌های اولیه
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        spam_count = 0
        inappropriate_count = 0
        
        # برای میانگین‌گیری
        sentiment_score_sum = 0
        spam_score_sum = 0
        
        # جمع‌آوری همه برچسب‌ها و کلمات احساسی
        all_categories = []
        all_emotional_words = []
        
        for item in analysis_results:
            analysis = item.get("analysis", {})
            
            # استخراج احساسات
            sentiment_info = analysis.get("sentiment", {})
            if isinstance(sentiment_info, dict):
                sentiment = sentiment_info.get("sentiment", "neutral")
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                sentiment_score_sum += sentiment_info.get("intensity", 0.5)
                
                # جمع‌آوری کلمات احساسی
                emotional_words = sentiment_info.get("emotional_words", [])
                if isinstance(emotional_words, list):
                    all_emotional_words.extend(emotional_words)
            else:
                # اگر sentiment یک رشته باشد
                sentiment_counts[sentiment_info] = sentiment_counts.get(sentiment_info, 0) + 1
            
            # استخراج اطلاعات اسپم
            spam_info = analysis.get("spam", {})
            if isinstance(spam_info, dict):
                if spam_info.get("is_spam", False):
                    spam_count += 1
                spam_score_sum += spam_info.get("spam_score", spam_info.get("confidence", 0.5))
            
            # استخراج اطلاعات محتوای نامناسب
            inappropriate_info = analysis.get("inappropriate_content", {})
            if isinstance(inappropriate_info, dict):
                if inappropriate_info.get("is_inappropriate", False):
                    inappropriate_count += 1
                
                # جمع‌آوری دسته‌بندی‌ها
                categories = inappropriate_info.get("categories", [])
                if isinstance(categories, list):
                    all_categories.extend(categories)
        
        # محاسبه آمار
        from collections import Counter
        
        # محاسبه فراوانی کلمات احساسی و دسته‌بندی‌ها
        emotional_word_counts = Counter(all_emotional_words).most_common(10)
        category_counts = Counter(all_categories).most_common(10)
        
        return {
            "total_analyzed": total_items,
            "sentiment_distribution": {
                "positive": sentiment_counts.get("positive", 0) / total_items,
                "negative": sentiment_counts.get("negative", 0) / total_items,
                "neutral": sentiment_counts.get("neutral", 0) / total_items
            },
            "sentiment_counts": sentiment_counts,
            "average_sentiment_score": sentiment_score_sum / total_items,
            "spam_percentage": spam_count / total_items,
            "inappropriate_percentage": inappropriate_count / total_items,
            "top_emotional_words": emotional_word_counts,
            "top_content_categories": category_counts
        }
    
    def bulk_analyze(self, texts: List[str], analysis_type: str = "sentiment") -> List[Dict[str, Any]]:
        """
        تحلیل انبوه متن‌ها
        
        Args:
            texts: لیست متن‌ها برای تحلیل
            analysis_type: نوع تحلیل (sentiment, spam, inappropriate, full)
            
        Returns:
            لیست نتایج تحلیل
        """
        results = []
        
        # استفاده از تحلیل موازی برای سرعت بیشتر
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for text in texts:
                if analysis_type == "sentiment":
                    future = executor.submit(self.analyze_sentiment, text)
                elif analysis_type == "spam":
                    future = executor.submit(self.analyze_spam, text)
                elif analysis_type == "inappropriate":
                    future = executor.submit(self.analyze_inappropriate_content, text)
                elif analysis_type == "full":
                    future = executor.submit(self.analyze_text_full, text)
                else:
                    raise ValueError(f"Unknown analysis type: {analysis_type}")
                
                futures.append((text, future))
            
            # جمع‌آوری نتایج
            for text, future in futures:
                try:
                    result = future.result()
                    results.append({
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "result": result
                    })
                except Exception as e:
                    self.logger.error(f"Error analyzing text: {str(e)}")
                    results.append({
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "error": str(e)
                    })
        
        return results
    
    def export_analysis_history(self, format: str = "json", file_path: Optional[str] = None) -> Union[str, Dict[str, Any]]:
        """
        صدور تاریخچه تحلیل‌ها
        
        Args:
            format: فرمت خروجی (json, csv)
            file_path: مسیر فایل برای ذخیره (اختیاری)
            
        Returns:
            داده‌های تاریخچه در فرمت درخواستی
        """
        if not self.analysis_history:
            return {"error": "Analysis history is empty"}
        
        if format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            fieldnames = ["type", "text", "result", "timestamp"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in self.analysis_history:
                # تبدیل result به رشته JSON
                if isinstance(item.get("result"), dict):
                    item["result"] = json.dumps(item["result"])
                writer.writerow(item)
            
            csv_data = output.getvalue()
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    f.write(csv_data)
            
            return csv_data
            
        else:  # json
            json_data = {
                "history": self.analysis_history,
                "stats": {
                    "total_entries": len(self.analysis_history),
                    "types": {}
                }
            }
            
            # محاسبه آمار ساده
            for item in self.analysis_history:
                item_type = item.get("type", "unknown")
                if item_type in json_data["stats"]["types"]:
                    json_data["stats"]["types"][item_type] += 1
                else:
                    json_data["stats"]["types"][item_type] = 1
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            return json_data

# کلاس کمکی برای ادغام با TwitterAnalyzer موجود
class IntegratedTextAnalyzer:
    """
    یک کلاس برای ادغام تحلیلگر متن Anthropic با PersianTextProcessor موجود
    """
    
    def __init__(self, anthropic_analyzer, persian_processor=None, app=None):
        """
        مقداردهی اولیه
        
        Args:
            anthropic_analyzer: نمونه AnthropicTextAnalyzer
            persian_processor: نمونه PersianTextProcessor (اختیاری)
            app: نمونه برنامه flask (اختیاری)
        """
        self.anthropic_analyzer = anthropic_analyzer
        self.persian_processor = persian_processor
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """اتصال به برنامه Flask"""
        # بررسی وجود پردازشگر متن فارسی
        if not self.persian_processor and 'persian_content_analyzer' in app.extensions:
            self.persian_processor = app.extensions['persian_content_analyzer']
        
        app.extensions['integrated_text_analyzer'] = self
    
    def analyze_text(self, text: str, use_local_first: bool = True) -> Dict[str, Any]:
        """
        تحلیل متن با استفاده از پردازشگر محلی و آنتروپیک
        
        Args:
            text: متن برای تحلیل
            use_local_first: ابتدا از پردازشگر محلی استفاده شود
            
        Returns:
            نتایج تحلیل ترکیبی
        """
        results = {
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        
        # اگر پردازشگر محلی موجود باشد و استراتژی local-first باشد
        if self.persian_processor and use_local_first:
            # تحلیل با پردازشگر محلی
            local_results = self.persian_processor.analyze_content(text)
            results["local_analysis"] = local_results
            
            # بررسی اینکه آیا نیاز به تحلیل با آنتروپیک است یا خیر
            needs_advanced_analysis = (
                local_results.get("is_inappropriate", False) or
                local_results.get("is_spam", False) or
                local_results.get("sentiment") in ["positive", "negative"] or
                len(local_results.get("negative_words", [])) > 2 or
                len(local_results.get("positive_words", [])) > 3
            )
            
            if not needs_advanced_analysis:
                # اگر نیاز به تحلیل پیشرفته نباشد، نتایج محلی را بازمی‌گردانیم
                results["source"] = "local_only"
                return results
        
        # تحلیل با آنتروپیک
        anthropic_results = self.anthropic_analyzer.analyze_text_full(text)
        results["anthropic_analysis"] = anthropic_results
        
        # اگر هر دو تحلیل انجام شده، نتایج را ترکیب می‌کنیم
        if "local_analysis" in results:
            results["source"] = "hybrid"
            results["combined_analysis"] = self._combine_analysis_results(
                results["local_analysis"],
                results["anthropic_analysis"]
            )
        else:
            results["source"] = "anthropic_only"
        
        return results
    
    def _combine_analysis_results(self, local_results: Dict[str, Any], anthropic_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        ترکیب نتایج تحلیل محلی و آنتروپیک
        
        Args:
            local_results: نتایج تحلیل محلی
            anthropic_results: نتایج تحلیل آنتروپیک
            
        Returns:
            نتایج ترکیبی
        """
        # استخراج اطلاعات احساسات
        sentiment_local = local_results.get("sentiment", "neutral")
        
        sentiment_anthropic = "neutral"
        if "sentiment" in anthropic_results and isinstance(anthropic_results["sentiment"], dict):
            sentiment_anthropic = anthropic_results["sentiment"].get("sentiment", "neutral")
        
        # دادن اولویت به تحلیل آنتروپیک برای احساسات غیر خنثی
        final_sentiment = sentiment_anthropic if sentiment_anthropic != "neutral" else sentiment_local
        
        # استخراج اطلاعات اسپم
        is_spam_local = local_results.get("is_spam", False)
        
        is_spam_anthropic = False
        if "spam" in anthropic_results and isinstance(anthropic_results["spam"], dict):
            is_spam_anthropic = anthropic_results["spam"].get("is_spam", False)
        
        # اگر هر کدام از منابع اسپم را تشخیص دهند، نتیجه نهایی اسپم است
        final_is_spam = is_spam_local or is_spam_anthropic
        
        # استخراج اطلاعات محتوای نامناسب
        is_inappropriate_local = local_results.get("is_inappropriate", False)
        
        is_inappropriate_anthropic = False
        if "inappropriate_content" in anthropic_results and isinstance(anthropic_results["inappropriate_content"], dict):
            is_inappropriate_anthropic = anthropic_results["inappropriate_content"].get("is_inappropriate", False)
        
        # اگر هر کدام از منابع محتوای نامناسب را تشخیص دهند، نتیجه نهایی نامناسب است
        final_is_inappropriate = is_inappropriate_local or is_inappropriate_anthropic
        
        # ترکیب نتایج
        combined = {
            "sentiment": {
                "value": final_sentiment,
                "local_value": sentiment_local,
                "anthropic_value": sentiment_anthropic,
                "confidence": max(
                    local_results.get("sentiment_confidence", 0.5),
                    anthropic_results.get("sentiment", {}).get("confidence", 0.5)
                    if isinstance(anthropic_results.get("sentiment"), dict) else 0.5
                )
            },
            "spam": {
                "is_spam": final_is_spam,
                "local_detection": is_spam_local,
                "anthropic_detection": is_spam_anthropic,
                "spam_type": anthropic_results.get("spam", {}).get("spam_type", None)
                if isinstance(anthropic_results.get("spam"), dict) else None
            },
            "inappropriate_content": {
                "is_inappropriate": final_is_inappropriate,
                "local_detection": is_inappropriate_local,
                "anthropic_detection": is_inappropriate_anthropic,
                "categories": anthropic_results.get("inappropriate_content", {}).get("categories", [])
                if isinstance(anthropic_results.get("inappropriate_content"), dict) else []
            }
        }
        
        return combined
    
    def analyze_multiple_texts(self, texts: List[str], use_local_first: bool = True) -> Dict[str, Any]:
        """
        تحلیل چندین متن و تولید گزارش ترکیبی
        
        Args:
            texts: لیست متن‌ها برای تحلیل
            use_local_first: ابتدا از پردازشگر محلی استفاده شود
            
        Returns:
            گزارش تحلیلی ترکیبی
        """
        # تحلیل هر متن
        analysis_results = []
        for text in texts:
            analysis_results.append(self.analyze_text(text, use_local_first))
        
        # تولید گزارش با استفاده از آنتروپیک
        report_data = []
        for result in analysis_results:
            if "combined_analysis" in result:
                # استفاده از نتایج ترکیبی
                report_data.append({
                    "text": result["text"],
                    "analysis": result["combined_analysis"]
                })
            elif "anthropic_analysis" in result:
                # استفاده از نتایج آنتروپیک
                report_data.append({
                    "text": result["text"],
                    "analysis": result["anthropic_analysis"]
                })
            else:
                # استفاده از نتایج محلی
                report_data.append({
                    "text": result["text"],
                    "analysis": {
                        "sentiment": {
                            "sentiment": result["local_analysis"].get("sentiment", "neutral"),
                            "intensity": 0.5
                        },
                        "spam": {
                            "is_spam": result["local_analysis"].get("is_spam", False),
                            "spam_type": result["local_analysis"].get("spam_type", None)
                        },
                        "inappropriate_content": {
                            "is_inappropriate": result["local_analysis"].get("is_inappropriate", False),
                            "categories": []
                        }
                    }
                })
        
        # تولید گزارش نهایی با مدل متوسط یا بهتر
        report = self.anthropic_analyzer.generate_analysis_report([r["text"] for r in report_data])
        
        # اضافه کردن نتایج تحلیل به گزارش
        report["analysis_results"] = analysis_results
        
        return report