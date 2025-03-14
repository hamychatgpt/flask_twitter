/**
 * این فایل شامل توابع لازم برای کار با کامپوننت‌های هوش مصنوعی است
 * در این نسخه نمونه، از داده‌های شبیه‌سازی شده استفاده می‌کنیم
 * در محیط واقعی، این توابع با API های بک‌اند شما ارتباط برقرار می‌کنند
 */

// -------- تنظیمات اولیه --------
document.addEventListener('DOMContentLoaded', function() {
    // مقداردهی اولیه باکس تحلیل هوشمند
    if (document.getElementById('aiAnalysisContent')) {
        fetchAiAnalysis();
    }
    
    // رویداد دکمه به‌روزرسانی
    const refreshButton = document.getElementById('refreshAiAnalysis');
    if (refreshButton) {
        refreshButton.addEventListener('click', fetchAiAnalysis);
    }
    
    // رویدادهای باکس چت
    const chatForm = document.getElementById('aiChatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', handleChatSubmit);
    }
    
    // رویداد دکمه پاک کردن چت
    const clearChatButton = document.getElementById('clearAiChat');
    if (clearChatButton) {
        clearChatButton.addEventListener('click', clearChat);
    }
});

// -------- توابع تحلیل هوشمند --------

/**
 * دریافت تحلیل هوشمند از API
 * در نسخه واقعی، این تابع با API بک‌اند شما ارتباط برقرار می‌کند
 */
function fetchAiAnalysis() {
    // نمایش وضعیت بارگذاری
    const loadingElement = document.getElementById('aiAnalysisLoading');
    const resultElement = document.getElementById('aiAnalysisResult');
    
    if (loadingElement && resultElement) {
        loadingElement.style.display = 'flex';
        resultElement.style.display = 'none';
        
        // شبیه‌سازی تأخیر شبکه (در نسخه واقعی این بخش با fetch جایگزین می‌شود)
        setTimeout(() => {
            // دریافت تحلیل از API (در اینجا از داده نمونه استفاده می‌کنیم)
            const analysis = getMockAiAnalysis();
            
            // نمایش نتیجه
            resultElement.innerHTML = analysis;
            loadingElement.style.display = 'none';
            resultElement.style.display = 'block';
            
            // به‌روزرسانی زمان
            updateAiAnalysisTimestamp();
        }, 1500);
    }
}

/**
 * به‌روزرسانی زمان آخرین دریافت تحلیل
 */
function updateAiAnalysisTimestamp() {
    const timestampElement = document.getElementById('aiAnalysisTimestamp');
    if (timestampElement) {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const formattedTime = `${hours}:${minutes}`;
        timestampElement.textContent = formattedTime;
    }
}

/**
 * تولید داده نمونه برای تحلیل هوشمند
 * در نسخه واقعی، این تابع حذف می‌شود و داده از API دریافت می‌شود
 */
function getMockAiAnalysis() {
    const analyses = [
        `<p>در 24 ساعت گذشته، شاهد افزایش <strong>32 درصدی</strong> در فعالیت کاربران حول هشتگ <strong>#پایتون</strong> بوده‌ایم. این افزایش با انتشار نسخه جدید فریمورک فلسک همزمان شده است.</p>
        <p>روند احساسات در توییت‌های مرتبط با برنامه‌نویسی وب مثبت است (68٪ مثبت، 22٪ خنثی، 10٪ منفی) که نشان‌دهنده استقبال از فناوری‌های جدید است.</p>
        <ul>
            <li>محبوب‌ترین موضوعات: یادگیری ماشین، توسعه وب، امنیت داده</li>
            <li>بیشترین تعامل: توییت‌های آموزشی و راهنماها</li>
            <li>زمان اوج فعالیت: ساعات 18 تا 22</li>
        </ul>`,
        
        `<p>تحلیل داده‌های هفته اخیر نشان می‌دهد موضوع <strong>هوش مصنوعی</strong> با رشد <strong>45 درصدی</strong> در صدر گفتگوهای کاربران قرار گرفته است.</p>
        <p>ترکیب احساسات در مورد این موضوع متعادل است (52٪ مثبت، 35٪ خنثی، 13٪ منفی) که نشان‌دهنده وجود دیدگاه‌های متنوع است.</p>
        <ul>
            <li>کلیدواژه‌های پرتکرار: GPT، یادگیری عمیق، اخلاق هوش مصنوعی</li>
            <li>افراد تأثیرگذار: محققان دانشگاهی و متخصصان صنعت</li>
            <li>پیش‌بینی: ادامه روند صعودی این موضوع در 2 هفته آینده</li>
        </ul>`,
        
        `<p>در سه روز گذشته، توییت‌های مرتبط با <strong>امنیت سایبری</strong> افزایش <strong>28 درصدی</strong> داشته‌اند که با گزارش چند آسیب‌پذیری مهم همزمان شده است.</p>
        <p>احساسات غالب در این موضوع نگرانی است (23٪ مثبت، 42٪ خنثی، 35٪ منفی) که نشان‌دهنده دغدغه کاربران درباره حفاظت از داده‌هاست.</p>
        <ul>
            <li>موضوعات مرتبط: رمزنگاری، حریم خصوصی، باگ‌های امنیتی</li>
            <li>منابع پرارجاع: مقالات تخصصی و اخبار فناوری</li>
            <li>توصیه: پوشش بیشتر مباحث آموزشی امنیت برای جذب مخاطب</li>
        </ul>`
    ];
    
    // انتخاب تصادفی یکی از تحلیل‌ها
    return analyses[Math.floor(Math.random() * analyses.length)];
}

// -------- توابع چت هوشمند --------

/**
 * مدیریت ارسال پیام در چت
 */
function handleChatSubmit(e) {
    e.preventDefault();
    
    const inputElement = document.getElementById('aiChatPrompt');
    const chatMessages = document.getElementById('aiChatMessages');
    
    if (inputElement && chatMessages && inputElement.value.trim() !== '') {
        const userMessage = inputElement.value.trim();
        
        // افزودن پیام کاربر به چت
        appendUserMessage(chatMessages, userMessage);
        
        // پاک کردن فیلد ورودی
        inputElement.value = '';
        
        // شبیه‌سازی دریافت پاسخ از API (در نسخه واقعی با fetch جایگزین می‌شود)
        setTimeout(() => {
            const aiResponse = getMockAiResponse(userMessage);
            appendAiMessage(chatMessages, aiResponse);
            
            // اسکرول به پایین چت
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 1000);
        
        // اسکرول به پایین چت
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

/**
 * افزودن پیام کاربر به چت
 */
function appendUserMessage(chatContainer, message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'user-message';
    messageElement.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="user-avatar"></div>
    `;
    chatContainer.appendChild(messageElement);
}

/**
 * افزودن پیام هوش مصنوعی به چت
 */
function appendAiMessage(chatContainer, message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'ai-message';
    messageElement.innerHTML = `
        <div class="ai-avatar"></div>
        <div class="message-content">${message}</div>
    `;
    chatContainer.appendChild(messageElement);
}

/**
 * پاک کردن تاریخچه چت
 */
function clearChat() {
    const chatMessages = document.getElementById('aiChatMessages');
    if (chatMessages) {
        // حذف همه پیام‌ها به جز پیام خوشامدگویی اولیه
        chatMessages.innerHTML = `
            <div class="ai-message">
                <div class="ai-avatar"></div>
                <div class="message-content">
                    سلام! من هوشیار هستم. درباره روندهای توییتر از من بپرسید.
                </div>
            </div>
        `;
    }
}

/**
 * تولید پاسخ نمونه برای چت
 * در نسخه واقعی، این تابع حذف می‌شود و پاسخ از API دریافت می‌شود
 */
function getMockAiResponse(userMessage) {
    // کلمات کلیدی برای تشخیص نوع سوال
    const keywords = {
        trend: ['روند', 'ترند', 'داغ', 'محبوب', 'پرطرفدار'],
        sentiment: ['احساس', 'نظر', 'دیدگاه', 'واکنش', 'بازخورد'],
        hashtag: ['هشتگ', 'تگ', '#'],
        users: ['کاربر', 'فالوور', 'دنبال‌کننده', 'مخاطب'],
        time: ['زمان', 'ساعت', 'روز', 'هفته', 'ماه']
    };
    
    // پاسخ‌های پیش‌فرض بر اساس کلمات کلیدی
    let response = '';
    
    // بررسی کلمات کلیدی در سوال کاربر
    if (keywords.trend.some(keyword => userMessage.includes(keyword))) {
        response = 'در 24 ساعت گذشته، موضوعات هوش مصنوعی، برنامه‌نویسی وب و امنیت داده بیشترین روند رشد را داشته‌اند.';
    } else if (keywords.sentiment.some(keyword => userMessage.includes(keyword))) {
        response = 'تحلیل احساسات نشان می‌دهد در موضوعات فناوری، 65% توییت‌ها مثبت، 25% خنثی و 10% منفی هستند.';
    } else if (keywords.hashtag.some(keyword => userMessage.includes(keyword))) {
        response = 'محبوب‌ترین هشتگ‌های هفته اخیر: #پایتون، #هوش_مصنوعی، #برنامه_نویسی، #داده_کاوی و #امنیت_سایبری بوده‌اند.';
    } else if (keywords.users.some(keyword => userMessage.includes(keyword))) {
        response = 'کاربران فعال در حوزه فناوری عمدتاً در ساعات عصر و شب فعالیت بیشتری دارند و به مطالب آموزشی علاقه نشان می‌دهند.';
    } else if (keywords.time.some(keyword => userMessage.includes(keyword))) {
        response = 'ساعات اوج فعالیت کاربران بین 18 تا 22 است، با بیشترین میزان مشارکت در روزهای یکشنبه و سه‌شنبه.';
    } else if (userMessage.length < 10) {
        response = 'لطفاً سوال خود را کامل‌تر بپرسید تا بتوانم پاسخ مناسبی ارائه دهم.';
    } else {
        // پاسخ عمومی برای سایر سوالات
        const generalResponses = [
            'بر اساس داده‌های اخیر، مباحث مرتبط با هوش مصنوعی و یادگیری ماشین بیشترین توجه را جلب کرده‌اند.',
            'تحلیل‌ها نشان می‌دهد محتوای آموزشی و راهنماها بیشترین نرخ تعامل را در میان کاربران دارند.',
            'در هفته گذشته، توییت‌های حاوی تصویر یا ویدیو 40% تعامل بیشتری نسبت به توییت‌های متنی داشته‌اند.',
            'کاربران بیشتر به محتوای کوتاه با پیام روشن و مستقیم واکنش نشان می‌دهند.',
            'بررسی داده‌ها نشان می‌دهد بهترین زمان برای انتشار محتوا ساعت 19 تا 21 است.'
        ];
        
        // انتخاب یک پاسخ تصادفی
        response = generalResponses[Math.floor(Math.random() * generalResponses.length)];
    }
    
    return response;
}