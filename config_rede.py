from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from functools import wraps
import subprocess
import os
import shutil
import netifaces as ni
import socket

# -------------------------------
# Blueprint
# -------------------------------
config_rede_bp = Blueprint("config_rede", __name__, template_folder="templates", url_prefix="/config")
#config_rede_bp = Blueprint("config_rede", __name__, template_folder="templates")

INTERFACES_FILE = "/etc/network/interfaces"
RESOLVCONF_FILE = "/etc/resolv.conf"
RESOLVCONF_BKP_FILE = "/etc/resolv.conf.bak"
BACKUP_FILE = "/etc/network/interfaces.bak"


# -------------------------------
# Decorator de login (usando sessão)
# -------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------
# Funções auxiliares
# -------------------------------
def backup_interfaces():
    if os.path.exists(INTERFACES_FILE):
        shutil.copy2(INTERFACES_FILE, BACKUP_FILE)


def backup_resolvconf():
    if os.path.exists(RESOLVCONF_FILE):
        shutil.copy2(RESOLVCONF_FILE, RESOLVCONF_BKP_FILE)


def get_dns():
    dns_servers = []
    if os.path.exists(RESOLVCONF_FILE):
        with open(RESOLVCONF_FILE) as f:
            for line in f:
                if line.startswith("nameserver"):
                    dns_servers.append(line.split()[1].strip())
    return ", ".join(dns_servers)


def carrega_config():
    iface = ni.gateways()["default"][ni.AF_INET][1]
    ip_info = ni.ifaddresses(iface)[ni.AF_INET][0]
    return {
        "hostname": socket.gethostname(),
        "iface": iface,
        "ip_atual": ip_info["addr"],
        "netmask": ip_info["netmask"],
        "gateway": ni.gateways()["default"][ni.AF_INET][0],
        "dns": get_dns(),
    }


def apply_network_config(iface):
    try:
        subprocess.run(["ifdown", iface], check=True)
        subprocess.run(["ifup", iface], check=True)
        return True, "Configuração aplicada com sucesso!"
    except subprocess.CalledProcessError as e:
        return False, f"Erro ao aplicar a configuração: {e}"


# -------------------------------
# Banco de localnets
# -------------------------------
from database import get_localnets, update_localnets


# -------------------------------
# Rota principal de configuração de rede
# -------------------------------
@config_rede_bp.route("/rede", methods=["GET", "POST"])
#@config_rede_bp.route("/config/rede", methods=["GET", "POST"])
@login_required
def config_rede():
    network = carrega_config()
    localnets = get_localnets()
    mensagem = None
    erro = None

    if request.method == "POST":
        iface = request.form["iface"]
        ip = request.form["ip"]
        netmask = request.form["netmask"]
        gateway = request.form["gateway"]
        dns = request.form["dns"]

        nomes = request.form.getlist("nome[]")
        redes = request.form.getlist("localnet[]")

        # Prepara lista de dicionários
        redes_para_salvar = [
            {"nome": n.strip(), "localnet": r.strip()}
            for n, r in zip(nomes, redes) if n.strip() and r.strip()
        ]

        # Salva localnets no banco
        try:
            update_localnets(redes_para_salvar)
        except Exception as e:
            flash(f"Erro ao salvar redes locais: {str(e)}", "danger")

        # Faz backup antes de alterar arquivos de rede
        backup_interfaces()
        backup_resolvconf()

        # Monta novo arquivo interfaces
        interfaces_content = f"""# Arquivo gerado pelo Micro PABX Flask
auto lo
iface lo inet loopback

auto {iface}
iface {iface} inet static
    address {ip}
    netmask {netmask}
    gateway {gateway}
"""

        # Grava resolv.conf
        try:
            with open(RESOLVCONF_FILE, "w") as file:
                dns = dns.replace(" ", "").split(",")
                file.write("# Arquivo gerado pelo Micro PABX Flask\n")
                for ip_dns in dns:
                    if ip_dns.strip():
                        file.write(f"nameserver {ip_dns.strip()}\n")
        except PermissionError:
            erro = "Permissão negada ao gravar resolv.conf!"

        # Grava interfaces
        try:
            with open(INTERFACES_FILE, "w") as f:
                f.write(interfaces_content)
            success, message = apply_network_config(iface)
            if success:
                mensagem = message
            else:
                erro = message
        except PermissionError:
            erro = "Permissão negada! Rode o Flask como root ou ajuste as permissões."

        if mensagem:
            flash(mensagem, "success")
        if erro:
            flash(erro, "danger")

        return redirect(url_for("config_rede.config_rede"))

    return render_template(
        "config_rede.html",
        network=network,
        localnets=localnets
    )

