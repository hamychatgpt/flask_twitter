"""
بررسی مشکل الگوی emoji_pattern
"""
import re

def check_emoji_pattern():
    print("=== بررسی الگوی emoji_pattern ===")
    
    # تست الگوهای مختلف برای ایموجی
    patterns = [
        ("Basic", r'[\U0001F600-\U0001F64F]'),
        ("Simple union", r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]'),
        ("Pipe-separated", r'[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]'),
        ("Join method", '|'.join([
            r'[\U0001F600-\U0001F64F]',
            r'[\U0001F300-\U0001F5FF]'
        ]))
    ]
    
    for name, pattern in patterns:
        try:
            compiled = re.compile(pattern)
            print(f"✅ الگوی '{name}' معتبر است")
            
            # تست عملکرد
            test_text = "این یک متن با ایموجی 😊 است"
            result = re.sub(compiled, '', test_text)
            print(f"   نتیجه: '{result}'")
        except Exception as e:
            print(f"❌ الگوی '{name}' نامعتبر است: {str(e)}")
    
    # بررسی کد emoji_pattern در NoiseRemover
    print("\n=== بررسی کد NoiseRemover ===")
    try:
        from twitter_analyzer.text_processing.noise_removal import NoiseRemover
        remover = NoiseRemover()
        
        # نمایش pattern
        print(f"pattern موجود: {remover.emoji_pattern.pattern[:50]}...")
        
        # تست عملکرد remove_emojis
        test_text = "این یک متن با ایموجی 😊 است"
        result = remover.remove_emojis(test_text)
        print(f"نتیجه remove_emojis: '{result}'")
    except Exception as e:
        print(f"❌ خطا در NoiseRemover: {str(e)}")
        
    # پیشنهاد اصلاح
    print("\n=== پیشنهاد اصلاح ===")
    print("""
برای اصلاح خطا، کد زیر را در کلاس NoiseRemover جایگزین کنید:

self.emoji_pattern = re.compile('|'.join([
    r'[\U0001F600-\U0001F64F]',  # ایموجی‌های صورت
    r'[\U0001F300-\U0001F5FF]',  # نمادها و اشیاء
    r'[\U0001F680-\U0001F6FF]'   # نمادهای متفرقه
]))

و متد remove_emojis را به این صورت اصلاح کنید:

def remove_emojis(self, text: str, preserve_length: bool = False) -> str:
    if not text:
        return ""
        
    if preserve_length:
        return re.sub(self.emoji_pattern, ' ', text)
    else:
        return re.sub(self.emoji_pattern, '', text)
""")

if __name__ == "__main__":
    check_emoji_pattern()