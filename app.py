from flask import Flask, render_template, redirect, url_for, flash, request
from database import init_db
import os

from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.nanosip import nanosip_bp
from blueprints.rede import rede_bp
from blueprints.rotas import rotas_bp
from blueprints.relatorios import relatorios_bp

import licenca

# ----- App Flask

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chave_super_secreta_para_desenvolvimento")

# ----- Licença

LICENSE_CONFIG = licenca.get_protected_config_data()
LICENSE_VALID = LICENSE_CONFIG["status"] == "ok"
LICENSE_MESSAGE = LICENSE_CONFIG["message"]

# ----- Registro de blueprints permitidos

BLUEPRINT_MAP = {
    "main": main_bp,
    "auth": auth_bp,
    "nanosip": nanosip_bp,
    "rede": rede_bp,
    "relatorios": relatorios_bp,
    "rotas": rotas_bp
}

for bp_name, bp in BLUEPRINT_MAP.items():
    if bp_name in ["nanosip", "rede", "rotas"]:
        app.register_blueprint(bp, url_prefix='/config')
    else:
        app.register_blueprint(bp)


# ----- Context processor para base.html

@app.context_processor
def inject_license_status():
    return dict(LICENSE_VALID=LICENSE_VALID, LICENSE_MSG=LICENSE_MESSAGE)

# ---- Before request (checa licença)

@app.before_request
def check_license_status():
    if not LICENSE_VALID:
        flash(LICENSE_MESSAGE, "danger")

def initialize_database():
    db_path = "/opt/nanosip/nanosip.db"  # ajuste conforme seu caminho real
    if not os.path.exists(db_path):
        print("📀 Banco de dados não encontrado. Criando...")
        with app.app_context():
            init_db()
        print("✅ Banco criado com sucesso.")
    else:
        print("📂 Banco já existe. Pulando criação.")

# ---- Inicialização do app

if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
