from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_apscheduler import APScheduler
from flask_caching import Cache

# ایجاد نمونه Marshmallow
ma = Marshmallow()

# ایجاد نمونه‌های دیگر
migrate = Migrate()
bootstrap = Bootstrap()
scheduler = APScheduler()

# نمونه کش برای استفاده در برنامه
cache = Cache()