/**
 * این فایل ساختار داده‌های نمونه را برای داشبورد تحلیل توییتر تعریف می‌کند
 * در یک پیاده‌سازی واقعی، این داده‌ها از API بک‌اند یا پایگاه داده دریافت می‌شوند
 */

/**
 * ساختار کلی داده‌های داشبورد
 */
const dashboardData = {
    total_tweets: 1250,
    sentiment: {
        positive: 450,
        neutral: 650,
        negative: 150
    },
    top_hashtags: ['#پایتون', '#فلسک', '#توسعه_وب', '#داده_کاوی', '#هوش_مصنوعی', '#توییتر', '#تحلیل_داده', '#یادگیری_ماشین'],
    daily_activity: [
        { day: 'شنبه', count: 65 },
        { day: 'یکشنبه', count: 59 },
        { day: 'دوشنبه', count: 80 },
        { day: 'سه‌شنبه', count: 81 },
        { day: 'چهارشنبه', count: 56 },
        { day: 'پنج‌شنبه', count: 55 },
        { day: 'جمعه', count: 40 }
    ],
    sentiment_trend: [
        { date: '1401/01/01', positive: 45, neutral: 65, negative: 15 },
        { date: '1401/01/02', positive: 50, neutral: 60, negative: 10 },
        { date: '1401/01/03', positive: 40, neutral: 70, negative: 20 },
        // ... و غیره
    ],
    topic_sentiment: {
        'سیاست': { positive: 65, negative: 28 },
        'اقتصاد': { positive: 59, negative: 48 },
        'فناوری': { positive: 90, negative: 40 },
        'ورزش': { positive: 81, negative: 19 },
        'سرگرمی': { positive: 76, negative: 36 },
        'علمی': { positive: 55, negative: 27 }
    },
    engagement: [
        { tweet_id: 1, likes: 10, retweets: 5, replies: 10 },
        { tweet_id: 2, likes: 20, retweets: 10, replies: 15 },
        { tweet_id: 3, likes: 30, retweets: 15, replies: 20 },
        { tweet_id: 4, likes: 40, retweets: 20, replies: 25 },
        { tweet_id: 5, likes: 50, retweets: 25, replies: 30 }
    ]
};

/**
 * ساختار داده‌های نتایج تحلیل برای یک عبارت جستجو
 */
const analysisResults = {
    query: 'پایتون',
    total_matching_tweets: 250,
    sentiment: {
        positive: 120,
        neutral: 100,
        negative: 30
    },
    timeline: [
        { date: '1401/01/01', count: 15 },
        { date: '1401/01/02', count: 18 },
        { date: '1401/01/03', count: 12 },
        { date: '1401/01/04', count: 20 },
        { date: '1401/01/05', count: 25 },
        { date: '1401/01/06', count: 22 },
        { date: '1401/01/07', count: 16 },
        { date: '1401/01/08', count: 19 },
        { date: '1401/01/09', count: 14 },
        { date: '1401/01/10', count: 17 },
        { date: '1401/01/11', count: 21 }
    ],
    keywords: [
        { word: 'پایتون', count: 250 },
        { word: 'فلسک', count: 120 },
        { word: 'جنگو', count: 95 },
        { word: 'برنامه‌نویسی', count: 85 },
        { word: 'کدنویسی', count: 75 },
        { word: 'یادگیری‌ماشین', count: 70 },
        { word: 'توسعه‌وب', count: 65 },
        { word: 'هوش‌مصنوعی', count: 60 }
    ],
    engagement: {
        likes: 150,
        retweets: 80,
        replies: 45,
        quotes: 30,
        shares: 25,
        saves: 15
    },
    word_cloud: [
        { text: 'پایتون', size: 45 },
        { text: 'فلسک', size: 38 },
        { text: 'جنگو', size: 35 },
        { text: 'برنامه‌نویسی', size: 32 },
        { text: 'کدنویسی', size: 30 },
        { text: 'یادگیری‌ماشین', size: 28 },
        { text: 'توسعه‌وب', size: 26 },
        { text: 'هوش‌مصنوعی', size: 25 },
        { text: 'پایتونیست', size: 22 },
        { text: 'داده‌کاوی', size: 20 },
        { text: 'دیتاساینس', size: 18 },
        { text: 'نیوپایتون', size: 16 },
        { text: 'پایرتچ', size: 15 },
        { text: 'نام‌پای', size: 14 },
        { text: 'پاندا', size: 12 }
    ],
    influential_tweets: [
        {
            id: 1,
            user: 'پایتون_ایران',
            content: 'چطور می‌توانیم از پایتون برای تحلیل داده‌های بزرگ استفاده کنیم؟ در این آموزش به شما نشان می‌دهیم چگونه با پایتون می‌توانید داده‌های حجیم را پردازش کنید.',
            stats: { likes: 320, retweets: 95, replies: 45 },
            date: '1401/01/01'
        },
        {
            id: 2,
            user: 'برنامه‌نویس_وب',
            content: 'فریمورک فلسک برای توسعه وب‌سایت‌های کوچک تا متوسط بسیار مناسب است. سادگی و انعطاف‌پذیری فلسک باعث محبوبیت آن شده است.',
            stats: { likes: 280, retweets: 75, replies: 30 },
            date: '1401/01/03'
        },
        {
            id: 3,
            user: 'هوش_مصنوعی',
            content: 'استفاده از کتابخانه‌های پایتون مانند TensorFlow و PyTorch برای پیاده‌سازی الگوریتم‌های یادگیری عمیق بسیار رایج است.',
            stats: { likes: 250, retweets: 65, replies: 25 },
            date: '1401/01/05'
        },
        {
            id: 4,
            user: 'دیتاساینتیست',
            content: 'چرا پایتون زبان اول داده‌کاوی و علم داده است؟ سادگی، کتابخانه‌های قدرتمند و جامعه بزرگ از دلایل اصلی است.',
            stats: { likes: 220, retweets: 60, replies: 20 },
            date: '1401/01/07'
        },
        {
            id: 5,
            user: 'مهندس_نرم‌افزار',
            content: 'جنگو یک فریمورک قدرتمند برای توسعه وب‌سایت‌های بزرگ است که از معماری MVT استفاده می‌کند و امنیت بالایی دارد.',
            stats: { likes: 190, retweets: 50, replies: 15 },
            date: '1401/01/09'
        }
    ]
};

/**
 * ساختار داده‌های جستجوی توییت‌ها
 */
const searchResults = {
    query: 'پایتون',
    total_results: 250,
    tweets: [
        {
            id: 1,
            user: {
                username: 'پایتون_ایران',
                display_name: 'پایتون ایران',
                profile_image: 'profile1.jpg'
            },
            content: 'چطور می‌توانیم از پایتون برای تحلیل داده‌های بزرگ استفاده کنیم؟ در این آموزش به شما نشان می‌دهیم چگونه با پایتون می‌توانید داده‌های حجیم را پردازش کنید.',
            created_at: '1401/01/01 12:30',
            stats: {
                likes: 320,
                retweets: 95,
                replies: 45
            },
            sentiment: 'neutral',
            media: []
        },
        {
            id: 2,
            user: {
                username: 'برنامه‌نویس_وب',
                display_name: 'برنامه‌نویس وب',
                profile_image: 'profile2.jpg'
            },
            content: 'فریمورک فلسک برای توسعه وب‌سایت‌های کوچک تا متوسط بسیار مناسب است. سادگی و انعطاف‌پذیری فلسک باعث محبوبیت آن شده است.',
            created_at: '1401/01/03 14:45',
            stats: {
                likes: 280,
                retweets: 75,
                replies: 30
            },
            sentiment: 'positive',
            media: []
        },
        {
            id: 3,
            user: {
                username: 'هوش_مصنوعی',
                display_name: 'هوش مصنوعی',
                profile_image: 'profile3.jpg'
            },
            content: 'استفاده از کتابخانه‌های پایتون مانند TensorFlow و PyTorch برای پیاده‌سازی الگوریتم‌های یادگیری عمیق بسیار رایج است.',
            created_at: '1401/01/05 09:15',
            stats: {
                likes: 250,
                retweets: 65,
                replies: 25
            },
            sentiment: 'positive',
            media: []
        },
        {
            id: 4,
            user: {
                username: 'دیتاساینتیست',
                display_name: 'دیتا ساینتیست',
                profile_image: 'profile4.jpg'
            },
            content: 'چرا پایتون زبان اول داده‌کاوی و علم داده است؟ سادگی، کتابخانه‌های قدرتمند و جامعه بزرگ از دلایل اصلی است.',
            created_at: '1401/01/07 18:20',
            stats: {
                likes: 220,
                retweets: 60,
                replies: 20
            },
            sentiment: 'positive',
            media: []
        },
        {
            id: 5,
            user: {
                username: 'مهندس_نرم‌افزار',
                display_name: 'مهندس نرم‌افزار',
                profile_image: 'profile5.jpg'
            },
            content: 'جنگو یک فریمورک قدرتمند برای توسعه وب‌سایت‌های بزرگ است که از معماری MVT استفاده می‌کند و امنیت بالایی دارد.',
            created_at: '1401/01/09 11:30',
            stats: {
                likes: 190,
                retweets: 50,
                replies: 15
            },
            sentiment: 'neutral',
            media: []
        }
    ]
};

/**
 * تابع برای گرفتن داده‌های داشبورد
 * در یک پیاده‌سازی واقعی، این داده‌ها از API بک‌اند دریافت می‌شوند
 */
async function fetchDashboardData() {
    // ساخت شبیه‌سازی تأخیر شبکه
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(dashboardData);
        }, 500);
    });
}

/**
 * تابع برای گرفتن نتایج تحلیل برای یک عبارت جستجو
 * در یک پیاده‌سازی واقعی، این داده‌ها از API بک‌اند دریافت می‌شوند
 */
async function fetchAnalysisResults(query) {
    // ساخت شبیه‌سازی تأخیر شبکه
    return new Promise((resolve) => {
        setTimeout(() => {
            // کپی داده‌های نمونه و تغییر عبارت جستجو
            const results = JSON.parse(JSON.stringify(analysisResults));
            results.query = query;
            resolve(results);
        }, 800);
    });
}

/**
 * تابع برای گرفتن نتایج جستجوی توییت‌ها
 * در یک پیاده‌سازی واقعی، این داده‌ها از API بک‌اند دریافت می‌شوند
 */
async function fetchSearchResults(query) {
    // ساخت شبیه‌سازی تأخیر شبکه
    return new Promise((resolve) => {
        setTimeout(() => {
            // کپی داده‌های نمونه و تغییر عبارت جستجو
            const results = JSON.parse(JSON.stringify(searchResults));
            results.query = query;
            resolve(results);
        }, 600);
    });
}