# app.py
from flask import Flask, render_template, redirect, url_for, flash, Blueprint
import subprocess
from system_info import get_system_info
from database import init_db
from auth import login_required
from blueprints import register_blueprints
import os

# -------------------------------
# App Flask
# -------------------------------
app = Flask(__name__)
app.secret_key = "chave_super_secreta"

# Inicializa o banco de dados
init_db()

# -------------------------------
# Blueprint Principal
# -------------------------------
main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    info = get_system_info()
    return render_template("index.html", info=info)


@main_bp.route("/reload", methods=["POST"])
@login_required
def reload():
    try:
        subprocess.run(["sudo", "systemctl", "start", "pabx-admin@apply_config.service"], check=True)
        flash("Tarefa de aplicar configurações iniciada com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao iniciar tarefa de reload: {str(e)}", "danger")
    return redirect(url_for("main.index"))
# Registra o blueprint principal
app.register_blueprint(main_bp)

# -------------------------------
# Registro de Blueprints
# -------------------------------
register_blueprints(app)

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

