import uuid
import re
import subprocess
import hashlib
import json
import os
import requests
from datetime import datetime, timedelta, timezone

# Caminhos fixos e ocultos
BASE_DIR = "/opt/nanosip"
LIC_DIR = "/opt/nanosip/venv/bin/.lic"
LIC_FILE = os.path.join(LIC_DIR, ".lic.json")

def ensure_lic_dir():
    """Cria o diretório oculto de licenças se não existir."""
    try:
        if not os.path.exists(LIC_DIR):
            os.makedirs(LIC_DIR, mode=0o700, exist_ok=True)
    except Exception as e:
        print(f"[licenca] Erro ao criar diretório oculto {LIC_DIR}: {e}")

def load_hardware_file():
    """Carrega o arquivo de licença (.lic.json)"""
    ensure_lic_dir()
    if os.path.exists(LIC_FILE):
        try:
            with open(LIC_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[licenca] Erro ao ler {LIC_FILE}: {e}")
    return {}

def save_hardware_file(hardware_id, cpu_serial=None, mac=None, status=None, valid_until=None):
    """Salva o arquivo oculto de licença (.lic.json)"""
    ensure_lic_dir()
    data = {
        "hardware_id": hardware_id,
        "cpu_serial": cpu_serial,
        "mac": mac
    }
    if status:
        data["status"] = status
    if valid_until:
        data["valid_until"] = valid_until

    try:
        with open(LIC_FILE, "w") as f:
            json.dump(data, f, indent=2)
        os.chmod(LIC_FILE, 0o600)
    except Exception as e:
        print(f"[licenca] Erro ao salvar {LIC_FILE}: {e}")

def produce_hardware_info():
    """Obtém informações básicas de hardware (UUID e MAC)."""
    info = {"is_vm": False, "uuid": None, "mac": None, "hardware_id": None}
    try:
        # Detecta VM
        try:
            product_name = open("/sys/class/dmi/id/product_name").read().strip()
            if any(x in product_name for x in ["VMware", "VirtualBox", "KVM", "QEMU"]):
                info["is_vm"] = True
                return info
        except Exception:
            pass

        uuid_output = subprocess.check_output(["dmidecode", "-s", "system-uuid"]).decode().strip()
        mac_output = subprocess.check_output(["cat", "/sys/class/net/eth0/address"]).decode().strip()

        mac_clean = mac_output.replace(":", "").upper()
        hardware_key = f"{uuid_output}_{mac_clean}"

        info.update({
            "uuid": uuid_output,
            "mac": mac_clean,
            "hardware_id": hardware_key
        })
    except Exception as e:
        info["erro"] = str(e)
    return info

def normalize_cpu_serial(serial: str | None) -> str | None:
    if not serial:
        return None
    return serial.strip().upper()

def normalize_mac(mac: str | None) -> str | None:
    if not mac:
        return None
    mac = mac.strip()
    pairs = re.findall(r'[0-9A-Fa-f]{2}', mac)
    if len(pairs) != 6:
        m = re.search(r'([0-9A-Fa-f]{12})', mac)
        if m:
            s = m.group(1)
            pairs = [s[i:i+2] for i in range(0, 12, 2)]
    if not pairs or len(pairs) != 6:
        return None
    return ':'.join(p.lower() for p in pairs)

def parse_installer_key(installer_key: str):
    if not installer_key or '_' not in installer_key:
        return None, None
    uuid_part, mac_part = installer_key.split('_', 1)
    cpu_serial = normalize_cpu_serial(uuid_part)
    mac_raw = mac_part.replace('-', '').replace(':', '').strip()
    if len(mac_raw) == 12 and re.fullmatch(r'[0-9A-Fa-f]{12}', mac_raw):
        mac_pairs = [mac_raw[i:i+2] for i in range(0, 12, 2)]
        mac_joined = ':'.join(mac_pairs)
    else:
        mac_joined = mac_part
    mac = normalize_mac(mac_joined)
    return cpu_serial, mac

def compute_hardware_hash(uuid, mac):
    """Gera hash SHA256 da chave de licença."""
    if not uuid or not mac:
        return None
    combined = f"UUID:{uuid}|MAC:{mac}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest().upper()

# ------------------
# Validação da licença
# ------------------
def get_license_status():
    """Lê status e validade do arquivo .lic.json"""
    data = load_hardware_file()
    status = data.get("status", "Desconhecido")
    valid_until = data.get("valid_until", None)
    return status, valid_until

from datetime import datetime, timedelta, timezone

from datetime import datetime, timedelta, timezone

def validate_license():
    """Valida a licença atual"""
    data = load_hardware_file()
    status = data.get("status", "Desconhecido")
    valid_until = data.get("valid_until", None)

    # Timezone do Brasil (UTC-3)
    BR_TZ = timezone(timedelta(hours=-3))
    now = datetime.now(BR_TZ)
    valid_until_dt = None
    valid = False
    message = ""
    expires_at = None
    tolerance_days = 10

    # Converter data de validade com timezone
    if valid_until:
        try:
            valid_until_dt = datetime.strptime(valid_until, "%Y-%m-%d").replace(tzinfo=BR_TZ)
        except Exception:
            valid_until_dt = None

    # Lógica de validação
    if status == "ativo":
        if valid_until_dt and now <= valid_until_dt:
            valid = True
            control_asterisk("start")
            message = f"Licença válida até {valid_until_dt.date()}"
        elif valid_until_dt and now <= (valid_until_dt + timedelta(days=tolerance_days)):
            valid = True
            control_asterisk("start")
            expires_at = valid_until_dt + timedelta(days=tolerance_days)
            message = f"Licença vencida em {valid_until_dt.date()}. Sistema disponível até {expires_at.date()} (período de tolerância)"
        else:
            valid = False
            control_asterisk("stop")
            message = f"Licença vencida em {valid_until_dt.date() if valid_until_dt else 'desconhecida'}. Sistema bloqueado."
    elif status == "pendente":
        valid = True
        control_asterisk("stop")
        message = "Licença pendente de validação. Possível problema de conexão."
    elif status == "bloqueado":
        valid = False
        control_asterisk("stop")
        message = "Licença bloqueada pelo gerenciamento. Sistema bloqueado."
    else:
        valid = True
        message = "Problema ao verificar licença. Possível falha de conexão."

    return {
        "valid": valid,
        "message": message,
        "expires_at": expires_at
    }

# ------------------
# Protected config data (para app.py)
# ------------------
def get_protected_config_data():
    """Retorna dados essenciais para o app baseado na licença"""
    license_info = validate_license()
    if license_info["valid"]:
        blueprints_permitidos = ["main", "auth", "nanosip", "rede", "rotas", "relatorios"]
        status = "ok"
    else:
        blueprints_permitidos = ["main", "auth"]
        status = "error"

    return {
        "status": status,
        "message": license_info["message"],
        "blueprints_permitidos": blueprints_permitidos
    }

def control_asterisk(action: str):
    #return True, f"Simulação: Asterisk não será {action}ado."
    """
    Controla o serviço Asterisk.
    action: 'start' ou 'stop'
    Retorna tupla (sucesso: bool, mensagem: str)
    """
    def is_asterisk_active():
        result = subprocess.run(["/usr/bin/systemctl", "is-active", "--quiet", "asterisk"])
        return result.returncode == 0

    action = action.lower()
    active = is_asterisk_active()

    # Se a ação já está no estado desejado, não faz nada
    if action == "start" and active:
        return True, "Asterisk já está rodando."
    if action == "stop" and not active:
        return True, "Asterisk já está parado."

    # Executa a ação
    try:
        subprocess.run(["/usr/bin/systemctl", action, "asterisk"], check=True)
        return True, f"Asterisk {action}ado com sucesso."
    except Exception as e:
        return False, f"Erro ao {action} o Asterisk: {str(e)}"

def load_licenca_data():
    """Lê o conteúdo do arquivo .lic e retorna os dados como dicionário."""
    if not os.path.exists(LIC_FILE):
        return {}
    try:
        with open(LIC_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_hardware_file(hardware_id, cpu_serial, mac, status, valid_until, modulos_override=None):
    """Salva os dados da licença no arquivo local .lic."""
    data = {
        "hardware_id": hardware_id,
        "cpu_serial": cpu_serial,
        "mac": mac,
        "status": status,
        "valid_until": valid_until,
        "modulos_override": modulos_override or "",
    }
    with open(LIC_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_licenca_data():
    """Lê o conteúdo do arquivo .lic e retorna os dados como dicionário."""
    if not os.path.exists(LIC_FILE):
        return {}
    try:
        with open(LIC_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_hardware_file(hardware_id, cpu_serial, mac, status, valid_until, modulos_override=None):
    """Salva os dados da licença no arquivo local .lic."""
    data = {
        "hardware_id": hardware_id,
        "cpu_serial": cpu_serial,
        "mac": mac,
        "status": status,
        "valid_until": valid_until,
        "modulos_override": modulos_override or "",
    }
    with open(LIC_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --- Função principal que consulta o servidor remoto e atualiza o .lic ---

def atualizar_licenca_remota():
    """Consulta o status da licença no servidor e atualiza o arquivo local."""
    try:
        info = produce_hardware_info()
        lic_data = load_licenca_data()

        hardware_id = lic_data.get("hardware_id")
        cpu_serial = lic_data.get("cpu_serial")
        mac = lic_data.get("mac")
        is_vm = info.get("is_vm", False)

        if not hardware_id or not cpu_serial or not mac:
            return False, "Nenhuma licença cadastrada para consultar."

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
            modulos_override = data.get("modulos_override", "N/A")

            save_hardware_file(
                hardware_id=hardware_id,
                cpu_serial=cpu_serial,
                mac=mac,
                status=status_api,
                valid_until=validade,
                modulos_override=modulos_override
            )
            return True, f"Status da licença atualizado: {status_api}"
        else:
            return False, "Falha ao consultar licença. Verifique sua conexão."

    except Exception as e:
        return False, f"Erro ao consultar licença: {str(e)}"

def get_modulos_override():
    lic_data = load_licenca_data()
    return lic_data.get("modulos_override")
  
#def atualizar_licenca_remota():
#    """Consulta o status da licença no servidor e atualiza o arquivo local."""
#    try:
#        info = produce_hardware_info()
#        lic_data = load_hardware_file()
#
#        hardware_id = lic_data.get("hardware_id")
#        cpu_serial = lic_data.get("cpu_serial")
#        mac = lic_data.get("mac")
#        is_vm = info.get("is_vm", False)
#
#        if not hardware_id or not cpu_serial or not mac:
#            return False, "Nenhuma licença cadastrada para consultar."
#
#        produto = "nanosip_vm" if is_vm else "nanosip_rasp"
#        payload = {
#            "uuid": cpu_serial,
#            "mac": mac,
#            "chave_licenca": hardware_id,
#            "produto": produto
#        }
#
#        response = requests.post(
#            "https://gerenciamento.bar7cordas.com.br/api/ativar_licenca",
#            json=payload,
#            headers={"Content-Type": "application/json"},
#            timeout=10
#        )
#
#        if response.status_code in (200, 201):
#            data = response.json()
#            status_api = data.get("status", "desconhecido")
#            validade = data.get("valid_until", "N/A")
#            modulos_override = data.get("modulos_override", "N/A")
#
#            save_hardware_file(
#                hardware_id=hardware_id,
#                cpu_serial=cpu_serial,
#                mac=mac,
#                status=status_api,
#                valid_until=validade,
#                modulos_override=modulos_override
#            )
#            return True, f"Status da licença atualizado: {status_api}"
#        else:
#            return False, "Falha ao consultar licença. Verifique sua conexão."
#    except Exception as e:
#        return False, f"Erro ao consultar licença: {str(e)}"
#
    
    
