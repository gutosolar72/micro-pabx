from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
import subprocess
from auth import login_required
from database import get_db, get_routes, get_filas
from functools import wraps
from datetime import datetime
import bcrypt
import licenca as lic  # <-- importar módulo de licença
import math
import csv

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
    if request.method == "POST":
        db = get_db()
        try:
            route_id = request.form.get("id")
            nome = request.form["nome"]
            numero_entrada = request.form["numero_entrada"]
            dest_fila_else = request.form["dest_fila_else"]

            if not route_id:
                cursor = db.execute("SELECT id FROM ramais WHERE ramal = ?", (numero_entrada,))
                if cursor.fetchone():
                    flash(f"Erro: O número {numero_entrada} já está em uso por um ramal.", "danger")
                    return redirect(url_for("rotas.config_rotas"))

                cursor = db.execute("SELECT id FROM filas WHERE fila = ?", (numero_entrada,))
                if cursor.fetchone():
                    flash(f"Erro: O número {numero_entrada} já está em uso por uma fila.", "danger")
                    return redirect(url_for("rotas.config_rotas"))

                cursor = db.execute("SELECT id FROM rotas WHERE numero_entrada = ?", (numero_entrada,))
                if cursor.fetchone():
                    flash(f"Erro: O número de entrada {numero_entrada} já está em uso por outra rota.", "danger")
                    return redirect(url_for("rotas.config_rotas"))

            if route_id:
                db.execute(
                    """UPDATE rotas SET nome = ?, numero_entrada = ?, dest_fila_else = ? WHERE id = ?""",
                    (nome, numero_entrada, dest_fila_else, route_id),
                )
                flash("Rota atualizada com sucesso!", "success")
            else:
                cursor = db.execute(
                    """INSERT INTO rotas (nome, numero_entrada, dest_fila_else) VALUES (?, ?, ?)""",
                    (nome, numero_entrada, dest_fila_else),
                )
                route_id = cursor.lastrowid
                flash("Rota criada com sucesso!", "success")

            # --- Time Conditions ---
            db.execute("DELETE FROM time_conditions WHERE rota_id = ?", (route_id,))
            time_starts = request.form.getlist("time_start[]")
            time_ends = request.form.getlist("time_end[]")
            days_list = request.form.getlist("days_hidden[]")
            dest_filas_if_time = request.form.getlist("dest_fila_if_time[]")

            for i in range(len(time_starts)):
                if time_starts[i] and time_ends[i] and days_list[i] and dest_filas_if_time[i]:
                    db.execute(
                        """INSERT INTO time_conditions (rota_id, time_start, time_end, days, dest_fila_if_time)
                           VALUES (?, ?, ?, ?, ?)""",
                        (route_id, time_starts[i], time_ends[i], days_list[i], dest_filas_if_time[i]),
                    )

            db.commit()

            try:
                subprocess.run(
                    ["sudo", "systemctl", "start", "nanosip-admin@apply_config.service"],
                    check=True,
                )
                flash("Configurações do Asterisk sendo aplicadas em segundo plano.", "info")
            except Exception as e:

                flash(f"Rota salva, mas falha ao recarregar o Asterisk: {e}", "warning")

        except Exception as e:
            flash(f"Erro ao salvar a rota: {str(e)}", "danger")
        finally:
            db.close()

        return redirect(url_for("rotas.config_rotas"))
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
    route_id = request.form.get("id")
    if route_id:
        db = get_db()
        try:
            db.execute("DELETE FROM rotas WHERE id = ?", (route_id,))
            db.commit()
            flash("Rota excluída com sucesso!", "success")
            try:
                subprocess.run(
                    ["sudo", "systemctl", "start", "nanosip-admin@apply_config.service"],
                    check=True,
                )
                flash("Configurações do Asterisk sendo aplicadas em segundo plano.", "info")
            except Exception as e:
                flash(f"Rota excluída, mas falha ao recarregar o Asterisk: {e}", "warning")
        except Exception as e:
            flash(f"Erro ao excluir a rota: {str(e)}", "danger")
        finally:
            db.close()
    else:
        flash("Nenhuma rota selecionada para exclusão.", "warning")
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
    if request.method == "POST":
        username = request.form["username"]
        senha = request.form["password"]
        role = request.form["role"]
        created_at = updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hashed = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (username, hashed, role, created_at, updated_at),
        )
        db.commit()
        db.close()
        flash("Usuário criado com sucesso!", "success")
        return redirect(url_for("rotas.listar_usuarios"))
    return render_template("criar_usuario.html", LICENSE_VALID=license_context())

@rotas_bp.route("/usuarios/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_role("admin", "gerente")
def editar_usuario(id):
    db = get_db()
    if request.method == "POST":
        username = request.form["username"]
        senha = request.form.get("password")
        role = request.form["role"]
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if senha:
            hashed = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            db.execute(
                "UPDATE users SET password_hash=?, role=?, updated_at=? WHERE id=?",
                (hashed, role, updated_at, id),
            )
        else:
            db.execute(
                "UPDATE users SET username=?, role=?, updated_at=? WHERE id=?",
                (username, role, updated_at, id),
            )
        db.commit()
        db.close()
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("rotas.listar_usuarios"))
    user = db.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()
    db.close()
    return render_template("editar_usuario.html", user=user, LICENSE_VALID=license_context())

@rotas_bp.route("/usuarios/excluir/<int:id>", methods=["POST"])
@login_required
@requires_role("admin", "gerente")
def excluir_usuario(id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (id,))
    db.commit()
    db.close()
    flash("Usuário excluído com sucesso!", "success")
    return redirect(url_for("rotas.listar_usuarios"))


@rotas_bp.route("/relatorios")
@login_required
@requires_role("admin", "gerente", "operador")
def relatorio_cdr():
    # Caminho do CSV
    csv_path = "/var/log/asterisk/cdr-csv/Master.csv"

    registros = []

    # Ler CSV
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Normaliza os nomes das colunas caso necessário
                registros.append({
                    'calldate': row.get('calldate', ''),
                    'src': row.get('src', ''),
                    'dst': row.get('dst', ''),
                    'duration': row.get('duration', ''),
                    'billsec': row.get('billsec', ''),
                    'disposition': row.get('disposition', ''),
                })
    except Exception as e:
        registros = []
        flash(f"Erro ao ler o CSV de CDR: {e}", "danger")

    # --- Paginação ---
    per_page = 20  # registros por página
    page = request.args.get('page', 1, type=int)
    total_pages = math.ceil(len(registros) / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    registros_pag = registros[start:end]

    return render_template(
        "relatorio_cdr.html",
        registros=registros_pag,
        page=page,
        total_pages=total_pages,
        LICENSE_VALID=license_context()
    )
