import pytest
from twitter_analyzer import create_app
from twitter_analyzer.models import db
from twitter_analyzer.models.user import User

@pytest.fixture
def app():
    """ایجاد و پیکربندی یک نمونه Flask برای هر تست"""
    app = create_app('testing')
    
    # ایجاد یک کانتکست برنامه
    with app.app_context():
        # ایجاد پایگاه داده و جداول
        db.create_all()
        
        # ایجاد یک کاربر نمونه برای تست
        user = User(username='test_user', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        yield app
        
        # پاک‌سازی پس از تست
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """یک کلاینت تست برای ارسال درخواست‌ها"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """یک runner برای تست دستورات CLI"""
    return app.test_cli_runner()
