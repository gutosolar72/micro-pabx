# /opt/nanosip/blueprints/nanosip.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from auth import login_required
from database import get_ramais, get_filas, get_localnets, get_db
from .main import license_context, license_message


from cadastro import (
    adicionar_ramal, atualizar_ramal, remover_ramal,
    adicionar_fila, atualizar_fila, remover_fila,
    associar_ramal_fila, desassociar_todos_ramais_da_fila
)

nanosip_bp = Blueprint("nanosip", __name__, template_folder="../templates")

@nanosip_bp.route("/nanosip")
@login_required
def config_nanosip():
    ramais = get_ramais()
    filas = get_filas()
    localnets = get_localnets()
    return render_template(
        "config_nanosip.html", 
        ramais=ramais, 
        filas=filas, 
        localnets=localnets,
        LICENSE_VALID=license_context(),
        LICENSE_MSG=license_message()
        )

# --- ROTAS DE RAMAL (Lógica de Edição Final) ---
@nanosip_bp.route("/ramal", methods=["GET", "POST"])
@login_required
def cadastro_ramal():
    if request.method == "POST":
        ramal_id = request.form.get("id")
        try:
            ramal_num = int(request.form["ramal"])
            nome = request.form["nome"]
            senha = request.form["senha"]
            contexto = "interno"

            if ramal_id:
                success, msg = atualizar_ramal(ramal_id, nome, senha, contexto)
            else:
                success, msg = adicionar_ramal(ramal_num, nome, senha, contexto)

            if success: flash(msg, "success")
            else: flash(msg, "danger")
        except ValueError:
            flash("O número do ramal deve ser um valor numérico.", "danger")
        except Exception as e:
            flash(f"Erro ao processar ramal: {str(e)}", "danger")
        
        return redirect(url_for("nanosip.cadastro_ramal"))

    ramais = get_ramais()
    return render_template(
        "config_ramais.html", 
        ramais=ramais,
        LICENSE_VALID=license_context(),
        LICENSE_MSG=license_message()
        )

@nanosip_bp.route("/ramal/excluir", methods=["POST"])
@login_required
def excluir_ramal():
    ramal_id = request.form.get("id")
    if ramal_id:
        success, msg = remover_ramal(ramal_id)
        if success: flash(msg, "success")
        else: flash(msg, "danger")
    return redirect(url_for("nanosip.cadastro_ramal"))

# --- ROTAS DE FILA (Lógica de Edição Final) ---
@nanosip_bp.route("/fila", methods=["GET", "POST"])
@login_required
def cadastro_fila():
    if request.method == "POST":
        fila_id = request.form.get("id")
        try:
            fila_num = int(request.form["fila"])
            nome = request.form["nome"]
            ramais_selecionados_ids = request.form.getlist("ramais")

            if fila_id:
                # --- LÓGICA DE EDIÇÃO ---
                success, msg = atualizar_fila(fila_id, nome)
                if success:
                    desassociar_todos_ramais_da_fila(fila_id)
                    for ramal_id in ramais_selecionados_ids:
                        # CORREÇÃO: Passando o segundo argumento 'fila_id'
                        associar_ramal_fila(ramal_id, fila_id)
                    flash("Fila atualizada com sucesso!", "success")
                else:
                    flash(f"Erro ao atualizar fila: {msg}", "danger")
            else:
                # --- LÓGICA DE CRIAÇÃO ---
                success, msg = adicionar_fila(fila_num, nome)
                if success:
                    db = get_db()
                    # Garante que a gente pegue o ID da fila recém-criada
                    new_fila_id = db.execute("SELECT id FROM filas WHERE fila = ?", (fila_num,)).fetchone()['id']
                    db.close()
                    for ramal_id in ramais_selecionados_ids:
                        # CORREÇÃO: Passando o segundo argumento 'new_fila_id'
                        associar_ramal_fila(ramal_id, new_fila_id)
                    flash("Fila criada e ramais associados com sucesso!", "success")
                else:
                    flash(f"Erro ao adicionar fila: {msg}", "danger")
        except ValueError:
            flash("O número da fila deve ser um valor numérico.", "danger")
        except Exception as e:
            flash(f"Erro ao processar fila: {str(e)}", "danger")
        
        return redirect(url_for("nanosip.cadastro_fila"))

    # Para requisições GET
    ramais = get_ramais()
    filas = get_filas()
    return render_template(
        "config_filas.html",
        ramais=ramais, 
        filas=filas,
        LICENSE_VALID=license_context(),
        LICENSE_MSG=license_message()
        )

@nanosip_bp.route("/fila/excluir", methods=["POST"])
@login_required
def excluir_fila():
    fila_id = request.form.get("id")
    if fila_id:
        success, msg = remover_fila(fila_id)
        if success: flash(msg, "success")
        else: flash(msg, "danger")
    return redirect(url_for("nanosip.cadastro_fila"))


