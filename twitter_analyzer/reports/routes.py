from flask import jsonify, current_app, request, abort, render_template
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
    reports_dir = os.path.join(current_app.instance_path, 'reports')
    
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

@reports_bp.route('/<report_id>')
@login_required
def get_report(report_id):
    """دریافت جزئیات یک گزارش"""
    reports_dir = os.path.join(current_app.instance_path, 'reports')
    
    # بررسی وجود فایل
    filename = f"{report_id}.json"
    if not report_id.endswith('.json'):
        filename = f"{report_id}.json"
    
    filepath = os.path.join(reports_dir, filename)
    
    if not os.path.exists(filepath):
        abort(404, description=f"Report {report_id} not found")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        return jsonify({
            'status': 'success',
            'report': report
        })
        
    except Exception as e:
        current_app.logger.error(f"Error reading report {report_id}: {e}")
        abort(500, description=f"Error reading report: {str(e)}")

@reports_bp.route('/generate', methods=['POST'])
@login_required
def generate_report():
    """تولید گزارش جدید"""
    # بررسی دسترسی ادمین
    if not current_user.is_admin:
        abort(403, description="Admin access required")
    
    data = request.get_json()
    
    if not data:
        abort(400, description="Invalid request data")
    
    period = data.get('period', 'hour')
    keywords = data.get('keywords')
    
    # بررسی اعتبار پارامترها
    valid_periods = ['minute', 'hour', 'day']
    if period not in valid_periods:
        abort(400, description=f"Invalid period. Valid values are: {', '.join(valid_periods)}")
    
    try:
        # دریافت سرویس گزارش‌گیری
        reporting_service = current_app.extensions.get('reporting_service')
        
        if not reporting_service:
            abort(503, description="Reporting service not available")
        
        # تولید گزارش
        report = reporting_service.generate_report(period, keywords)
        
        return jsonify({
            'status': 'success',
            'message': f"{period} report generated successfully",
            'report': report
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating report: {e}", exc_info=True)
        abort(500, description=f"Error generating report: {str(e)}")