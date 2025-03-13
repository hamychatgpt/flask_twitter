from flask import Blueprint

collector_bp = Blueprint('collector', __name__, url_prefix='/collector')

from . import routes