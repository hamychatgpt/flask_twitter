// فایل JavaScript اصلی برای تحلیلگر توییتر

// منتظر بارگذاری DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('تحلیلگر توییتر آماده شد');
    
    // مخفی کردن خودکار پیام‌های فلش پس از 5 ثانیه
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.display = 'none';
            }, 500);
        }, 5000);
    });
    
    // مدیریت فرم جستجو در صفحه تحلیل
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.getElementById('search-query').value;
            
            if (!query) return;
            
            // هدایت به صفحه جستجو با پارامتر مورد نظر
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        });
    }
});

// تابع برای آماده‌سازی نمودار احساسات
function setupSentimentChart(elementId, positive, neutral, negative) {
    // بررسی وجود المان و کتابخانه Chart.js
    if (!document.getElementById(elementId) || typeof Chart === 'undefined') {
        return;
    }
    
    const ctx = document.getElementById(elementId).getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['مثبت', 'خنثی', 'منفی'],
            datasets: [{
                label: 'تحلیل احساسات',
                data: [positive, neutral, negative],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.7)',
                    'rgba(108, 117, 125, 0.7)',
                    'rgba(220, 53, 69, 0.7)'
                ],
                borderColor: [
                    'rgb(40, 167, 69)',
                    'rgb(108, 117, 125)',
                    'rgb(220, 53, 69)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'توزیع احساسات در توییت‌ها',
                    font: {
                        family: 'Vazir',
                        size: 16
                    }
                },
                legend: {
                    labels: {
                        font: {
                            family: 'Vazir'
                        }
                    }
                }
            },
            font: {
                family: 'Vazir'
            }
        }
    });
}


/**
 * رندر نمودار تحلیل احساسات
 * @param {string} canvasId - شناسه المان canvas 
 * @param {Object} sentiment - داده‌های احساسات
 */
function renderSentimentChart(canvasId, sentiment) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['مثبت', 'خنثی', 'منفی'],
            datasets: [{
                data: [sentiment.positive, sentiment.neutral, sentiment.negative],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.7)',  // سبز برای مثبت
                    'rgba(201, 203, 207, 0.7)', // خاکستری برای خنثی
                    'rgba(255, 99, 132, 0.7)'   // قرمز برای منفی
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(201, 203, 207, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                    rtl: true,
                    labels: {
                        font: {
                            family: 'Vazir'
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'توزیع احساسات در توییت‌ها',
                    font: {
                        family: 'Vazir',
                        size: 16
                    }
                }
            }
        }
    });
}