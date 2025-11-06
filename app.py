from flask import Flask, render_template, redirect, url_for, request, session
from database import init_db
import os
import licenca

# ----- Importa Blueprints -----
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.nanosip import nanosip_bp
from blueprints.rede import rede_bp
from blueprints.rotas import rotas_bp
from blueprints.relatorios import relatorios_bp
from blueprints.painelweb import painelweb_bp


# ========================================================
# 🧱 Inicialização do App Flask
# ========================================================

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chave_super_secreta_para_desenvolvimento")


# ========================================================
# ⚙️ Registro dos Blueprints
# ========================================================

BLUEPRINT_MAP = {
    "main": main_bp,
    "auth": auth_bp,
    "nanosip": nanosip_bp,
    "rede": rede_bp,
    "rotas": rotas_bp,
    "relatorios": relatorios_bp,
    "painelweb": painelweb_bp
}

for bp_name, bp in BLUEPRINT_MAP.items():
    if bp_name in ["nanosip", "rede", "rotas"]:
        app.register_blueprint(bp, url_prefix="/config")
    else:
        app.register_blueprint(bp)


# ========================================================
# 🔐 Contexto Global (para uso no template base.html)
# ========================================================
# Aqui não há flash. Apenas disponibilizamos os dados
# atuais de licença (validação e mensagem).

@app.context_processor
def inject_license_status():
    lic_info = licenca.validate_license()
    return dict(
        LICENSE_VALID=lic_info["valid"],
        LICENSE_MSG=lic_info["message"]
    )


# ========================================================
# 🗄️ Inicialização do Banco de Dados
# ========================================================

def initialize_database():
    db_path = "/opt/nanosip/nanosip.db"
    if not os.path.exists(db_path):
        print("📀 Banco de dados não encontrado. Criando...")
        with app.app_context():
            init_db()
        print("✅ Banco criado com sucesso.")
    else:
        print("📂 Banco já existe. Pulando criação.")


# ========================================================
# 🚀 Execução Principal
# ========================================================

if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=80, debug=True)

