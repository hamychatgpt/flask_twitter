/**
 * ایجاد ابر کلمات با استفاده از D3.js و D3-Cloud
 * این کد پیشرفته‌تر برای ابر کلمات است که می‌تواند جایگزین کد داخل قالب شود
 */
function createWordCloud(containerId, words) {
    // پاکسازی محتویات قبلی
    document.getElementById(containerId).innerHTML = '';
    
    // تنظیمات ابر کلمات
    const width = document.getElementById(containerId).offsetWidth;
    const height = 400;
    const fontFamily = 'Vazir';
    
    // تنظیم اندازه کلمات بر اساس فراوانی
    const fontSize = d3.scaleLinear()
        .domain([d3.min(words, d => d.size), d3.max(words, d => d.size)])
        .range([15, 50]);
    
    // رنگ‌بندی کلمات
    const colorScale = d3.scaleSequential()
        .domain([0, words.length])
        .interpolator(d3.interpolateInferno);
    
    // ایجاد طرح ابر کلمات
    d3.layout.cloud()
        .size([width, height])
        .words(words)
        .padding(5)
        .rotate(() => ~~(Math.random() * 2) * 45) // چرخش تصادفی کلمات
        .font(fontFamily)
        .fontSize(d => fontSize(d.size))
        .spiral('archimedean') // نوع چیدمان
        .on("end", draw)
        .start();
    
    // رسم ابر کلمات
    function draw(words) {
        const svg = d3.select("#" + containerId).append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("class", "wordcloud");
        
        const wordGroup = svg.append("g")
            .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");
        
        wordGroup.selectAll("text")
            .data(words)
            .enter().append("text")
            .style("font-size", d => d.size + "px")
            .style("font-family", fontFamily)
            .style("fill", (d, i) => colorScale(i))
            .attr("text-anchor", "middle")
            .attr("transform", d => "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")")
            .text(d => d.text)
            .on("mouseover", function() {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .style("font-size", d => (d.size + 5) + "px")
                    .style("cursor", "pointer")
                    .style("fill", "#1da1f2");
            })
            .on("mouseout", function(d, i) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .style("font-size", d => d.size + "px")
                    .style("fill", colorScale(i));
            });
    }
}

/**
 * ساخت داده‌های نمونه برای ابر کلمات
 * در نسخه واقعی، این داده‌ها از API بک‌اند دریافت می‌شوند
 */
function generateWordCloudData() {
    // کلمات نمونه مرتبط با توییتر و شبکه‌های اجتماعی فارسی
    const sampleWords = [
        "توییتر", "توییت", "ریتوییت", "هشتگ", "لایک", 
        "کامنت", "فالو", "ترند", "اکانت", "پروفایل", 
        "تایم‌لاین", "منشن", "استوری", "پست", "دایرکت", 
        "نوتیفیکیشن", "اینفلوئنسر", "کانتنت", "دنبال‌کننده", "ویرایش", 
        "الگوریتم", "فیلتر", "اکسپلور", "انتشار", "بازنشر", 
        "محتوا", "رسانه", "عکس", "ویدیو", "گیف"
    ];
    
    return sampleWords.map(word => {
        return {
            text: word,
            size: Math.floor(Math.random() * 40) + 10 // اندازه تصادفی بین 10 تا 50
        };
    });
}

/**
 * ساخت داده‌های نمونه برای تحلیل احساسات
 */
function generateSentimentData() {
    return {
        positive: Math.floor(Math.random() * 50) + 20,
        neutral: Math.floor(Math.random() * 60) + 30,
        negative: Math.floor(Math.random() * 30) + 10
    };
}

// اضافه کردن عملکرد کلیک به دکمه جستجو
document.addEventListener('DOMContentLoaded', function() {
    // فرم جستجو
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            // در حالت نمونه، از ارسال فرم جلوگیری نمی‌کنیم
            // اما در اینجا می‌توان عملکرد اضافی مانند نمایش لودینگ اضافه کرد
            const searchInput = searchForm.querySelector('input[name="q"]');
            if (searchInput && searchInput.value.trim() === '') {
                e.preventDefault();
                alert('لطفاً یک عبارت جستجو وارد کنید.');
            }
        });
    }
    
    // اگر ابر کلمات وجود داشت، آن را ایجاد کن
    const wordCloudContainer = document.getElementById('wordCloudContainer');
    if (wordCloudContainer) {
        const wordCloudData = generateWordCloudData();
        createWordCloud('wordCloudContainer', wordCloudData);
    }
});