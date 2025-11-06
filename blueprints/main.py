from flask import Blueprint, render_template, redirect, url_for, flash, request
import subprocess
from system_info import get_system_info
from auth import login_required
import licenca as lic  # módulo de funções de licença


main_bp = Blueprint("main", __name__)


# ============================================================
# 🧩 Funções auxiliares de licença
# ============================================================

def license_context():
    """Retorna True se a licença estiver ativa."""
    info = lic.validate_license()
    return info["valid"]

def license_message():
    """Retorna a mensagem de status da licença."""
    info = lic.validate_license()
    return info["message"]


# ============================================================
# 🏠 Página inicial
# ============================================================

@main_bp.route("/")
def index():
    info = get_system_info()
    return render_template(
        "index.html",
        info=info,
        LICENSE_VALID=license_context(),
        LICENSE_MSG=license_message()
    )


# ============================================================
# 🔑 Página de Licença
# ============================================================

@main_bp.route("/licenca", methods=["GET", "POST"])
@login_required
def licenca_status():
    """
    Exibe o status da licença e permite atualizar ou registrar nova chave.
    """
    # Limpa mensagens antigas antes de processar nova requisição
    session = request.environ.get("werkzeug.session")
    if session:
        session.pop("_flashes", None)

    # 1️⃣ Carrega dados e informações do hardware
    lic_data = lic.load_licenca_data()
    info = lic.produce_hardware_info()
    is_vm_detected = info["is_vm"]

    # Dados base
    cpu_serial = None
    mac = None
    hardware_id = None

    # 2️⃣ Identifica se há licença local existente
    if lic_data:
        is_vm = lic_data.get("is_vm", is_vm_detected)
        cpu_serial = lic_data.get("cpu_serial")
        mac = lic_data.get("mac")
        hardware_id = lic_data.get("hardware_id")
    else:
        is_vm = is_vm_detected
        cpu_serial = info.get("uuid")
        mac = info.get("mac")
        hardware_id = info.get("hardware_id")

        # Gera automaticamente licença local para máquina física
        if not is_vm:
            lic_key = f"{cpu_serial}_{mac}"
            ok, msg = lic.atualizar_licenca_remota(lic_key, is_vm=False)
            flash(msg, "success" if ok else "danger")

    # 3️⃣ Processamento de formulário (POST)
    if request.method == "POST":
        # Checar status remoto
        if request.form.get("check_status"):
            ok, msg = lic.atualizar_licenca_remota()
            flash(msg, "success" if ok else "warning")

        # Registro manual em VM
        elif is_vm:
            posted = request.form.get("hardware_key", "").strip()
            if not posted:
                flash("Informe a Chave de Ativação.", "danger")
                return redirect(url_for("main.licenca_status"))

            ok, msg = lic.atualizar_licenca_remota(posted_key=posted, is_vm=True)
            flash(msg, "success" if ok else "danger")

        # Máquina física → não permite entrada manual
        else:
            flash("Sistema detectado como hardware físico — gravação manual não permitida.", "warning")

        return redirect(url_for("main.licenca_status"))

    # 4️⃣ Recarrega dados após operações
    lic_data = lic.load_licenca_data() or {}
    status, validade = lic.get_license_status()
    license_info = lic.validate_license()

    # Exibir formulário de VM apenas se necessário
    show_vm_form = is_vm and (not lic_data or not license_info["valid"])

    # Mensagem específica para hardware físico
    hardware_msg = None
    if not is_vm and license_info["valid"]:
        hardware_msg = "Hardware físico. Licença gerada automaticamente."

    modulos = lic.get_modulos()

    # 5️⃣ Renderiza template final
    return render_template(
        "licenca.html",
        status={
            "hardware_id": lic_data.get("hardware_id"),
            "status": status,
            "validade": validade,
            "msg": hardware_msg or license_info["message"],
            "modulos": modulos
        },
        is_vm=is_vm,
        show_vm_form=show_vm_form,
        cpu_serial=lic_data.get("cpu_serial"),
        mac=lic_data.get("mac"),
        LICENSE_VALID=license_info["valid"],
        LICENSE_MSG=license_info["message"]
    )


# ============================================================
# 🔁 Aplicar Configurações
# ============================================================

@main_bp.route("/reload", methods=["POST"])
@login_required
def reload():
    """
    Aplica novamente as configurações do sistema.
    """
    try:
        subprocess.run(
            ["/usr/bin/systemctl", "start", "nanosip-admin@apply_config.service"],
            check=True
        )
        flash("Configurações aplicadas com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao aplicar configurações: {e}", "danger")

    return redirect(url_for("main.index"))

