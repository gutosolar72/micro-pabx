# blueprints/__init__.py
from .rede import rede_bp
from .nanosip import nanosip_bp
from .auth import auth_bp # Importando o novo blueprint de autenticação

def register_blueprints(app):
    """
    Registra todos os blueprints da aplicação.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(rede_bp, url_prefix='/config')
    app.register_blueprint(nanosip_bp, url_prefix='/config')

