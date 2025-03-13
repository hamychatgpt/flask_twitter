from twitter_analyzer import create_app

def test_config():
    """تست پیکربندی برنامه"""
    assert create_app('testing').testing
    assert not create_app('development').testing

def test_hello(client):
    """تست مسیر سلام"""
    response = client.get('/hello')
    assert response.data.decode('utf-8') == 'سلام، تحلیلگر توییتر!'
