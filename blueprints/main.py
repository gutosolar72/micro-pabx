# /opt/micro-pbx/blueprints/main.py

from flask import Blueprint, render_template, redirect, url_for, flash
import subprocess
from system_info import get_system_info
from auth import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    info = get_system_info()
    return render_template("index.html", info=info)

@main_bp.route("/reload", methods=["POST"])
@login_required
def reload():
    try:
        # Usando o serviço systemd para aplicar as configurações como root
        subprocess.run(["sudo", "systemctl", "start", "pabx-admin@apply_config.service"], check=True)
        flash("Tarefa de aplicar configurações iniciada com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao iniciar tarefa de reload: {str(e)}", "danger")
    return redirect(url_for("main.index"))

