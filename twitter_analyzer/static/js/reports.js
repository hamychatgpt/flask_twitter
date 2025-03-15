// فایل JavaScript بهینه‌شده برای بخش گزارش‌ها

document.addEventListener('DOMContentLoaded', function() {
    // عناصر صفحه
    const statusElement = document.getElementById('status');
    const reportsTableBody = document.getElementById('reports-tbody');
    const generateReportBtn = document.getElementById('generate-report-btn');
    const generateReportModal = document.getElementById('generate-report-modal');
    const generateReportForm = document.getElementById('generate-report-form');
    const submitGenerateReportBtn = document.getElementById('submit-generate-report');
    const generateErrorElement = document.getElementById('generate-error');
    const reportDetailsModal = document.getElementById('report-details-modal');
    const detailsErrorElement = document.getElementById('details-error');
    
    // دکمه‌های بستن مودال
    const closeGenerateModalBtn = document.getElementById('close-generate-modal');
    const cancelGenerateBtn = document.getElementById('cancel-generate-btn');
    const closeDetailsModalBtn = document.getElementById('close-details-modal');
    const closeDetailsBtn = document.getElementById('close-details-btn');
    
    // دریافت توکن CSRF
    const getCsrfToken = () => {
        // ابتدا سعی می‌کنیم از تگ meta با نام csrf-token بگیریم
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) return metaToken.content;
        
        // اگر نبود از کوکی می‌گیریم
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrf_token') return value;
        }
        
        // در نهایت از یک فیلد مخفی در فرم می‌گیریم
        const tokenInput = document.querySelector('input[name="csrf_token"]');
        if (tokenInput) return tokenInput.value;
        
        return '';
    };
    
    // دریافت لیست گزارش‌ها
    function fetchReports() {
        statusElement.textContent = 'در حال بارگذاری گزارش‌ها...';
        statusElement.className = 'reports-status';
        
        fetch('/reports/summary')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`خطای HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    if (data.reports && data.reports.length === 0) {
                        statusElement.textContent = 'هیچ گزارشی یافت نشد.';
                        statusElement.className = 'reports-status';
                    } else {
                        statusElement.style.display = 'none';
                        renderReportsTable(data.reports);
                    }
                } else {
                    statusElement.textContent = data.message || 'خطا در بارگذاری گزارش‌ها';
                    statusElement.className = 'reports-status error';
                }
            })
            .catch(error => {
                console.error('Error fetching reports:', error);
                statusElement.textContent = 'خطا در بارگذاری گزارش‌ها: ' + error.message;
                statusElement.className = 'reports-status error';
            });
    }
    
    // تابع رندر جدول گزارش‌ها
    function renderReportsTable(reports) {
        if (!reports || !Array.isArray(reports)) {
            console.error('Invalid reports data:', reports);
            statusElement.textContent = 'داده‌های نامعتبر گزارش‌ها';
            statusElement.className = 'reports-status error';
            statusElement.style.display = 'block';
            return;
        }
        
        reportsTableBody.innerHTML = '';
        
        reports.forEach(report => {
            const row = document.createElement('tr');
            
            // تبدیل تاریخ‌ها
            let createdDate;
            try {
                createdDate = new Date(report.created_at);
                if (isNaN(createdDate)) throw new Error('Invalid date');
            } catch (e) {
                console.warn('Invalid date format:', report.created_at);
                createdDate = new Date(); // استفاده از تاریخ فعلی به عنوان جایگزین
            }
            
            // ایجاد ردیف جدول
            row.innerHTML = `
                <td>${report.id || ''}</td>
                <td>${report.period_name || report.period || ''}</td>
                <td>${createdDate.toLocaleString('fa-IR')}</td>
                <td>${report.total_tweets || 0}</td>
                <td>${report.keywords && report.keywords.length > 0 ? report.keywords.join(', ') : '-'}</td>
                <td>
                    <button class="btn-view report-action-btn view-report" data-id="${report.id}">
                        مشاهده
                    </button>
                </td>
            `;
            
            reportsTableBody.appendChild(row);
        });
        
        // اضافه کردن رویداد به دکمه‌های مشاهده
        document.querySelectorAll('.view-report').forEach(button => {
            button.addEventListener('click', function() {
                const reportId = this.getAttribute('data-id');
                if (reportId) {
                    viewReportDetails(reportId);
                } else {
                    console.error('Missing report ID');
                }
            });
        });
    }
    
    // تابع تولید گزارش جدید
    function generateReport() {
        // جمع‌آوری داده‌های فرم
        const formData = new FormData(generateReportForm);
        const period = formData.get('period');
        const keywordsStr = formData.get('keywords');
        
        // پردازش کلمات کلیدی
        let keywords = null;
        if (keywordsStr) {
            keywords = keywordsStr.split(',').map(k => k.trim()).filter(k => k);
        }
        
        // نمایش وضعیت بارگذاری
        submitGenerateReportBtn.disabled = true;
        submitGenerateReportBtn.textContent = 'در حال تولید...';
        generateErrorElement.style.display = 'none';
        
        // ارسال درخواست با CSRF توکن
        fetch('/reports/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                period: period,
                keywords: keywords
            }),
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            submitGenerateReportBtn.disabled = false;
            submitGenerateReportBtn.textContent = 'تولید گزارش';
            
            if (data.status === 'success') {
                // بستن مودال و بروزرسانی لیست
                hideModal(generateReportModal);
                fetchReports();
                
                // نمایش جزئیات گزارش جدید
                if (data.report && data.report.period) {
                    renderReportDetails(data.report);
                    showModal(reportDetailsModal);
                }
            } else {
                generateErrorElement.textContent = data.message || 'خطا در تولید گزارش';
                generateErrorElement.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error generating report:', error);
            submitGenerateReportBtn.disabled = false;
            submitGenerateReportBtn.textContent = 'تولید گزارش';
            generateErrorElement.textContent = 'خطا در تولید گزارش: ' + error.message;
            generateErrorElement.style.display = 'block';
        });
    }
    
    // تابع مشاهده جزئیات گزارش
    function viewReportDetails(reportId) {
        if (!reportId) {
            console.error('Invalid report ID');
            return;
        }
        
        // نمایش وضعیت بارگذاری
        document.getElementById('report-period').textContent = 'در حال بارگذاری...';
        detailsErrorElement.style.display = 'none';
        
        // نمایش مودال
        showModal(reportDetailsModal);
        
        // دریافت جزئیات گزارش
        fetch(`/reports/${reportId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`خطای HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success' && data.report) {
                    renderReportDetails(data.report);
                } else {
                    detailsErrorElement.textContent = data.message || 'خطا در بارگذاری جزئیات گزارش';
                    detailsErrorElement.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error fetching report details:', error);
                detailsErrorElement.textContent = 'خطا در بارگذاری جزئیات گزارش: ' + error.message;
                detailsErrorElement.style.display = 'block';
            });
    }
    
    // تابع رندر جزئیات گزارش
    function renderReportDetails(report) {
        if (!report) {
            console.error('Invalid report data');
            detailsErrorElement.textContent = 'داده‌های گزارش نامعتبر است';
            detailsErrorElement.style.display = 'block';
            return;
        }
        
        const periodDisplay = {
            'minute': 'دقیقه گذشته',
            'hour': 'ساعت گذشته',
            'day': 'روز گذشته'
        };
        
        // اطلاعات پایه
        document.getElementById('report-period').textContent = report.period_name || periodDisplay[report.period] || report.period || '';
        
        // تبدیل تاریخ‌ها
        try {
            document.getElementById('report-start-time').textContent = new Date(report.start_time).toLocaleString('fa-IR');
            document.getElementById('report-end-time').textContent = new Date(report.end_time).toLocaleString('fa-IR');
        } catch (e) {
            console.warn('Invalid date format in report', e);
            document.getElementById('report-start-time').textContent = report.start_time || '-';
            document.getElementById('report-end-time').textContent = report.end_time || '-';
        }
        
        // آمار
        const stats = report.stats || {};
        document.getElementById('report-total-tweets').textContent = stats.total_tweets || 0;
        document.getElementById('report-total-likes').textContent = stats.total_likes || 0;
        document.getElementById('report-total-retweets').textContent = stats.total_retweets || 0;
        
        // هشتگ‌های برتر
        const topHashtagsElement = document.getElementById('top-hashtags');
        topHashtagsElement.innerHTML = '';
        
        if (stats.top_hashtags && stats.top_hashtags.length > 0) {
            stats.top_hashtags.forEach(hashtag => {
                const li = document.createElement('li');
                li.textContent = `#${hashtag.text || ''} (${hashtag.count || 0})`;
                topHashtagsElement.appendChild(li);
            });
        } else {
            topHashtagsElement.innerHTML = '<li>هیچ هشتگی یافت نشد</li>';
        }
        
        // منشن‌های برتر
        const topMentionsElement = document.getElementById('top-mentions');
        topMentionsElement.innerHTML = '';
        
        if (stats.top_mentions && stats.top_mentions.length > 0) {
            stats.top_mentions.forEach(mention => {
                const li = document.createElement('li');
                li.textContent = `@${mention.username || ''} (${mention.count || 0})`;
                topMentionsElement.appendChild(li);
            });
        } else {
            topMentionsElement.innerHTML = '<li>هیچ منشنی یافت نشد</li>';
        }
        
        // نمودار احساسات - با بررسی وجود Chart.js
        if (typeof Chart !== 'undefined') {
            renderSentimentChart(stats.sentiment || {});
        } else {
            console.error('Chart.js is not loaded. Sentiment chart will not be rendered.');
            document.getElementById('sentiment-chart').innerHTML = 
                '<div class="chart-error">کتابخانه Chart.js بارگذاری نشده است. نمودار احساسات قابل نمایش نیست.</div>';
        }
        
        // تحلیل هوش مصنوعی
        const aiAnalysisCard = document.getElementById('ai-analysis-card');
        const aiAnalysisContent = document.getElementById('ai-analysis-content');
        
        if (stats.ai_analysis) {
            let analysisText = '';
            if (typeof stats.ai_analysis === 'string') {
                analysisText = stats.ai_analysis;
            } else {
                try {
                    analysisText = JSON.stringify(stats.ai_analysis, null, 2);
                } catch (e) {
                    analysisText = 'خطا در پردازش تحلیل هوش مصنوعی';
                    console.error('Error processing AI analysis:', e);
                }
            }
            
            aiAnalysisContent.textContent = analysisText;
            aiAnalysisCard.style.display = 'block';
        } else {
            aiAnalysisCard.style.display = 'none';
        }
        
        // توییت‌های برتر
        const topTweetsElement = document.getElementById('top-tweets');
        topTweetsElement.innerHTML = '';
        
        if (report.top_tweets && report.top_tweets.length > 0) {
            report.top_tweets.forEach(tweet => {
                // تعیین کلاس رنگ بر اساس احساسات
                let sentimentClass = '';
                if (tweet.sentiment === 'positive') {
                    sentimentClass = 'positive';
                } else if (tweet.sentiment === 'negative') {
                    sentimentClass = 'negative';
                }
                
                const tweetDiv = document.createElement('div');
                tweetDiv.className = `report-tweet ${sentimentClass}`;
                
                tweetDiv.innerHTML = `
                    <div class="report-tweet-text">${tweet.text || ''}</div>
                    <div class="report-tweet-stats">
                        <span class="tweet-stat">لایک: ${tweet.likes || 0}</span>
                        <span class="tweet-stat">ریتوییت: ${tweet.retweets || 0}</span>
                        <span class="tweet-stat">پاسخ: ${tweet.replies || 0}</span>
                    </div>
                `;
                
                topTweetsElement.appendChild(tweetDiv);
            });
        } else {
            topTweetsElement.innerHTML = '<p style="text-align: center;">هیچ توییتی یافت نشد</p>';
        }
    }
    
    // تابع رندر نمودار احساسات - با بررسی بیشتر وجود Chart.js
    function renderSentimentChart(sentimentData) {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not available');
            return;
        }
        
        const chartContainer = document.getElementById('sentiment-chart');
        if (!chartContainer) {
            console.error('Chart container not found');
            return;
        }
        
        // پاکسازی نمودار قبلی
        chartContainer.innerHTML = '';
        
        const canvas = document.createElement('canvas');
        canvas.id = 'sentiment-chart-canvas';
        canvas.height = 300;
        chartContainer.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('Could not get canvas context');
            return;
        }
        
        // تبدیل داده‌ها به فرمت مناسب چارت
        const labels = [];
        const data = [];
        const colors = [];
        
        if (sentimentData.positive) {
            labels.push('مثبت');
            data.push(sentimentData.positive);
            colors.push('#28a745');
        }
        
        if (sentimentData.negative) {
            labels.push('منفی');
            data.push(sentimentData.negative);
            colors.push('#dc3545');
        }
        
        if (sentimentData.neutral) {
            labels.push('خنثی');
            data.push(sentimentData.neutral);
            colors.push('#6c757d');
        }
        
        if (sentimentData.unknown) {
            labels.push('نامشخص');
            data.push(sentimentData.unknown);
            colors.push('#17a2b8');
        }
        
        // اطمینان از وجود داده
        if (data.length === 0) {
            chartContainer.innerHTML = '<div class="chart-empty">داده‌ای برای نمایش نمودار وجود ندارد</div>';
            return;
        }
        
        try {
            // ایجاد چارت جدید با حالت امن
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                font: {
                                    family: 'Vazir'
                                }
                            }
                        }
                    }
                }
            });
        } catch (e) {
            console.error('Error creating chart:', e);
            chartContainer.innerHTML = `<div class="chart-error">خطا در ایجاد نمودار: ${e.message}</div>`;
        }
    }
    
    // تابع نمایش مودال
    function showModal(modal) {
        if (modal) {
            modal.style.display = 'flex';
        }
    }
    
    // تابع مخفی کردن مودال
    function hideModal(modal) {
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    // گوش دادن به رویدادها
    if (generateReportBtn) {
        generateReportBtn.addEventListener('click', function() {
            showModal(generateReportModal);
        });
    }
    
    // رویدادهای بستن مودال
    if (closeGenerateModalBtn) {
        closeGenerateModalBtn.addEventListener('click', function() {
            hideModal(generateReportModal);
        });
    }
    
    if (cancelGenerateBtn) {
        cancelGenerateBtn.addEventListener('click', function() {
            hideModal(generateReportModal);
        });
    }
    
    if (closeDetailsModalBtn) {
        closeDetailsModalBtn.addEventListener('click', function() {
            hideModal(reportDetailsModal);
        });
    }
    
    if (closeDetailsBtn) {
        closeDetailsBtn.addEventListener('click', function() {
            hideModal(reportDetailsModal);
        });
    }
    
    // بستن مودال با کلیک بیرون از آن
    window.addEventListener('click', function(event) {
        if (event.target === generateReportModal) {
            hideModal(generateReportModal);
        }
        if (event.target === reportDetailsModal) {
            hideModal(reportDetailsModal);
        }
    });
    
    if (submitGenerateReportBtn) {
        submitGenerateReportBtn.addEventListener('click', function() {
            generateReport();
        });
    }
    
    // شروع دریافت گزارش‌ها
    fetchReports();
});