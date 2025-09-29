# /opt/nanosip/app.py

from flask import Flask, render_template, redirect, url_for, flash, Blueprint
import subprocess
from system_info import get_system_info
from database import init_db
from auth import login_required
import os

# --- Importação de TODOS os Blueprints ---
# Centralizamos todas as importações de blueprints aqui.
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.pabx import pabx_bp
from blueprints.rede import rede_bp
from blueprints.rotas import rotas_bp

# -------------------------------
# App Flask
# -------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chave_super_secreta_para_desenvolvimento")

# Inicializa o banco de dados
init_db()

# ---------------------------------------------------
# Registro Centralizado de Blueprints
# ---------------------------------------------------
# Todo o registro acontece em um único lugar, com seus prefixos.
# Isso torna a estrutura de URLs do site explícita e clara.

app.register_blueprint(main_bp)  # Rota principal, sem prefixo
app.register_blueprint(auth_bp)  # Rotas de login/logout, sem prefixo

# Blueprints de Configuração, todos agrupados sob /config
app.register_blueprint(pabx_bp, url_prefix='/config')
app.register_blueprint(rede_bp, url_prefix='/config')
app.register_blueprint(rotas_bp, url_prefix='/config')

# -------------------------------
# Main (Ponto de Entrada)
# -------------------------------
if __name__ == "__main__":
    # Em um ambiente de produção real, usaríamos Gunicorn,
    # mas para desenvolvimento, o servidor do Flask é suficiente.
    app.run(host="0.0.0.0", port=5000, debug=True)


