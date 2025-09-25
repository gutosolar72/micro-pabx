# /opt/micro-pbx/blueprints/rotas.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
import subprocess
from auth import login_required
from database import get_db  # Usaremos get_db para mais controle

rotas_bp = Blueprint("rotas", __name__, template_folder="../templates")

def get_all_rotas():
    """Busca todas as rotas para exibir na lista, já convertidas para dicionário."""
    db = get_db()
    rotas_raw = db.execute("""
        SELECT id, nome, numero_entrada, time_condition_enabled, 
               time_start, time_end, days, dest_fila_if_time, dest_fila_else 
        FROM rotas 
        ORDER BY nome
    """).fetchall()
    db.close()
    
    rotas = [dict(row) for row in rotas_raw]
    
    return rotas

def get_all_filas():
    """Busca todas as filas para preencher os menus de destino."""
    db = get_db()
    filas = db.execute("SELECT id, nome, fila FROM filas ORDER BY nome").fetchall()
    db.close()
    return filas

@rotas_bp.route("/rotas", methods=["GET", "POST"])
@login_required
def config_rotas():
    if request.method == "POST":
        # A lógica de salvar (adicionar/editar) virá aqui
        try:
            route_id = request.form.get("id")
            nome = request.form["nome"]
            numero_entrada = request.form["numero_entrada"]
            dest_fila_else = request.form["dest_fila_else"]
            
            time_condition_enabled = "time_condition_enabled" in request.form
            time_start = request.form.get("time_start")
            time_end = request.form.get("time_end")
            days = ",".join(request.form.getlist("days")) # Salva como "mon,tue,wed"
            dest_fila_if_time = request.form.get("dest_fila_if_time")

            db = get_db()
            if route_id:
                # Lógica de Edição
                db.execute("""
                    UPDATE rotas SET nome = ?, numero_entrada = ?, time_condition_enabled = ?,
                    time_start = ?, time_end = ?, days = ?, dest_fila_if_time = ?, dest_fila_else = ?
                    WHERE id = ?
                """, (nome, numero_entrada, time_condition_enabled, time_start, time_end, days, dest_fila_if_time, dest_fila_else, route_id))
                flash("Rota atualizada com sucesso!", "success")
            else:
                # Lógica de Criação

                # 1. Validação: Ramal
                cursor = db.execute("SELECT id FROM ramais WHERE ramal = ?", (numero_entrada,))
                if cursor.fetchone():
                    db.close()
                    flash(f"Erro: O número {numero_entrada} já está em uso por um ramal.", "danger")
                    return redirect(url_for("rotas.config_rotas")) # <-- INTERROMPE E REDIRECIONA

                # 2. Validação: Fila
                cursor = db.execute("SELECT id FROM filas WHERE fila = ?", (numero_entrada,))
                if cursor.fetchone():
                    db.close()
                    flash(f"Erro: O número {numero_entrada} já está em uso por uma fila.", "danger")
                    return redirect(url_for("rotas.config_rotas")) # <-- INTERROMPE E REDIRECIONA

                # 3. Validação: Outra Rota
                cursor = db.execute("SELECT id FROM rotas WHERE numero_entrada = ?", (numero_entrada,))
                if cursor.fetchone():
                    db.close()
                    flash(f"Erro: O número de entrada {numero_entrada} já está em uso por outra rota.", "danger")
                    return redirect(url_for("rotas.config_rotas")) # <-- INTERROMPE E REDIRECIONA


                db.execute("""
                    INSERT INTO rotas (nome, numero_entrada, time_condition_enabled, time_start, time_end, days, dest_fila_if_time, dest_fila_else)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (nome, numero_entrada, time_condition_enabled, time_start, time_end, days, dest_fila_if_time, dest_fila_else))
                flash("Rota criada com sucesso!", "success")
            
            db.commit()
            db.close()

            # Aciona o reload do Asterisk
            try:
                subprocess.run(["sudo", "systemctl", "start", "pabx-admin@apply_config.service"], check=True)
                flash("Configurações do Asterisk sendo aplicadas em segundo plano.", "info")
            except Exception as e:
                flash(f"Rota salva no banco, mas falha ao recarregar o Asterisk: {e}", "warning")

        except Exception as e:
            flash(f"Erro ao salvar a rota: {str(e)}", "danger")
        
        return redirect(url_for("rotas.config_rotas"))

    # Para requisições GET
    rotas = get_all_rotas()
    filas = get_all_filas()
    return render_template("config_rotas.html", rotas=rotas, filas=filas)

@rotas_bp.route("/rotas/excluir", methods=["POST"])
@login_required
def excluir_rota():
    route_id = request.form.get("id")
    if route_id:
        try:
            db = get_db()
            db.execute("DELETE FROM rotas WHERE id = ?", (route_id,))
            db.commit()
            db.close()
            flash("Rota excluída com sucesso!", "success")

            # Aciona o reload do Asterisk
            try:
                subprocess.run(["sudo", "systemctl", "start", "pabx-admin@apply_config.service"], check=True)
                flash("Configurações do Asterisk sendo aplicadas em segundo plano.", "info")
            except Exception as e:
                flash(f"Rota excluída do banco, mas falha ao recarregar o Asterisk: {e}", "warning")

        except Exception as e:
            flash(f"Erro ao excluir a rota: {str(e)}", "danger")
    else:
        flash("Nenhuma rota selecionada para exclusão.", "warning")
        
    return redirect(url_for("rotas.config_rotas"))

