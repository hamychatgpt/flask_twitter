from flask import Blueprint

analyzer_bp = Blueprint('analyzer', __name__, url_prefix='/api/analyzer')

from . import routes