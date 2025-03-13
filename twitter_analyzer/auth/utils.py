from flask_login import LoginManager
from twitter_analyzer.models.user import User

# تنظیم مدیریت ورود به سیستم
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'لطفاً برای دسترسی به این صفحه وارد شوید.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """بارگذاری کاربر از طریق شناسه"""
    return User.query.get(int(user_id))
