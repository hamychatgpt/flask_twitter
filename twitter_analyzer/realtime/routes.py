from flask import render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from . import realtime_bp
from .stream import TwitterStream

@realtime_bp.route('/monitor')
@login_required
def monitor():
    """نمایش صفحه مانیتورینگ لحظه‌ای"""
    return render_template('realtime/monitor.html', title='مانیتورینگ لحظه‌ای')

@realtime_bp.route('/status')
@login_required
def status():
    """وضعیت ردیابی فعلی"""
    stream = current_app.extensions.get('twitter_stream')
    
    if not stream:
        return jsonify({
            'status': 'inactive',
            'message': 'سرویس ردیابی در حال حاضر فعال نیست'
        })
    
    return jsonify({
        'status': 'active' if stream.is_running else 'inactive',
        'tracking_keywords': stream.tracking_keywords,
        'message': 'ردیابی فعال است' if stream.is_running else 'ردیابی غیرفعال است'
    })

@realtime_bp.route('/start', methods=['POST'])
@login_required
def start_tracking():
    """شروع ردیابی"""
    # بررسی دسترسی ادمین
    if not current_user.is_admin:
        return jsonify({
            'status': 'error',
            'message': 'شما دسترسی لازم برای این عملیات را ندارید'
        }), 403
    
    data = request.get_json()
    keywords = data.get('keywords') if data else None
    
    # دریافت سرویس ردیابی
    if 'twitter_stream' not in current_app.extensions:
        stream = TwitterStream()
        current_app.extensions['twitter_stream'] = stream
    else:
        stream = current_app.extensions['twitter_stream']
    
    # شروع ردیابی
    if stream.start_tracking(keywords):
        return jsonify({
            'status': 'success',
            'message': f'ردیابی با کلمات کلیدی {stream.tracking_keywords} شروع شد',
            'tracking_keywords': stream.tracking_keywords
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'خطا در شروع ردیابی'
        }), 500

@realtime_bp.route('/stop', methods=['POST'])
@login_required
def stop_tracking():
    """توقف ردیابی"""
    # بررسی دسترسی ادمین
    if not current_user.is_admin:
        return jsonify({
            'status': 'error',
            'message': 'شما دسترسی لازم برای این عملیات را ندارید'
        }), 403
    
    if 'twitter_stream' in current_app.extensions:
        stream = current_app.extensions['twitter_stream']
        if stream.stop_tracking():
            return jsonify({
                'status': 'success',
                'message': 'ردیابی متوقف شد'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'خطا در توقف ردیابی'
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': 'سرویس ردیابی یافت نشد'
        }), 404