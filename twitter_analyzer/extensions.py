from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_apscheduler import APScheduler

# ایجاد نمونه Marshmallow
ma = Marshmallow()


migrate = Migrate()
bootstrap = Bootstrap()
scheduler = APScheduler()