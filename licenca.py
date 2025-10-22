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
                data = json.load(f)
                return data
        except Exception as e:
            print(f"[licenca] Erro ao ler {LIC_FILE}: {e}")
    return {}

def save_hardware_file(hardware_id, cpu_serial=None, mac=None, status=None, valid_until=None, modulos_override=None):
    """Salva o arquivo oculto de licença (.lic.json)."""
    ensure_lic_dir()

    data = {
        "hardware_id": hardware_id,
        "cpu_serial": cpu_serial,
        "mac": mac,
    }

    if status is not None:
        data["status"] = status
    if valid_until is not None:
        data["valid_until"] = valid_until
    if modulos_override is not None:
        data["modulos_override"] = modulos_override

    try:
        with open(LIC_FILE, "w") as f:
            json.dump(data, f, indent=2)
        os.chmod(LIC_FILE, 0o600)
    except Exception as e:
        print(f"[licenca] Erro ao salvar {LIC_FILE}: {e}")

def produce_hardware_info():
    """Obtém informações básicas de hardware (UUID, MAC, is_vm, hardware_id) sem salvar arquivo."""
    info = {"is_vm": False, "uuid": None, "mac": None, "hardware_id": None}

    # ----- Detecta se é VM -----
    try:
        with open("/sys/class/dmi/id/product_name") as f:
            product_name = f.read().strip()
        if any(x in product_name for x in ["VMware", "VirtualBox", "KVM", "QEMU"]):
            info["is_vm"] = True
    except Exception:
        pass
    is_vm = info["is_vm"]

    # ----- Detecta UUID / Serial -----
    uuid_output = None
    try:
        uuid_output = subprocess.check_output(
            ["dmidecode", "-s", "system-uuid"], stderr=subprocess.DEVNULL
        ).decode().strip()
        if not uuid_output or uuid_output.startswith("00000000"):
            uuid_output = None
    except Exception:
        pass

    # ----- Fallback Raspberry Pi -----
    if not uuid_output:
        try:
            path = "/sys/firmware/devicetree/base/serial-number"
            if os.path.exists(path):
                with open(path, "r") as f:
                    uuid_output = f.read().replace("\x00", "").strip().upper()
        except Exception:
            pass

    # ----- Detecta interface de rede e MAC -----
    iface = None
    try:
        route_output = subprocess.check_output(
            "ip route | grep default | awk '{print $5}'",
            shell=True
        ).decode().strip()
        if route_output:
            iface = route_output.splitlines()[0]
    except Exception:
        pass

    mac_output = None
    if iface:
        path = f"/sys/class/net/{iface}/address"
        if os.path.exists(path):
            try:
                with open(path) as f:
                    mac_output = f.read().strip()
            except Exception:
                pass

    if not mac_output:
        for dev in os.listdir("/sys/class/net/"):
            if dev.startswith(("eth", "enp")):
                try:
                    with open(f"/sys/class/net/{dev}/address") as f:
                        mac_output = f.read().strip()
                        break
                except Exception:
                    continue

    # ----- Normaliza MAC e gera hash -----
    mac_clean = normalize_mac(mac_output)
    hardware_hash = compute_hardware_hash(uuid_output, mac_clean) if uuid_output and mac_clean else None

    # ----- Atualiza info -----
    info.update({
        "uuid": uuid_output,
        "mac": mac_clean,
        "hardware_id": hardware_hash,
        "is_vm": is_vm
    })

    return info



def registrar_chave_licenca(posted_key, is_vm=False):
    posted = (posted_key or "").strip()
    if not posted:
        return False, "Chave de licença não informada."

    cpu_serial, mac = parse_installer_key(posted)
    if not cpu_serial or not mac:
        return False, "Formato inválido da chave. Use UUID_MAC (ex.: 4C4C..._00D76D252709)."

    hardware_id = compute_hardware_hash(cpu_serial, mac)
    produto = "nanosip_vm" if is_vm else "nanosip_rasp"

    save_hardware_file(
        hardware_id=hardware_id,
        cpu_serial=cpu_serial,
        mac=mac,
        status="pendente"
    )

    try:
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
            save_hardware_file(
                hardware_id=hardware_id,
                cpu_serial=cpu_serial,
                mac=mac,
                status=data.get("status", "pendente"),
                valid_until=data.get("valid_until"),
                modulos_override=data.get("modulos_override")
            )
            return True, "Licença registrada com sucesso."
        else:
            return False, f"Falha ao validar licença (HTTP {response.status_code})"
    except Exception as e:
        return False, f"Erro ao registrar licença: {e}"

def normalize_cpu_serial(serial: str | None) -> str | None:
    if not serial:
        return None
    return serial.strip().upper()

def normalize_mac(mac: str | None) -> str | None:
    if not mac:
        return None
    mac = mac.strip().lower()
    pairs = re.findall(r'[0-9a-f]{2}', mac)
    if len(pairs) != 6:
        m = re.search(r'([0-9a-fA-F]{12})', mac)
        if m:
            s = m.group(1)
            pairs = [s[i:i+2] for i in range(0, 12, 2)]
    if not pairs or len(pairs) != 6:
        return None
    return ':'.join(pairs)

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
    """Gera hash SHA256 da chave de licença no formato UUID|MAC."""
    if not uuid or not mac:
        return None
    combined = f"UUID:{uuid}|MAC:{mac}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest().upper()

# ------------------
# Validação da licença
# ------------------
def get_license_status():
    data = load_hardware_file()
    status = data.get("status", "Desconhecido")
    valid_until = data.get("valid_until", None)
    print(f"get_license_status -> status: {status} ----   valid:{valid_until}")
    return status, valid_until

def validate_license():
    data = load_hardware_file()
    status = data.get("status", "Desconhecido")
    valid_until = data.get("valid_until", None)

    BR_TZ = timezone(timedelta(hours=-3))
    now = datetime.now(BR_TZ)
    valid_until_dt = None
    valid = False
    message = ""
    expires_at = None
    tolerance_days = 10

    if valid_until:
        try:
            valid_until_dt = datetime.strptime(valid_until, "%Y-%m-%d").replace(tzinfo=BR_TZ)
        except Exception:
            valid_until_dt = None
    else:
        valid_until_dt = None
    
    expires_at = None  # evita NameError no retorno final
    
    if status == "ativo" and valid_until_dt:
        if now <= valid_until_dt:
            valid = True
            control_asterisk("start")
            message = f"Licença válida até {valid_until_dt.date()}"
        elif now <= (valid_until_dt + timedelta(days=tolerance_days)):
            valid = True
            control_asterisk("start")
            expires_at = valid_until_dt + timedelta(days=tolerance_days)
            message = f"Licença vencida em {valid_until_dt.date()}. Sistema disponível até {expires_at.date()} (período de tolerância)"
        else:
            valid = False
            control_asterisk("stop")
            message = f"Licença vencida em {valid_until_dt.date() if valid_until_dt else 'desconhecida'}. Sistema bloqueado."
    
    elif status == "pendente":
        if valid_until_dt:
            # só entra aqui se houver data de validade
            if now <= (valid_until_dt + timedelta(days=tolerance_days)):
                valid = False
                control_asterisk("start")
                message = f"Licença com pendência de pagamento. Validade: {valid_until}"
            else:
                valid = False
                control_asterisk("stop")
                message = f"Licença com pendência de pagamento vencida em {valid_until_dt.date()}."
        else:
            # sem data nenhuma -> provavelmente primeira ativação
            valid = False
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
    
def get_protected_config_data():
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
    def is_asterisk_active():
        result = subprocess.run(["/usr/bin/systemctl", "is-active", "--quiet", "asterisk"])
        return result.returncode == 0

    action = action.lower()
    active = is_asterisk_active()

    if action == "start" and active:
        return True, "Asterisk já está rodando."
    if action == "stop" and not active:
        return True, "Asterisk já está parado."

    try:
        subprocess.run(["/usr/bin/systemctl", action, "asterisk"], check=True)
        return True, f"Asterisk {action}ado com sucesso."
    except Exception as e:
        return False, f"Erro ao {action} o Asterisk: {str(e)}"

def load_licenca_data():
    if not os.path.exists(LIC_FILE):
        return {}
    try:
        with open(LIC_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def atualizar_licenca_remota():
    """Atualiza a licença no servidor ou registra caso não exista arquivo .lic."""
    try:
        lic_data = load_licenca_data()
        arquivo_existe = bool(lic_data)

        # Se não existe arquivo .lic, precisa criar os dados a partir do hardware
        if not arquivo_existe:
            info = produce_hardware_info()
            cpu_serial = info.get("uuid")
            mac = info.get("mac")
            hardware_id = compute_hardware_hash(cpu_serial, mac)
            lic_data = {
                "hardware_id": hardware_id,
                "cpu_serial": cpu_serial,
                "mac": mac,
                "status": "pendente"
            }
            save_hardware_file(**lic_data)  # cria o arquivo

        # Produto dependendo se é VM ou Rasp
        is_vm = False  # opcional: detecta se é VM via produce_hardware_info() se quiser
        produto = "nanosip_vm" if is_vm else "nanosip_rasp"

        payload = {
            "uuid": lic_data["cpu_serial"],
            "mac": lic_data["mac"],
            "chave_licenca": lic_data["hardware_id"],
            "produto": produto
        }

        # Consulta API para atualizar status, validade e módulos
        response = requests.post(
            "https://gerenciamento.bar7cordas.com.br/api/ativar_licenca",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code in (200, 201):
            data = response.json()
            lic_data.update({
                "status": data.get("status", lic_data.get("status", "pendente")),
                "valid_until": data.get("valid_until"),
                "modulos_override": data.get("modulos_override")
            })
            save_hardware_file(**lic_data)
            return True, f"Status da licença atualizado: {lic_data['status']}"
        else:
            return False, "Falha ao consultar licença. Verifique sua conexão."

    except Exception as e:
        return False, f"Erro ao consultar licença: {str(e)}"


def get_modulos_override():
    lic_data = load_licenca_data()
    return lic_data.get("modulos_override")
