from flask import Blueprint, render_template, request, redirect, url_for, flash
import subprocess
from auth import login_required
from database import get_db, get_routes, get_filas

rotas_bp = Blueprint("rotas", __name__, template_folder="../templates")

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

            # Validações de conflito (mantidas)
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
                # Atualizar rota existente
                db.execute(
                    """UPDATE rotas SET nome = ?, numero_entrada = ?, dest_fila_else = ? WHERE id = ?""",
                    (nome, numero_entrada, dest_fila_else, route_id),
                )
                flash("Rota atualizada com sucesso!", "success")
            else:
                # Criar nova rota
                cursor = db.execute(
                    """INSERT INTO rotas (nome, numero_entrada, dest_fila_else) VALUES (?, ?, ?)""",
                    (nome, numero_entrada, dest_fila_else),
                )
                route_id = cursor.lastrowid
                flash("Rota criada com sucesso!", "success")

            # --- Time Conditions ---
            # Remove os antigos
            db.execute("DELETE FROM time_conditions WHERE rota_id = ?", (route_id,))

            # Adiciona os novos
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

            # Reload Asterisk
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

    # --- GET ---
    rotas = get_routes(include_time_conditions=True)  # <- precisa do novo parâmetro
    filas = get_filas()
    return render_template("config_rotas.html", rotas=rotas, filas=filas)


@rotas_bp.route("/rotas/excluir", methods=["POST"])
@login_required
def excluir_rota():
    route_id = request.form.get("id")
    if route_id:
        db = get_db()
        try:
            # Exclusão em cascata remove também os time_conditions
            db.execute("DELETE FROM rotas WHERE id = ?", (route_id,))
            db.commit()
            flash("Rota excluída com sucesso!", "success")

            # Reload Asterisk
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

