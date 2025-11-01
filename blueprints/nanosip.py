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

# ----------------------------
# Tela principal do NANO SIP
# ----------------------------
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

# ----------------------------
# Cadastro / edição de ramais
# ----------------------------
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

            flash(msg, "success" if success else "danger")
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
        try:
            success, msg = remover_ramal(ramal_id)
            flash(msg, "success" if success else "danger")
        except Exception as e:
            flash(f"Erro ao remover ramal: {str(e)}", "danger")
    else:
        flash("Nenhum ramal selecionado para exclusão.", "warning")
    return redirect(url_for("nanosip.cadastro_ramal"))

# ----------------------------
# Cadastro / edição de filas
# ----------------------------
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
                # Edição de fila existente
                success, msg = atualizar_fila(fila_id, nome)
                if success:
                    desassociar_todos_ramais_da_fila(fila_id)
                    for ramal_id in ramais_selecionados_ids:
                        associar_ramal_fila(ramal_id, fila_id)
                    flash("Fila atualizada com sucesso!", "success")
                else:
                    flash(f"Erro ao atualizar fila: {msg}", "danger")
            else:
                # Criação de nova fila
                success, msg = adicionar_fila(fila_num, nome)
                if success:
                    db = get_db()
                    fila_row = db.execute("SELECT id FROM filas WHERE fila = ?", (fila_num,)).fetchone()
                    db.close()
                    if fila_row:
                        new_fila_id = fila_row['id']
                        for ramal_id in ramais_selecionados_ids:
                            associar_ramal_fila(ramal_id, new_fila_id)
                        flash("Fila criada e ramais associados com sucesso!", "success")
                    else:
                        flash("Fila criada, mas não foi possível recuperar o ID para associar ramais.", "warning")
                else:
                    flash(f"Erro ao adicionar fila: {msg}", "danger")

        except ValueError:
            flash("O número da fila deve ser um valor numérico.", "danger")
        except Exception as e:
            flash(f"Erro ao processar fila: {str(e)}", "danger")

        return redirect(url_for("nanosip.cadastro_fila"))

    # GET
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
        try:
            success, msg = remover_fila(fila_id)
            flash(msg, "success" if success else "danger")
        except Exception as e:
            flash(f"Erro ao remover fila: {str(e)}", "danger")
    else:
        flash("Nenhuma fila selecionada para exclusão.", "warning")
    return redirect(url_for("nanosip.cadastro_fila"))

