from flask import Flask, render_template, session, redirect, url_for, request, flash
from functools import wraps
import subprocess

from system_info import get_system_info
from database import get_ramais, get_filas, init_db, get_localnets
from cadastro import (
    adicionar_ramal, atualizar_ramal, remover_ramal,
    adicionar_fila, atualizar_fila, remover_fila, associar_ramal_fila
)
from config_rede import config_rede_bp

# -------------------------------
# App Flask
# -------------------------------
app = Flask(__name__)
app.secret_key = "chave_super_secreta"

# Inicializa o banco
init_db()

# -------------------------------
# Decorator de login
# -------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------
# Registro de Blueprints
# -------------------------------
app.register_blueprint(config_rede_bp)

# -------------------------------
# Rota inicial
# -------------------------------
@app.route("/")
def index():
    info = get_system_info()
    user = session.get("user")
    return render_template("index.html", info=info, user=user)

#--------------------------------
# Configuração de Rede
#--------------------------------
@app.route("/config/rede", methods=["GET", "POST"])
def config_rede():

    if not session.get("user"):
        return redirect(url_for("login"))

#    if request.method == "POST":
#        ip = request.form.get("ip")
#        netmask = request.form.get("netmask")
#        gateway = request.form.get("gateway")
#        dns = request.form.get("dns")
#        hostname = request.form.get("hostname")
#        print(f"Valores enviados: {ip}, {netmask}, {gateway}, {dns}, {hostname}")
#        return redirect(url_for("config_rede"))
#
    network_info = get_system_info()
    return render_template("config_rede.html", network=network_info)


# -------------------------------
# Configuração PABX
# -------------------------------
@app.route("/config/pabx")
@login_required
def config_pabx():
    ramais = get_ramais()
    filas = get_filas()
    localnets = get_localnets()
    return render_template("config_pabx.html", ramais=ramais, filas=filas, localnets=localnets)

# -------------------------------
# Cadastro de Ramal
# -------------------------------
@app.route("/cadastro/ramal", methods=["GET", "POST"])
@login_required
def cadastro_ramal():
    ramais = get_ramais()
    mensagem = None
    erro = None
    ramal = {"ramal": "", "nome": "", "senha": "", "contexto": "portaria"}

    if request.method == "POST":
        try:
            ramal_num = int(request.form.get("ramal"))
            nome = request.form.get("nome")
            senha = request.form.get("senha")
            contexto = request.form.get("contexto")

            success, msg = adicionar_ramal(ramal_num, nome, senha, contexto)
            if success:
                mensagem = msg
                ramal = {"ramal": ramal_num, "nome": nome, "senha": senha, "contexto": contexto or "portaria"}
            else:
                erro = msg
        except Exception as e:
            erro = str(e)

        ramais = get_ramais()

    return render_template("cadastro_ramal.html", ramais=ramais, ramal=ramal, mensagem=mensagem, erro=erro)

@app.route("/cadastro/ramal/excluir", methods=["POST"])
@login_required
def excluir_ramal():
    ramal = {"ramal": "", "nome": "", "senha": "", "contexto": "portaria"}
    ramal_num = request.form.get("ramal")
    mensagem = erro = None

    if ramal_num:
        try:
            ramal_num = int(ramal_num)
            success, msg = remover_ramal(ramal_num)
            if success:
                mensagem = msg
            else:
                erro = msg
        except Exception as e:
            erro = str(e)
    else:
        erro = "Ramal inválido"

    ramais = get_ramais()
    return render_template("cadastro_ramal.html", ramais=ramais, ramal=ramal, mensagem=mensagem, erro=erro)

# -------------------------------
# Cadastro de Fila
# -------------------------------
@app.route("/cadastro/fila", methods=["GET", "POST"])
@login_required
def cadastro_fila():
    ramais = get_ramais()
    filas = get_filas()
    mensagem = erro = None

    if request.method == "POST":
        try:
            fila_num = int(request.form.get("fila"))
            nome = request.form.get("nome")
            ramais_selecionados = request.form.getlist("ramais")

            success, msg = adicionar_fila(fila_num, nome)
            if not success:
                erro = f"Erro ao adicionar fila: {msg}"
            else:
                for r in ramais_selecionados:
                    associar_ramal_fila(int(r), fila_num)
                mensagem = "Fila criada com sucesso!"
        except Exception as e:
            erro = str(e)

        filas = get_filas()

    return render_template("cadastro_fila.html", ramais=ramais, filas=filas, mensagem=mensagem, erro=erro)

@app.route("/cadastro/fila/excluir", methods=["POST"])
@login_required
def excluir_fila():
    fila_num = request.form.get("fila")
    mensagem = erro = None

    if fila_num:
        try:
            fila_num = int(fila_num)
            success, msg = remover_fila(fila_num)
            if success:
                mensagem = msg
            else:
                erro = msg
        except Exception as e:
            erro = str(e)
    else:
        erro = "Número de fila inválido"

    filas = get_filas()
    ramais = get_ramais()
    return render_template("cadastro_fila.html", filas=filas, ramais=ramais, mensagem=mensagem, erro=erro)

# -------------------------------
# Login / Logout
# -------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "123mudar@":
            session["user"] = "admin"
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Usuário ou senha inválidos")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

# -------------------------------
# Reload configurações
# -------------------------------
@app.route("/reload", methods=["POST"])
def reload():
    try:
        subprocess.run(["python3", "reload.py"], check=True)
        flash("Configurações aplicadas com sucesso!", "success")
    except subprocess.CalledProcessError:
        flash("Erro ao aplicar configurações!", "danger")
    return redirect(url_for("index"))

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

