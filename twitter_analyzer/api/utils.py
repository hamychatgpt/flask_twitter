from flask import jsonify, current_app
from functools import wraps
from ..twitter.twitter_api import TwitterAPI

def api_response(data=None, status="success", message=None, code=200):
    """
    ایجاد پاسخ استاندارد API
    """
    response = {
        "status": status
    }
    
    if data is not None:
        response["data"] = data
        
    if message:
        response["message"] = message
        
    return jsonify(response), code

def handle_api_error(f):
    """
    دکوراتور مدیریت خطای API
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"API Error: {str(e)}", exc_info=True)
            return api_response(status="error", message=str(e), code=500)
    return decorated_function

def get_twitter_api_stats():
    """
    دریافت آمار TwitterAPI
    """
    twitter_api = current_app.extensions.get('twitter_api')
    
    if not twitter_api:
        return {
            "status": "error",
            "message": "TwitterAPI not initialized"
        }
    
    stats = {
        "rate_limit": twitter_api.get_rate_limit_stats(),
        "cache": {
            "type": current_app.config.get('CACHE_TYPE'),
            "ttl": current_app.config.get('TWITTER_CACHE_TTL'),
        }
    }
    
    return stats