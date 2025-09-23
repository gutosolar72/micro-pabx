# blueprints/pabx.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from auth import login_required
from database import get_ramais, get_filas, get_localnets
from cadastro import (
    adicionar_ramal, remover_ramal,
    adicionar_fila, remover_fila, associar_ramal_fila
)

pabx_bp = Blueprint("pabx", __name__, template_folder="../templates")

@pabx_bp.route("/pabx")
@login_required
def config_pabx():
    ramais = get_ramais()
    filas = get_filas()
    localnets = get_localnets()
    return render_template("config_pabx.html", ramais=ramais, filas=filas, localnets=localnets)

@pabx_bp.route("/ramal", methods=["GET", "POST"])
@login_required
def cadastro_ramal():
    ramal_data = {"ramal": "", "nome": "", "senha": "", "contexto": "portaria"}

    if request.method == "POST":
        try:
            ramal_num = int(request.form["ramal"])
            nome = request.form["nome"]
            senha = request.form["senha"]
            contexto = request.form["contexto"]

            success, msg = adicionar_ramal(ramal_num, nome, senha, contexto)
            if success:
                flash(msg, "success")
                ramal_data = {"ramal": "", "nome": "", "senha": "", "contexto": "portaria"}
            else:
                flash(msg, "danger")
                ramal_data = {"ramal": ramal_num, "nome": nome, "senha": senha, "contexto": contexto}
        except ValueError:
            flash("O número do ramal deve ser um valor numérico.", "danger")
        except Exception as e:
            flash(f"Erro ao cadastrar ramal: {str(e)}", "danger")

    ramais = get_ramais()
    return render_template("cadastro_ramal.html", ramais=ramais, ramal=ramal_data)

@pabx_bp.route("/ramal/excluir", methods=["POST"])
@login_required
def excluir_ramal():
    ramal_num = request.form.get("ramal")
    if ramal_num:
        try:
            success, msg = remover_ramal(int(ramal_num))
            if success:
                flash(msg, "success")
            else:
                flash(msg, "danger")
        except ValueError:
            flash("Número de ramal inválido.", "danger")
        except Exception as e:
            flash(f"Erro ao excluir ramal: {str(e)}", "danger")
    else:
        flash("Nenhum ramal selecionado para exclusão.", "warning")
    return redirect(url_for("pabx.cadastro_ramal"))

@pabx_bp.route("/fila", methods=["GET", "POST"])
@login_required
def cadastro_fila():
    if request.method == "POST":
        try:
            fila_num = int(request.form["fila"])
            nome = request.form["nome"]
            ramais_selecionados = request.form.getlist("ramais")

            success, msg = adicionar_fila(fila_num, nome)
            if not success:
                flash(f"Erro ao adicionar fila: {msg}", "danger")
            else:
                for r in ramais_selecionados:
                    associar_ramal_fila(int(r), fila_num)
                flash("Fila criada e ramais associados com sucesso!", "success")
        except ValueError:
            flash("O número da fila deve ser um valor numérico.", "danger")
        except Exception as e:
            flash(f"Erro ao criar fila: {str(e)}", "danger")
        return redirect(url_for("pabx.cadastro_fila"))

    ramais = get_ramais()
    filas = get_filas()
    return render_template("cadastro_fila.html", ramais=ramais, filas=filas)

@pabx_bp.route("/fila/excluir", methods=["POST"])
@login_required
def excluir_fila():
    fila_num = request.form.get("fila")
    if fila_num:
        try:
            success, msg = remover_fila(int(fila_num))
            if success:
                flash(msg, "success")
            else:
                flash(msg, "danger")
        except ValueError:
            flash("Número de fila inválido.", "danger")
        except Exception as e:
            flash(f"Erro ao excluir fila: {str(e)}", "danger")
    else:
        flash("Nenhuma fila selecionada para exclusão.", "warning")
    return redirect(url_for("pabx.cadastro_fila"))

