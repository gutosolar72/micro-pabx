from flask import Blueprint, render_template, redirect, url_for, flash, request
import subprocess
import requests
import json

from system_info import get_system_info
from auth import login_required
import licenca as lic  # módulo de funções de licença

main_bp = Blueprint('main', __name__)


def license_context():
    """Retorna True se a licença estiver ativa (pode usar o sistema)."""
    info = lic.validate_license()
    return info["valid"]

def license_message():
    """Retorna a mensagem de status da licença para exibir no HTML."""
    info = lic.validate_license()
    return info["message"]

# ---------- Rotas ----------
@main_bp.route("/")
def index():
    info = get_system_info()
    return render_template(
        "index.html",
        info=info,
        LICENSE_VALID=license_context(),
        LICENSE_MSG=license_message()
    )

@main_bp.route("/licenca", methods=["GET", "POST"])
@login_required
def licenca_status():
    info = lic.produce_hardware_info()
    lic_data = lic.load_hardware_file()

    hardware_id = lic_data.get("hardware_id")
    cpu_serial = lic_data.get("cpu_serial")
    mac = lic_data.get("mac")
    is_vm = info.get("is_vm", False)
    status, validade = lic.get_license_status()

    license_status = status or "--"
    license_info = lic.validate_license()  # <-- valida licença e pega mensagem

    if request.method == "POST":
        # --- Checar status na API ---
        if request.form.get("check_status"):
            if not hardware_id:
                flash("Nenhuma licença cadastrada para consultar.", "warning")
                return redirect(url_for("main.licenca_status"))
            try:
                produto = "nanosip_vm" if is_vm else "nanosip_rasp"
                payload = {
                    "uuid": cpu_serial,
                    "mac": mac,
                    "chave_licenca": hardware_id,
                    "produto": produto
                }
                response = requests.post(
                    "https://gerenciamento.bar7cordas.com.br/api/ativar_licenca",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                if response.status_code in (200, 201):
                    data = response.json()
                    status_api = data.get("status", "desconhecido")
                    validade = data.get("valid_until", "N/A")

                    lic.save_hardware_file(
                        hardware_id=hardware_id,
                        cpu_serial=cpu_serial,
                        mac=mac,
                        status=status_api,
                        valid_until=validade
                    )
                    flash(f"Status da licença atualizado: {status_api}", "success")
                else:
                    flash(f"Falha ao consultar licença! Verifique sua conexão de internet.", "warning")
            except Exception as e:
                flash(f"Falha ao consultar licença! Verifique sua conexão de internet.", "warning")
            return redirect(url_for("main.licenca_status"))

        # --- Salvar nova chave (VM) ---
        if not is_vm:
            flash("Sistema detectado como hardware físico — gravação manual não permitida.", "warning")
            return redirect(url_for("main.licenca_status"))

        posted = request.form.get("hardware_key", "").strip()
        if not posted:
            flash("Informe a Chave de Ativação.", "danger")
            return redirect(url_for("main.licenca_status"))

        cpu_serial, mac = lic.parse_installer_key(posted)
        if not cpu_serial or not mac:
            flash("Formato da chave inválido. Use: UUID_MAC (ex.: 4C4C..._00D76D252709).", "danger")
            return redirect(url_for("main.licenca_status"))

        hardware_id = lic.compute_hardware_hash(cpu_serial, mac)
        lic.save_hardware_file(
            hardware_id=hardware_id,
            cpu_serial=cpu_serial,
            mac=mac,
            status="pendente"
        )

        flash("Chave de Ativação salva com sucesso. Aguardando validação...", "success")

        try:
            produto = "nanosip_vm" if is_vm else "nanosip_rasp"
            payload = {
                "uuid": cpu_serial,
                "mac": mac,
                "chave_licenca": hardware_id,
                "produto": produto
            }
            response = requests.post(
                "https://gerenciamento.bar7cordas.com.br/api/ativar_licenca",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code in (200, 201):
                flash("Licença enviada com sucesso para o gerenciamento.", "info")
            else:
                flash(f"Falha ao validar licença. Verifique a chave ou entre em contato com o suporte", "warning")
        except Exception as e:
            flash(f"Falha ao validar licença. Verifique a chave ou entre em contato com o suporte", "warning")

        return redirect(url_for("main.licenca_status"))

    return render_template(
        "licenca.html",
        status={
            "hardware_id": hardware_id,
            "status": license_status,
            "validade": validade,
            "msg": license_info["message"]
        },
        is_vm=is_vm,
        cpu_serial=cpu_serial,
        mac=mac,
        LICENSE_VALID=license_context(),
        LICENSE_MSG=license_message()
    )

@main_bp.route("/reload", methods=["POST"])
@login_required
def reload():
    try:
        subprocess.run(["sudo", "systemctl", "start", "nanosip-admin@apply_config.service"], check=True)
        flash("Tarefa de aplicar configurações iniciada com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao iniciar tarefa de reload: {str(e)}", "danger")
    return redirect(url_for("main.index"))

