from .main import main_bp
from .participants import participants_bp
from .tournaments import tournaments_bp
from .users import users_bp


def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp, url_prefix="/v1")
    app.register_blueprint(tournaments_bp, url_prefix="/v1")
    app.register_blueprint(participants_bp, url_prefix="/v1")
