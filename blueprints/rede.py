# /opt/nanosip/blueprints/rede.py

from flask import Blueprint, request, render_template, redirect, url_for, flash
import subprocess
import os
import socket
import json
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
        pass  # Se o arquivo não existir, retorna uma lista vazia
    return ", ".join(dns_servers)

def carrega_config_atual():
    """
    Carrega as configurações de rede iniciando um serviço systemd que executa
    o script get_network_info.py como root.
    """
    network_info = {
        "hostname": socket.gethostname(),
        "iface": "N/A",
        "ip_atual": "N/A",
        "netmask": "N/A",
        "gateway": "N/A",
        "dns": get_dns_servers() or "Não definido",
    }
    try:
        service_name = "nanosip-admin@get_network_info.service"
        # Inicia o serviço oneshot para obter as informações
        subprocess.run(["sudo", "systemctl", "start", service_name], check=True)
        
        # A saída do script estará no log do sistema (journal). Precisamos lê-la de lá.
        # O comando busca a última entrada de log para este serviço.
        log_output = subprocess.check_output(
            ["journalctl", "-u", service_name, "--since", "10 seconds ago", "-o", "cat"],
            text=True, stderr=subprocess.DEVNULL
        )
        
        # A saída do journalctl pode conter mais do que apenas o JSON.
        # Encontramos a última linha que contém o JSON.
        json_line = [line for line in log_output.splitlines() if line.strip().startswith('{')][-1]
        data_from_script = json.loads(json_line)
        
        network_info.update({k: v for k, v in data_from_script.items() if v is not None})

    except Exception as e:
        flash(f"Não foi possível detectar as configurações de rede via serviço. Erro: {str(e)}", "warning")
    
    return network_info

@rede_bp.route("/rede", methods=["GET", "POST"])
@login_required
def config_rede():
    if request.method == "POST":
        try:
            # 1. Coleta os dados do formulário
            hostname = request.form["hostname"]
            iface = request.form["iface"]
            ip = request.form["ip"]
            netmask = request.form["netmask"]
            gateway = request.form["gateway"]
            dns = request.form["dns"]

            # 2. Salva as redes locais no banco de dados
            nomes = request.form.getlist("nome[]")
            redes = request.form.getlist("localnet[]")
            if nomes and redes:
                redes_para_salvar = [{"nome": n.strip(), "localnet": r.strip()} for n, r in zip(nomes, redes) if n.strip() and r.strip()]
                update_localnets(redes_para_salvar)

            # 3. Gera o conteúdo para os arquivos de configuração
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

            # 4. Escreve os dados em um arquivo temporário para o serviço systemd ler
            temp_data = json.dumps({
                "interfaces": interfaces_content,
                "resolv": resolv_content,
                "iface": iface,
                "hostname": hostname
            })
            
            tmp_file_path = "/tmp/nanosip_net_config.json"
            with open(tmp_file_path, "w") as f:
                f.write(temp_data)
            
            # 5. Inicia o serviço systemd que lerá o arquivo temporário e aplicará as configs
            service_name = "nanosip-admin@update_network_config.service"
            subprocess.run(["sudo", "systemctl", "start", service_name], check=True)
            
            flash("Tarefa de atualização de rede iniciada com sucesso.", "success")

        except Exception as e:
            flash(f"Erro ao iniciar tarefa de atualização de rede: {str(e)}", "danger")
            
        return redirect(url_for("rede.config_rede"))

    # Para requisições GET
    network = carrega_config_atual()
    localnets = get_localnets()
    return render_template("config_rede.html", network=network, localnets=localnets)

