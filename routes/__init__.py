from .decklist_images import decklist_images_bp
from .decklists import decklists_bp
from .main import main_bp


def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(decklists_bp, url_prefix="/v1")
    app.register_blueprint(decklist_images_bp, url_prefix="/v1")
