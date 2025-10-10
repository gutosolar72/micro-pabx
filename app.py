# /opt/nanosip/app.py

from flask import Flask, render_template, redirect, url_for, flash, Blueprint, request
import subprocess
from system_info import get_system_info
from database import init_db
from auth import login_required
import os

# --- Importação do Módulo de Licenciamento Protegido ---
# O módulo 'licenca' é importado. Se o arquivo licenca.py estiver presente,
# ele será carregado.
try:
    import licenca
    LICENSE_CONFIG = licenca.get_protected_config_data()
    LICENSE_VALID = LICENSE_CONFIG["status"] == "ok"
    LICENSE_MESSAGE = LICENSE_CONFIG["message"]
    BLUEPRINTS_PERMITIDOS = LICENSE_CONFIG["blueprints_permitidos"]
except ImportError:
    # Se o arquivo licenca.pyc não for encontrado, o sistema não deve funcionar.
    LICENSE_VALID = False
    LICENSE_MESSAGE = "Módulo de licenciamento (licenca.pyc) não encontrado. O sistema não pode ser iniciado."
    BLUEPRINTS_PERMITIDOS = ["main", "auth"] # Apenas o mínimo para exibir a tela de erro
except Exception as e:
    # Qualquer outro erro no módulo de licença (ex: erro de sintaxe no .pyc)
    LICENSE_VALID = False
    LICENSE_MESSAGE = f"Erro crítico no módulo de licenciamento: {str(e)}"
    BLUEPRINTS_PERMITIDOS = ["main", "auth"]

# --- Importação de TODOS os Blueprints ---
# Importamos todos, mas só registraremos os permitidos.
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.nanosip import nanosip_bp
from blueprints.rede import rede_bp
from blueprints.rotas import rotas_bp
from blueprints.relatorios import relatorios_bp

# Mapeamento de nomes de blueprints para objetos
BLUEPRINT_MAP = {
    "main": main_bp,
    "auth": auth_bp,
    "nanosip": nanosip_bp,
    "rede": rede_bp,
    "rotas": rotas_bp,
    "relatorios": relatorios_bp,
}

# -------------------------------
# App Flask
# -------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chave_super_secreta_para_desenvolvimento")

# Inicializa o banco de dados
init_db()

@app.before_request
def check_license_status():
    if not LICENSE_VALID:
        # Permite acesso apenas às rotas de login/logout e main (para exibir a mensagem)
        if request.endpoint and not any(request.endpoint.startswith(bp) for bp in ["main", "auth"]):
            flash(LICENSE_MESSAGE, "danger")
            return redirect(url_for("main.index"))

# --- Context Processor para Licença ---
@app.context_processor
def inject_license_status():
    return dict(LICENSE_VALID=LICENSE_VALID)

# ---------------------------------------------------
# Registro Centralizado de Blueprints
# ---------------------------------------------------
# Apenas registra os blueprints permitidos pelo módulo de licença.

for bp_name in BLUEPRINTS_PERMITIDOS:
    bp = BLUEPRINT_MAP.get(bp_name)
    if bp:
        if bp_name in ["nanosip", "rede", "rotas"]:
            # Blueprints de Configuração, agrupados sob /config
            app.register_blueprint(bp, url_prefix='/config')
        else:
            # Outros blueprints (main, auth, relatorios)
            app.register_blueprint(bp)


# -------------------------------
# Main (Ponto de Entrada)
# -------------------------------
if __name__ == "__main__":
    # Em um ambiente de produção real, usaríamos Gunicorn,
    # mas para desenvolvimento, o servidor do Flask é suficiente.
    app.run(host="0.0.0.0", port=5000, debug=True)


