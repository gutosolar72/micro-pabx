import uuid
import re
import subprocess
import hashlib
import json
import os

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
    """
    Salva o arquivo oculto de licença (.lic.json)
    Inclui status e validade caso fornecidos.
    """
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
            json.dump(data, f)
        os.chmod(LIC_FILE, 0o600)
    except Exception as e:
        print(f"[licenca] Erro ao salvar {LIC_FILE}: {e}")

def produce_hardware_info():
    """Obtém informações básicas de hardware (UUID e MAC)."""
    info = {"is_vm": False, "uuid": None, "mac": None, "hardware_id": None}
    try:
        try:
            product_name = open("/sys/class/dmi/id/product_name").read().strip()
            if any(x in product_name for x in ["VMware", "VirtualBox", "KVM", "QEMU"]):
                info["is_vm"] = True
                return info
        except Exception:
            pass

        uuid_output = subprocess.check_output(["dmidecode", "-s", "system-uuid"]).decode().strip()
        mac_output = subprocess.check_output(["cat", "/sys/class/net/eth0/address"]).decode().strip()

        uuid_clean = uuid_output.replace("-", "")
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
    if len(pairs) == 12:
        pass
    if not pairs or len(''.join(pairs)) < 12:
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
    """
    Gera hash SHA256 da chave de licença.
    Para VM: recebe UUID e MAC fornecidos pelo usuário (formato UUID_MAC).
    Para hardware físico: recebe UUID e MAC da máquina.
    """
    if not uuid or not mac:
        return None

    combined = f"UUID:{uuid}|MAC:{mac}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest().upper()

# ---- Novo helper para status ----
def get_license_status():
    """Lê status e validade do arquivo .lic.json, se existir."""
    data = load_hardware_file()
    status = data.get("status", "Desconhecido")
    valid_until = data.get("valid_until", None)
    return status, valid_until


def ensure_lic_dir():
    """Garante que o diretório e o arquivo de licença existam."""
    if not os.path.exists(LIC_DIR):
        os.makedirs(LIC_DIR, exist_ok=True)
    if not os.path.exists(LIC_FILE):
        with open(LIC_FILE, "w") as f:
            json.dump({}, f)


def load_license_status():
    """Carrega o status salvo da licença."""
    ensure_lic_dir()
    try:
        with open(LIC_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_license_status(data):
    """Salva o status atual da licença no arquivo oculto."""
    ensure_lic_dir()
    with open(LIC_FILE, "w") as f:
        json.dump(data, f, indent=2)
