from flask import jsonify, current_app, request, abort, render_template, make_response
from flask_login import login_required, current_user
from . import reports_bp
from datetime import datetime, timedelta
import os
import json

@reports_bp.route('/')
@login_required
def index():
    """صفحه اصلی گزارش‌ها"""
    return render_template('reports/index.html', title='گزارش‌ها')

@reports_bp.route('/summary')
@login_required
def get_summary():
    """دریافت خلاصه گزارش‌ها"""
    try:
        reports_dir = os.path.join(current_app.instance_path, 'reports')
        
        # ایجاد دایرکتوری reports اگر وجود نداشته باشد
        os.makedirs(reports_dir, exist_ok=True)
        
        if not os.path.exists(reports_dir):
            return jsonify({
                'status': 'success',
                'message': 'No reports found',
                'reports': []
            })
        
        # جمع‌آوری اطلاعات تمام گزارش‌ها
        reports = []
        for filename in os.listdir(reports_dir):
            if filename.endswith('.json') and filename.startswith('report_'):
                try:
                    filepath = os.path.join(reports_dir, filename)
                    
                    # استخراج بازه زمانی و تاریخ از نام فایل
                    parts = filename.replace('.json', '').split('_')
                    period = parts[1]
                    date_str = '_'.join(parts[2:])
                    
                    # تبدیل رشته تاریخ به شیء datetime
                    try:
                        created_at = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                    except:
                        created_at = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    # خواندن بخشی از فایل برای دریافت اطلاعات پایه
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    reports.append({
                        'id': filename.replace('.json', ''),
                        'filename': filename,
                        'period': period,
                        'period_name': data.get('period_name', period),
                        'created_at': created_at.isoformat(),
                        'start_time': data.get('start_time'),
                        'end_time': data.get('end_time'),
                        'total_tweets': data.get('stats', {}).get('total_tweets', 0),
                        'keywords': data.get('keywords', [])
                    })
                    
                except Exception as e:
                    current_app.logger.error(f"Error reading report {filename}: {e}")
        
        # مرتب‌سازی براساس تاریخ (جدیدترین اول)
        reports.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'count': len(reports),
            'reports': reports
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_summary: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"An error occurred: {str(e)}",
            'reports': []
        }), 500

@reports_bp.route('/<report_id>')
@login_required
def get_report(report_id):
    """دریافت جزئیات یک گزارش"""
    try:
        reports_dir = os.path.join(current_app.instance_path, 'reports')
        
        # بررسی وجود فایل
        filename = f"{report_id}.json"
        if not report_id.endswith('.json'):
            filename = f"{report_id}.json"
        
        filepath = os.path.join(reports_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'status': 'error',
                'message': f"Report {report_id} not found"
            }), 404
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            return jsonify({
                'status': 'success',
                'report': report
            })
            
        except Exception as e:
            current_app.logger.error(f"Error reading report {report_id}: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': f"Error reading report: {str(e)}"
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error in get_report: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"An error occurred: {str(e)}"
        }), 500

@reports_bp.route('/generate', methods=['POST'])
@login_required
def generate_report():
    """تولید گزارش جدید"""
    # در حالت عادی، فقط ادمین‌ها می‌توانند گزارش تولید کنند
    # برای دسترسی عمومی، این بخش را حذف یا تغییر دهید
    if not current_user.is_admin:
        return jsonify({
            'status': 'error',
            'message': "شما دسترسی کافی برای تولید گزارش را ندارید"
        }), 403
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': "داده‌های درخواست نامعتبر هستند"
            }), 400
        
        period = data.get('period', 'hour')
        keywords = data.get('keywords')
        
        # بررسی اعتبار پارامترها
        valid_periods = ['minute', 'hour', 'day']
        if period not in valid_periods:
            return jsonify({
                'status': 'error',
                'message': f"دوره زمانی نامعتبر است. مقادیر معتبر عبارتند از: {', '.join(valid_periods)}"
            }), 400
        
        try:
            # دریافت سرویس گزارش‌گیری
            reporting_service = current_app.extensions.get('reporting_service')
            
            if not reporting_service:
                return jsonify({
                    'status': 'error',
                    'message': "سرویس گزارش‌گیری در دسترس نیست"
                }), 503
            
            # تولید گزارش
            report = reporting_service.generate_report(period, keywords)
            
            return jsonify({
                'status': 'success',
                'message': f"گزارش {period} با موفقیت ایجاد شد",
                'report': report
            })
            
        except Exception as e:
            current_app.logger.error(f"Error generating report: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': f"خطا در تولید گزارش: {str(e)}"
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error in generate_report: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"یک خطای غیرمنتظره رخ داد: {str(e)}"
        }), 500

@reports_bp.route('/download/<report_id>')
@login_required
def download_report(report_id):
    """دانلود یک گزارش"""
    try:
        reports_dir = os.path.join(current_app.instance_path, 'reports')
        
        # بررسی وجود فایل
        filename = f"{report_id}.json"
        if not report_id.endswith('.json'):
            filename = f"{report_id}.json"
        
        filepath = os.path.join(reports_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'status': 'error',
                'message': f"Report {report_id} not found"
            }), 404
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # ایجاد پاسخ JSON برای دانلود
            response = make_response(json.dumps(report_data, ensure_ascii=False, indent=2))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            current_app.logger.error(f"Error downloading report {report_id}: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': f"Error reading report: {str(e)}"
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error in download_report: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"An error occurred: {str(e)}"
        }), 500