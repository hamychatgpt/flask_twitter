from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for
from flask_login import current_user
from .. import db
from ..models.tweet import Tweet
from ..models.hashtag import Hashtag
from ..models.mention import Mention
from ..models.collection import Collection, CollectionRule

# ایجاد نمونه Admin با قالب پایه سفارشی
admin = Admin(name='تحلیلگر توییتر', 
              template_mode='bootstrap3', 
              base_template='admin/custom_base.html')
              
class SecureModelView(ModelView):
    """کلاس پایه برای محافظت از بخش Admin"""
    def is_accessible(self):
        return current_user.is_authenticated
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

def init_app(app):
    # ثبت مدل‌ها در Admin
    admin.add_view(SecureModelView(Tweet, db.session, name='توییت‌ها'))
    admin.add_view(SecureModelView(Hashtag, db.session, name='هشتگ‌ها'))
    admin.add_view(SecureModelView(Mention, db.session, name='منشن‌ها'))
    admin.add_view(SecureModelView(Collection, db.session, name='جمع‌آوری‌ها'))
    admin.add_view(SecureModelView(CollectionRule, db.session, name='قواعد جمع‌آوری'))
    
    # افزودن نمای سفارشی برای جمع‌آوری
    from .views import CollectorView
    admin.add_view(CollectorView(name='جمع‌آوری جدید'))
    
    admin.init_app(app)