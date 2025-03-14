// 1. نمودار خطی فعالیت روزانه
function createDailyActivityChart() {
    const ctx = document.getElementById('dailyActivityChart').getContext('2d');
    
    // داده های نمونه - تعداد توییت های روزانه در یک هفته اخیر
    const data = {
        labels: ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه'],
        datasets: [{
            label: 'تعداد توییت‌ها',
            data: [65, 59, 80, 81, 56, 55, 40],
            fill: false,
            borderColor: '#1da1f2',
            tension: 0.1
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'فعالیت روزانه (تعداد توییت‌ها)'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 2. نمودار دایره‌ای توزیع احساسات (مثبت، خنثی، منفی)
function createSentimentPieChart() {
    const ctx = document.getElementById('sentimentPieChart').getContext('2d');
    
    // داده های نمونه - توزیع احساسات
    const data = {
        labels: ['مثبت', 'خنثی', 'منفی'],
        datasets: [{
            label: 'توزیع احساسات',
            data: [45, 65, 15],
            backgroundColor: [
                '#28a745',  // سبز برای مثبت
                '#6c757d',  // خاکستری برای خنثی
                '#dc3545'   // قرمز برای منفی
            ],
            hoverOffset: 4
        }]
    };
    
    new Chart(ctx, {
        type: 'pie',
        data: data,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'توزیع احساسات در توییت‌ها'
                },
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// 3. نمودار ستونی هشتگ‌های محبوب
function createTopHashtagsChart() {
    const ctx = document.getElementById('topHashtagsChart').getContext('2d');
    
    // داده های نمونه - هشتگ‌های محبوب
    const data = {
        labels: ['#پایتون', '#فلسک', '#توسعه_وب', '#داده_کاوی', '#هوش_مصنوعی'],
        datasets: [{
            label: 'تعداد استفاده',
            data: [120, 95, 85, 75, 65],
            backgroundColor: '#17a2b8'
        }]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            indexAxis: 'y',  // برای نمایش افقی ستون‌ها
            plugins: {
                title: {
                    display: true,
                    text: 'هشتگ‌های محبوب'
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 4. نمودار خطی روند احساسات در طول زمان
function createSentimentTrendChart() {
    const ctx = document.getElementById('sentimentTrendChart').getContext('2d');
    
    // داده های نمونه - روند احساسات در طول زمان (30 روز)
    const labels = Array.from({length: 30}, (_, i) => `${i+1}`);
    
    const data = {
        labels: labels,
        datasets: [
            {
                label: 'مثبت',
                data: Array.from({length: 30}, () => Math.floor(Math.random() * 50) + 20),
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.2)',
                fill: true
            },
            {
                label: 'خنثی',
                data: Array.from({length: 30}, () => Math.floor(Math.random() * 40) + 30),
                borderColor: '#6c757d',
                backgroundColor: 'rgba(108, 117, 125, 0.2)',
                fill: true
            },
            {
                label: 'منفی',
                data: Array.from({length: 30}, () => Math.floor(Math.random() * 30) + 10),
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.2)',
                fill: true
            }
        ]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'روند احساسات در 30 روز گذشته'
                },
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    stacked: false
                }
            }
        }
    });
}

// 5. نمودار رادار برای مقایسه موضوعات مختلف
function createTopicsRadarChart() {
    const ctx = document.getElementById('topicsRadarChart').getContext('2d');
    
    // داده های نمونه - موضوعات توییت‌ها
    const data = {
        labels: ['سیاست', 'اقتصاد', 'فناوری', 'ورزش', 'سرگرمی', 'علمی'],
        datasets: [{
            label: 'توییت‌های مثبت',
            data: [65, 59, 90, 81, 76, 55],
            fill: true,
            backgroundColor: 'rgba(40, 167, 69, 0.2)',
            borderColor: '#28a745',
            pointBackgroundColor: '#28a745',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: '#28a745'
        }, {
            label: 'توییت‌های منفی',
            data: [28, 48, 40, 19, 36, 27],
            fill: true,
            backgroundColor: 'rgba(220, 53, 69, 0.2)',
            borderColor: '#dc3545',
            pointBackgroundColor: '#dc3545',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: '#dc3545'
        }]
    };
    
    new Chart(ctx, {
        type: 'radar',
        data: data,
        options: {
            responsive: true,
            elements: {
                line: {
                    borderWidth: 3
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'مقایسه احساسات در موضوعات مختلف'
                }
            }
        }
    });
}

// 6. نمودار حبابی برای نشان دادن تعامل‌ها (لایک، ریتوییت، پاسخ)
function createEngagementBubbleChart() {
    const ctx = document.getElementById('engagementBubbleChart').getContext('2d');
    
    // داده های نمونه - تعامل کاربران
    const data = {
        datasets: [{
            label: 'تعامل کاربران',
            data: [
                { x: 10, y: 5, r: 10 },   // کم لایک، کم ریتوییت، کم پاسخ
                { x: 20, y: 10, r: 15 },  // متوسط لایک، کم ریتوییت، متوسط پاسخ
                { x: 30, y: 15, r: 20 },  // متوسط لایک، متوسط ریتوییت، متوسط پاسخ
                { x: 40, y: 20, r: 25 },  // زیاد لایک، متوسط ریتوییت، زیاد پاسخ
                { x: 50, y: 25, r: 30 },  // خیلی زیاد لایک، زیاد ریتوییت، خیلی زیاد پاسخ
            ],
            backgroundColor: 'rgba(29, 161, 242, 0.7)'
        }]
    };
    
    new Chart(ctx, {
        type: 'bubble',
        data: data,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'تعامل کاربران (لایک، ریتوییت، پاسخ)'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `لایک: ${context.raw.x}, ریتوییت: ${context.raw.y}, پاسخ: ${context.raw.r}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'لایک'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'ریتوییت'
                    }
                }
            }
        }
    });
}

// اجرای همه نمودارها زمانی که صفحه کاملاً بارگذاری شده است
document.addEventListener('DOMContentLoaded', function() {
    // بررسی وجود المان‌ها قبل از ایجاد نمودارها
    if (document.getElementById('dailyActivityChart')) {
        createDailyActivityChart();
    }
    
    if (document.getElementById('sentimentPieChart')) {
        createSentimentPieChart();
    }
    
    if (document.getElementById('topHashtagsChart')) {
        createTopHashtagsChart();
    }
    
    if (document.getElementById('sentimentTrendChart')) {
        createSentimentTrendChart();
    }
    
    if (document.getElementById('topicsRadarChart')) {
        createTopicsRadarChart();
    }
    
    if (document.getElementById('engagementBubbleChart')) {
        createEngagementBubbleChart();
    }
});