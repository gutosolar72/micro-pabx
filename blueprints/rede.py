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
    Carrega as configurações de rede executando um script de sistema como root
    e capturando sua saída para depuração detalhada.
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
        script_path = "/opt/nanosip/system_manager.sh"
        task_name = "get_network_info"

        # --- MUDANÇA PRINCIPAL: CAPTURAR TUDO ---
        # Executamos o comando e capturamos stdout e stderr, sem falhar em caso de erro.
        # 'check=True' foi removido para que possamos inspecionar o resultado mesmo se houver erro.
        result = subprocess.run(
            ["sudo", script_path, task_name],
            capture_output=True,
            text=True,
            timeout=10
        )

        # --- BLOCO DE DEPURAÇÃO ---
        # Verificamos o que realmente aconteceu na execução do script.

        # Se o script retornou um código de erro...
        if result.returncode != 0:
            # Criamos uma mensagem de erro detalhada para o flash.
            error_details = (
                f"O script de sistema falhou com código de saída {result.returncode}. "
                f"Saída Padrão (STDOUT): '{result.stdout}'. "
                f"Saída de Erro (STDERR): '{result.stderr}'."
            )
            flash(error_details, "danger")
            # Retornamos o dicionário com os valores padrão para a página não quebrar.
            return network_info

        # Se o script rodou com sucesso (código 0), mas não produziu nada...
        if not result.stdout.strip():
            error_details = (
                f"O script de sistema rodou com sucesso, mas não produziu saída (stdout). "
                f"Saída de Erro (STDERR): '{result.stderr}'."
            )
            flash(error_details, "warning")
            return network_info

        # Se chegamos aqui, o script rodou E produziu uma saída.
        # Agora tentamos decodificar o JSON.
        output_json = result.stdout.strip()
        data_from_script = json.loads(output_json)

        # Atualiza o dicionário network_info com os dados obtidos
        network_info.update(data_from_script)

    except json.JSONDecodeError:
        # Este erro agora é mais informativo.
        flash(f"O script produziu uma saída, mas não é um JSON válido. Saída recebida: '{result.stdout}'", "danger")

    except subprocess.TimeoutExpired:
        # Ocorre se o script demorar mais de 10 segundos para responder
        flash("A obtenção das informações de rede demorou muito para responder (timeout).", "danger")

    except Exception as e:
        # Captura qualquer outro erro (ex: FileNotFoundError se o script não existir)
        flash(f"Um erro inesperado ocorreu ao buscar as informações de rede: {str(e)}", "danger")

    # Retorna o dicionário, atualizado ou com os valores padrão em caso de erro.
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

