from .decklists import decklists_bp
from .main import main_bp


def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(decklists_bp, url_prefix="/v1")
