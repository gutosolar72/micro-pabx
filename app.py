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
    script_path = os.path.join(os.path.dirname(__file__), 'system_manager.sh')
    try:
        # Chama o script mestre com a ação 'apply_config'
        subprocess.run(
            ["sudo", script_path, "apply_config"], 
            check=True,
            capture_output=True # Captura a saída para não poluir o log do Flask
        )
        flash("Configurações aplicadas e Asterisk recarregado com sucesso!", "success")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        flash(f"Erro ao aplicar configurações: {str(e)}", "danger")
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

