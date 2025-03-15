from flask import request, jsonify, current_app
from ..utils.anthropic_analyzer import AnthropicTextAnalyzer, IntegratedTextAnalyzer
from functools import wraps
import os
from . import analyzer_bp  # وارد کردن analyzer_bp از __init__.py

# دکوراتور برای بررسی وجود تحلیلگر متن
def requires_analyzer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'anthropic_analyzer' not in current_app.extensions:
            return jsonify({
                "status": "error", 
                "message": "Text analyzer is not configured. Please set ANTHROPIC_API_KEY."
            }), 503
        return f(*args, **kwargs)
    return decorated_function


def init_app(app):
    """
    راه‌اندازی تحلیلگر متن در برنامه Flask
    
    Args:
        app: نمونه برنامه Flask
    """
    # بررسی تنظیمات API key
    api_key = app.config.get('ANTHROPIC_API_KEY', os.environ.get('ANTHROPIC_API_KEY'))
    
    if not api_key:
        app.logger.warning("ANTHROPIC_API_KEY not set. Text analysis will not be available.")
        return
    
    # ایجاد نمونه تحلیلگر متن
    anthropic_analyzer = AnthropicTextAnalyzer(api_key=api_key, app=app)
    
    # بررسی وجود پردازشگر متن فارسی
    if 'persian_content_analyzer' in app.extensions:
        persian_processor = app.extensions['persian_content_analyzer']
        integrated_analyzer = IntegratedTextAnalyzer(anthropic_analyzer, persian_processor, app)
    else:
        app.logger.warning("PersianTextProcessor not found. Falling back to Anthropic only.")
        integrated_analyzer = IntegratedTextAnalyzer(anthropic_analyzer, app=app)


@analyzer_bp.route('/sentiment', methods=['POST'])
@requires_analyzer
def analyze_sentiment():
    """اندپوینت تحلیل احساسات متن"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({"status": "error", "message": "No text provided"}), 400
    
    text = data['text']
    force_full = data.get('force_full_analysis', False)
    
    analyzer = current_app.extensions['anthropic_analyzer']
    result = analyzer.analyze_sentiment(text, force_full)
    
    return jsonify({
        "status": "success",
        "text": text[:100] + "..." if len(text) > 100 else text,
        "result": result
    })


@analyzer_bp.route('/spam', methods=['POST'])
@requires_analyzer
def analyze_spam():
    """اندپوینت تشخیص اسپم"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({"status": "error", "message": "No text provided"}), 400
    
    text = data['text']
    force_full = data.get('force_full_analysis', False)
    
    analyzer = current_app.extensions['anthropic_analyzer']
    result = analyzer.analyze_spam(text, force_full)
    
    return jsonify({
        "status": "success",
        "text": text[:100] + "..." if len(text) > 100 else text,
        "result": result
    })


@analyzer_bp.route('/inappropriate', methods=['POST'])
@requires_analyzer
def analyze_inappropriate():
    """اندپوینت تشخیص محتوای نامناسب"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({"status": "error", "message": "No text provided"}), 400
    
    text = data['text']
    force_full = data.get('force_full_analysis', False)
    
    analyzer = current_app.extensions['anthropic_analyzer']
    result = analyzer.analyze_inappropriate_content(text, force_full)
    
    return jsonify({
        "status": "success",
        "text": text[:100] + "..." if len(text) > 100 else text,
        "result": result
    })


@analyzer_bp.route('/analyze', methods=['POST'])
@requires_analyzer
def analyze_full():
    """اندپوینت تحلیل کامل متن"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({"status": "error", "message": "No text provided"}), 400
    
    text = data['text']
    
    # استفاده از تحلیلگر ترکیبی در صورت وجود
    if 'integrated_text_analyzer' in current_app.extensions:
        analyzer = current_app.extensions['integrated_text_analyzer']
        result = analyzer.analyze_text(text, use_local_first=True)
    else:
        analyzer = current_app.extensions['anthropic_analyzer']
        result = analyzer.analyze_text_full(text)
    
    return jsonify({
        "status": "success",
        "text": text[:100] + "..." if len(text) > 100 else text,
        "result": result
    })


@analyzer_bp.route('/batch', methods=['POST'])
@requires_analyzer
def batch_analyze():
    """اندپوینت تحلیل دسته‌ای متن‌ها"""
    data = request.get_json()
    
    if not data or 'texts' not in data or not isinstance(data['texts'], list):
        return jsonify({"status": "error", "message": "Invalid or missing 'texts' array"}), 400
    
    texts = data['texts']
    analysis_type = data.get('analysis_type', 'sentiment')
    
    # محدود کردن تعداد متن‌ها برای جلوگیری از سوء استفاده
    max_texts = current_app.config.get('MAX_BATCH_TEXTS', 20)
    if len(texts) > max_texts:
        return jsonify({
            "status": "error", 
            "message": f"Too many texts. Maximum allowed is {max_texts}"
        }), 400
    
    analyzer = current_app.extensions['anthropic_analyzer']
    results = analyzer.bulk_analyze(texts, analysis_type)
    
    return jsonify({
        "status": "success",
        "count": len(results),
        "results": results
    })


@analyzer_bp.route('/report', methods=['POST'])
@requires_analyzer
def generate_report():
    """اندپوینت تولید گزارش تحلیلی"""
    data = request.get_json()
    
    if not data or 'texts' not in data or not isinstance(data['texts'], list):
        return jsonify({"status": "error", "message": "Invalid or missing 'texts' array"}), 400
    
    texts = data['texts']
    report_type = data.get('report_type', 'text')
    
    # محدود کردن تعداد متن‌ها
    max_texts = current_app.config.get('MAX_REPORT_TEXTS', 50)
    if len(texts) > max_texts:
        return jsonify({
            "status": "error", 
            "message": f"Too many texts. Maximum allowed is {max_texts}"
        }), 400
    
    # استفاده از تحلیلگر ترکیبی در صورت وجود
    if 'integrated_text_analyzer' in current_app.extensions:
        analyzer = current_app.extensions['integrated_text_analyzer']
        report = analyzer.analyze_multiple_texts(texts)
    else:
        analyzer = current_app.extensions['anthropic_analyzer']
        report = analyzer.generate_analysis_report(texts, report_type)
    
    return jsonify({
        "status": "success",
        "report": report
    })


@analyzer_bp.route('/history', methods=['GET'])
@requires_analyzer
def get_history():
    """اندپوینت دریافت تاریخچه تحلیل‌ها"""
    analyzer = current_app.extensions['anthropic_analyzer']
    
    format_type = request.args.get('format', 'json')
    limit = request.args.get('limit', type=int)
    
    # محدود کردن تاریخچه به تعداد درخواستی
    history = analyzer.analysis_history
    if limit and limit > 0:
        history = history[-limit:]
    
    if format_type == 'csv':
        csv_data = analyzer.export_analysis_history(format='csv')
        return csv_data, 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=analysis_history.csv'}
    else:
        return jsonify({
            "status": "success",
            "count": len(history),
            "history": history
        })