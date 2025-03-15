// فایل JavaScript برای بخش رصد لحظه‌ای

document.addEventListener('DOMContentLoaded', function() {
    // اتصال به Socket.IO
    const socket = io();
    const tweetsContainer = document.getElementById('tweets-container');
    const statusElement = document.getElementById('status');
    const keywordInput = document.getElementById('keyword-input');
    const trackBtn = document.getElementById('track-btn');
    const stopBtn = document.getElementById('stop-btn');
    const clearBtn = document.getElementById('clear-btn');
    const autoScrollCheckbox = document.getElementById('auto-scroll');
    
    let currentKeyword = null;
    
    // رویداد اتصال
    socket.on('connect', function() {
        statusElement.textContent = 'اتصال برقرار شد';
        statusElement.className = 'realtime-status connected';
    });
    
    // رویداد قطع اتصال
    socket.on('disconnect', function() {
        statusElement.textContent = 'اتصال قطع شد. در حال تلاش مجدد...';
        statusElement.className = 'realtime-status disconnected';
    });
    
    // رویداد دریافت توییت
    socket.on('tweet', function(data) {
        console.log('Tweet received:', data);
        
        // تحلیل احساسات
        let sentiment = 'neutral';
        let sentimentText = 'خنثی';
        let sentimentClass = 'neutral';
        
        if (data.local_analysis && data.local_analysis.sentiment) {
            sentiment = data.local_analysis.sentiment;
            if (sentiment === 'positive') {
                sentimentText = 'مثبت';
                sentimentClass = 'positive';
            } else if (sentiment === 'negative') {
                sentimentText = 'منفی';
                sentimentClass = 'negative';
            }
        }
        
        // ایجاد کارت توییت
        const tweetCard = document.createElement('div');
        tweetCard.className = 'tweet-card';
        
        // محتوای کارت
        tweetCard.innerHTML = `
            <div class="tweet-header">
                <div class="tweet-user">
                    <span class="tweet-username">@${data.user}</span>
                    <span class="tweet-sentiment ${sentimentClass}">${sentimentText}</span>
                    <span class="tweet-score">امتیاز تعامل: ${data.engagement_score}</span>
                </div>
            </div>
            <div class="tweet-body">
                <div class="tweet-text">${data.text}</div>
                ${data.ai_analysis ? 
                    `<div class="tweet-ai-analysis">
                        <div class="tweet-ai-title">تحلیل هوش مصنوعی:</div>
                        <div>${formatAIAnalysis(data.ai_analysis)}</div>
                    </div>` : ''}
            </div>
        `;
        
        // افزودن به ابتدای لیست
        tweetsContainer.prepend(tweetCard);
        
        // اسکرول خودکار
        if (autoScrollCheckbox.checked) {
            tweetsContainer.scrollTop = 0;
        }
    });
    
    // رویداد پیوستن به اتاق
    socket.on('join_response', function(data) {
        statusElement.textContent = `در حال ردیابی: ${data.term}`;
        statusElement.className = 'realtime-status tracking';
        currentKeyword = data.term;
    });
    
    // رویداد خروج از اتاق
    socket.on('leave_response', function(data) {
        statusElement.textContent = 'ردیابی متوقف شد';
        statusElement.className = 'realtime-status';
        currentKeyword = null;
    });
    
    // شروع ردیابی
    trackBtn.addEventListener('click', function() {
        const keyword = keywordInput.value.trim();
        if (!keyword) {
            alert('لطفاً یک کلمه کلیدی وارد کنید');
            return;
        }
        
        // خروج از اتاق قبلی
        if (currentKeyword) {
            socket.emit('leave', { term: currentKeyword });
        }
        
        // پیوستن به اتاق جدید
        socket.emit('join', { term: keyword });
        keywordInput.value = '';
    });
    
    // توقف ردیابی
    stopBtn.addEventListener('click', function() {
        if (currentKeyword) {
            socket.emit('leave', { term: currentKeyword });
        }
    });
    
    // پاکسازی توییت‌ها
    clearBtn.addEventListener('click', function() {
        tweetsContainer.innerHTML = '';
    });
    
    // فرمت‌بندی تحلیل هوش مصنوعی
    function formatAIAnalysis(analysis) {
        if (typeof analysis === 'string') {
            return analysis;
        }
        
        try {
            // تبدیل به متن با فرمت مناسب
            if (analysis.sentiment) {
                const sentimentText = {
                    'positive': 'مثبت',
                    'negative': 'منفی',
                    'neutral': 'خنثی'
                };
                
                return `احساس: ${sentimentText[analysis.sentiment] || analysis.sentiment}
                       ${analysis.reason ? '<br>دلیل: ' + analysis.reason : ''}`;
            }
            
            return JSON.stringify(analysis, null, 2);
        } catch (error) {
            console.error('Error formatting AI analysis:', error);
            return JSON.stringify(analysis);
        }
    }
});



// فایل JavaScript برای مدیریت درخواست‌های API در بخش رصد لحظه‌ای

// افزودن توابع برای مدیریت درخواست‌های REST API رصد لحظه‌ای
document.addEventListener('DOMContentLoaded', function() {
    // دکمه‌های شروع و توقف دستی ردیابی از طریق REST API
    const manualStartBtn = document.getElementById('manual-start-btn');
    const manualStopBtn = document.getElementById('manual-stop-btn');
    const statusElement = document.getElementById('status');
    
    if (manualStartBtn) {
        manualStartBtn.addEventListener('click', function() {
            const keywordInput = document.getElementById('admin-keyword-input');
            if (!keywordInput || !keywordInput.value.trim()) {
                alert('لطفاً یک کلمه کلیدی وارد کنید');
                return;
            }
            
            // ارسال درخواست شروع ردیابی
            startTrackingAPI(keywordInput.value.trim());
        });
    }
    
    if (manualStopBtn) {
        manualStopBtn.addEventListener('click', function() {
            // ارسال درخواست توقف ردیابی
            stopTrackingAPI();
        });
    }
    
    // تابع دریافت وضعیت فعلی ردیابی
    function getTrackingStatus() {
        fetch('/realtime/status')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'active') {
                    statusElement.textContent = `در حال ردیابی: ${data.tracking_keywords.join(', ')}`;
                    statusElement.className = 'realtime-status tracking';
                } else {
                    statusElement.textContent = 'ردیابی غیرفعال است';
                    statusElement.className = 'realtime-status';
                }
            })
            .catch(error => {
                console.error('Error getting tracking status:', error);
                statusElement.textContent = 'خطا در دریافت وضعیت ردیابی';
                statusElement.className = 'realtime-status disconnected';
            });
    }
    
    // تابع شروع ردیابی از طریق API
    function startTrackingAPI(keywords) {
        // تبدیل به آرایه اگر رشته باشد
        if (typeof keywords === 'string') {
            keywords = keywords.split(',').map(k => k.trim()).filter(k => k);
        }
        
        manualStartBtn.disabled = true;
        manualStartBtn.textContent = 'در حال شروع...';
        
        fetch('/realtime/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                keywords: keywords
            })
        })
        .then(response => response.json())
        .then(data => {
            manualStartBtn.disabled = false;
            manualStartBtn.textContent = 'شروع ردیابی';
            
            if (data.status === 'success') {
                statusElement.textContent = data.message || `ردیابی با کلمات کلیدی ${data.tracking_keywords.join(', ')} شروع شد`;
                statusElement.className = 'realtime-status tracking';
            } else {
                statusElement.textContent = data.message || 'خطا در شروع ردیابی';
                statusElement.className = 'realtime-status disconnected';
            }
        })
        .catch(error => {
            console.error('Error starting tracking:', error);
            manualStartBtn.disabled = false;
            manualStartBtn.textContent = 'شروع ردیابی';
            statusElement.textContent = 'خطا در برقراری ارتباط با سرور';
            statusElement.className = 'realtime-status disconnected';
        });
    }
    
    // تابع توقف ردیابی از طریق API
    function stopTrackingAPI() {
        manualStopBtn.disabled = true;
        manualStopBtn.textContent = 'در حال توقف...';
        
        fetch('/realtime/stop', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            manualStopBtn.disabled = false;
            manualStopBtn.textContent = 'توقف ردیابی';
            
            if (data.status === 'success') {
                statusElement.textContent = data.message || 'ردیابی متوقف شد';
                statusElement.className = 'realtime-status';
            } else {
                statusElement.textContent = data.message || 'خطا در توقف ردیابی';
                statusElement.className = 'realtime-status disconnected';
            }
        })
        .catch(error => {
            console.error('Error stopping tracking:', error);
            manualStopBtn.disabled = false;
            manualStopBtn.textContent = 'توقف ردیابی';
            statusElement.textContent = 'خطا در برقراری ارتباط با سرور';
            statusElement.className = 'realtime-status disconnected';
        });
    }
    
    // دریافت وضعیت اولیه ردیابی
    if (statusElement) {
        getTrackingStatus();
    }
});