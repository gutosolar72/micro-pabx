import uuid
import re
import subprocess
import hashlib
import json
import os

LIC_FILE = "/opt/nanosip/licenca.txt"

def load_hardware_file():
    if os.path.exists(LIC_FILE):
        with open(LIC_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_hardware_file(hardware_id, cpu_serial=None, mac=None):
    """
    Salva a chave de ativação (hash) e, opcionalmente, UUID e MAC no arquivo licenca.txt
    """
    data = {
        "hardware_id": hardware_id,
        "cpu_serial": cpu_serial,
        "mac": mac
    }
    with open(LIC_FILE, "w") as f:
        json.dump(data, f)

def produce_hardware_info():
    info = {"is_vm": False, "uuid": None, "mac": None, "hardware_id": None}

    try:
        # Detecta VM
        try:
            product_name = open("/sys/class/dmi/id/product_name").read().strip()
            if any(x in product_name for x in ["VMware", "VirtualBox", "KVM", "QEMU"]):
                info["is_vm"] = True
                return info  # se for VM, retornamos logo
        except Exception:
            pass  # se não conseguir ler, assume que não é VM

        # Se não é VM, pega UUID e MAC
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
    """Normaliza o CPU serial: trim e uppercase."""
    if not serial:
        return None
    return serial.strip().upper()

def normalize_mac(mac: str | None) -> str | None:
    """
    Aceita MAC em várias formas:
     - 00D76D252709
     - 00:D7:6D:25:27:09
     - 00-d7-6d-25-27-09
    Retorna mac formatado em minúsculas com dois-pontos: 00:d7:6d:25:27:09
    """
    if not mac:
        return None
    mac = mac.strip()
    # Extrai pares hexadecimais
    pairs = re.findall(r'[0-9A-Fa-f]{2}', mac)
    if len(pairs) == 12:  # por algum motivo detectou cada dígito - improvável
        # re.findall pode separar em 12 grupos se regex for errado; mas normalmente pega pares
        pass
    if not pairs or len(''.join(pairs)) < 12:
        # tenta extrair 12 hex chars em sequência
        m = re.search(r'([0-9A-Fa-f]{12})', mac)
        if m:
            s = m.group(1)
            pairs = [s[i:i+2] for i in range(0, 12, 2)]
    if not pairs or len(pairs) != 6:
        return None
    return ':'.join(p.lower() for p in pairs)

def parse_installer_key(installer_key: str):
    """
    Espera formato: <UUID>_<MAC_SEM_SEPARADOR> (ex: UUID_00D76D252709)
    Retorna (cpu_serial, mac) normalizados ou (None, None) se inválido.
    """
    if not installer_key or '_' not in installer_key:
        return None, None
    uuid_part, mac_part = installer_key.split('_', 1)
    cpu_serial = normalize_cpu_serial(uuid_part)
    # mac_part pode vir sem ':' então normaliza com normalize_mac
    mac_raw = mac_part.replace('-', '').replace(':', '').strip()
    # Se instalador enviar MAC em maiúsculas sem :, ainda funciona
    # reconstruímos com pairs
    if len(mac_raw) == 12 and re.fullmatch(r'[0-9A-Fa-f]{12}', mac_raw):
        # transforma em pairs
        mac_pairs = [mac_raw[i:i+2] for i in range(0, 12, 2)]
        mac_joined = ':'.join(mac_pairs)
    else:
        mac_joined = mac_part
    mac = normalize_mac(mac_joined)
    return cpu_serial, mac

# Atualize compute_hardware_hash para normalizar internamente:
def compute_hardware_hash(cpu_serial, mac):
    """Gera SHA256 a partir dos identificadores presentes (ordena para determinismo)."""
    # Normaliza para garantir que hash gerado no instalador e no dispositivo físico bata
    cpu_serial_norm = normalize_cpu_serial(cpu_serial)
    mac_norm = normalize_mac(mac)
    parts = []
    if cpu_serial_norm:
        parts.append(f"CPU_SERIAL:{cpu_serial_norm}")
    if mac_norm:
        parts.append(f"MAC:{mac_norm}")
    if not parts:
        return None
    combined = "|".join(sorted(parts))
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

