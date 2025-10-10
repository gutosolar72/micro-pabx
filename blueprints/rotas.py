from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
import subprocess
from auth import login_required
from database import get_db, get_routes, get_filas
from functools import wraps
from datetime import datetime
import bcrypt
import licenca as lic  # <-- importar módulo de licença

rotas_bp = Blueprint("rotas", __name__, template_folder="../templates")

def license_context():
    status, _ = lic.get_license_status()
    return status == "ativo"

# --- Decorador de permissões ---
def requires_role(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            if session.get('role') not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator

# --- Rotas de Configuração de Rotas existentes ---
@rotas_bp.route("/rotas", methods=["GET", "POST"])
@login_required
def config_rotas():
    # ... lógica de POST permanece igual
    rotas = get_routes(include_time_conditions=True)
    filas = get_filas()
    return render_template(
        "config_rotas.html",
        rotas=rotas,
        filas=filas,
        LICENSE_VALID=license_context()
    )

@rotas_bp.route("/rotas/excluir", methods=["POST"])
@login_required
def excluir_rota():
    # ... lógica permanece igual
    return redirect(url_for("rotas.config_rotas"))

# --- Rotas de Gerenciamento de Usuários ---
@rotas_bp.route("/usuarios")
@login_required
@requires_role("admin", "gerente")
def listar_usuarios():
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    db.close()
    return render_template("usuarios.html", users=users, LICENSE_VALID=license_context())

@rotas_bp.route("/usuarios/criar", methods=["GET", "POST"])
@login_required
@requires_role("admin", "gerente")
def criar_usuario():
    # ... POST permanece igual
    return render_template("criar_usuario.html", LICENSE_VALID=license_context())

@rotas_bp.route("/usuarios/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_role("admin", "gerente")
def editar_usuario(id):
    # ... POST permanece igual
    user = db.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()
    db.close()
    return render_template("editar_usuario.html", user=user, LICENSE_VALID=license_context())

@rotas_bp.route("/relatorios")
@login_required
@requires_role("admin", "gerente", "operador")
def relatorios():
    return render_template("relatorios.html", LICENSE_VALID=license_context())

