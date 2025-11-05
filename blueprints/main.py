from flask import Blueprint, render_template, redirect, url_for, flash, request, session
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
    # 1️⃣ Carrega dados da licença, se existir
    lic_data = lic.load_licenca_data()
    info = lic.produce_hardware_info()
    is_vm_detected = info["is_vm"]

    cpu_serial = None
    mac = None
    hardware_id = None

    if lic_data:
        # Licença já existe
        is_vm = lic_data.get("is_vm", is_vm_detected)
        cpu_serial = lic_data.get("cpu_serial")
        mac = lic_data.get("mac")
        hardware_id = lic_data.get("hardware_id")
    else:
        # Sem licença ainda
        is_vm = is_vm_detected
        cpu_serial = info.get("uuid")
        mac = info.get("mac")
        hardware_id = info.get("hardware_id")

        if not is_vm:
            # Máquina física → gera arquivo automaticamente
            lic_key = f"{cpu_serial}_{mac}"
            lic.atualizar_licenca_remota(lic_key, is_vm=False)

    # 2️⃣ POST
    if request.method == "POST":
        if request.form.get("check_status"):
            ok, msg = lic.atualizar_licenca_remota()
            flash(msg, "success" if ok else "warning")
        elif is_vm:
            posted = request.form.get("hardware_key", "").strip()
            if not posted:
                flash("Informe a Chave de Ativação.", "danger")
                return redirect(url_for("main.licenca_status"))

            ok, msg = lic.atualizar_licenca_remota(posted_key=posted, is_vm=True)
            flash(msg, "success" if ok else "danger")
            return redirect(url_for("main.licenca_status"))
        else:
            flash("Sistema detectado como hardware físico — gravação manual não permitida.", "warning")
            return redirect(url_for("main.licenca_status"))

    # 3️⃣ GET → status atual
    lic_data = lic.load_licenca_data()  # recarrega
    status, validade = lic.get_license_status()
    license_info = lic.validate_license()

    # Determina se deve mostrar formulário de chave VM
    show_vm_form = is_vm and (not lic_data or license_info["valid"] is False)

    # Determina mensagem para hardware físico
    hardware_msg = None
    if not is_vm and license_info["valid"]:
        hardware_msg = "Hardware físico. Licença gerada automaticamente."

    return render_template(
        "licenca.html",
        status={
            "hardware_id": lic_data.get("hardware_id"),
            "status": status,
            "validade": validade,
            "msg": license_info["message"] if not hardware_msg else hardware_msg
        },
        is_vm=is_vm,
        show_vm_form=show_vm_form,
        cpu_serial=lic_data.get("cpu_serial"),
        mac=lic_data.get("mac"),
        LICENSE_VALID=license_info["valid"],
        LICENSE_MSG=license_info["message"]
    )


@main_bp.route("/reload", methods=["POST"])
@login_required
def reload():
    try:
        subprocess.run(
            ["/usr/bin/systemctl", "start", "nanosip-admin@apply_config.service"],
            check=True
        )
        flash("Configurações aplicadas com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao aplicar configurações: {e}", "danger")
    return redirect(url_for("main.index"))

