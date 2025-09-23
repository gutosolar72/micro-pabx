# /opt/micro-pbx/blueprints/rede.py

from flask import Blueprint, request, render_template, redirect, url_for, flash
import subprocess
import os
import socket
import json # <--- Adicionado
from database import get_localnets, update_localnets
from auth import login_required

rede_bp = Blueprint("rede", __name__, template_folder="../templates")

def get_dns_servers():
    """Lê os servidores DNS do /etc/resolv.conf."""
    dns_servers = []
    try:
        with open("/etc/resolv.conf") as f:
            for line in f:
                if line.strip().startswith("nameserver"):
                    dns_servers.append(line.split()[1].strip())
    except FileNotFoundError:
        print("Aviso: /etc/resolv.conf não encontrado.")
    return ", ".join(dns_servers)

def carrega_config_atual():
    """
    Carrega as configurações de rede chamando o script mestre com sudo.
    """
    network_info = {
        "hostname": socket.gethostname(),
        "iface": "eth0",
        "ip_atual": "0.0.0.0",
        "netmask": "0.0.0.0",
        "gateway": "0.0.0.0",
        "dns": get_dns_servers() or "8.8.8.8",
    }
    
    script_path = "/opt/micro-pbx/system_manager.sh"
    try:
        result = subprocess.run(
            ["sudo", script_path, "get_network_info"],
            check=True,
            capture_output=True,
            text=True
        )
        # O stdout pode conter echos, então pegamos apenas a linha JSON
        json_line = [line for line in result.stdout.splitlines() if line.startswith('{')][0]
        data_from_script = json.loads(json_line)
        
        network_info.update({k: v for k, v in data_from_script.items() if v is not None})

    except Exception as e:
        flash(f"Não foi possível detectar as configurações de rede. Carregando valores padrão.", "warning")
    
    return network_info

@rede_bp.route("/rede", methods=["GET", "POST"])
@login_required
def config_rede():
    if request.method == "POST":
        try:
            iface = request.form["iface"]
            ip = request.form["ip"]
            netmask = request.form["netmask"]
            gateway = request.form["gateway"]
            dns = request.form["dns"]

            update_localnets([
                {"nome": n.strip(), "localnet": r.strip()}
                for n, r in zip(request.form.getlist("nome[]"), request.form.getlist("localnet[]"))
                if n.strip() and r.strip()
            ])

            interfaces_content = f"""# Arquivo gerado pelo Micro PABX Flask
auto lo
iface lo inet loopback

auto {iface}
iface {iface} inet static
    address {ip}
    netmask {netmask}
    gateway {gateway}
"""
            
            dns_list = dns.replace(" ", "").split(",")
            resolv_lines = ["# Arquivo gerado pelo Micro PABX Flask"]
            resolv_lines.extend([f"nameserver {ip_dns.strip()}" for ip_dns in dns_list if ip_dns.strip()])
            resolv_content = "\n".join(resolv_lines)

            script_path = "/opt/micro-pbx/system_manager.sh"
            subprocess.run([
                "sudo", script_path, "update_network_config",
                interfaces_content, resolv_content, iface
            ], check=True)
            
            flash("Configuração de rede aplicada com sucesso!", "success")

        except Exception as e:
            flash(f"Erro ao aplicar configuração de rede: {str(e)}", "danger")
            
        return redirect(url_for("rede.config_rede"))

    network = carrega_config_atual()
    localnets = get_localnets()
    return render_template("config_rede.html", network=network, localnets=localnets)

