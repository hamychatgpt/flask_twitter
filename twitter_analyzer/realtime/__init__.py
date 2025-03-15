from flask import Blueprint

realtime_bp = Blueprint('realtime', __name__, url_prefix='/realtime')

from . import routes