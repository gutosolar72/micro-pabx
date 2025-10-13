#!/opt/nanosip/venv/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime
import requests
import subprocess

# Adicionar o caminho do projeto
sys.path.append("/opt/nanosip")
import licenca as lic

LOG_FILE = "/var/log/nanosip/nanosip_license.log"


def log(msg):
    """Grava logs simples com data e hora."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] {msg}\n")


def check_license_remote():
    """Atualiza a licença na API se o arquivo local existir."""
    lic_file = lic.LIC_FILE
    if not os.path.exists(lic_file):
        log("❌ Nenhuma licença local encontrada.")
        return False

    # Carrega os dados atuais
    lic_data = lic.load_hardware_file()
    payload = {
        "uuid": lic_data.get("cpu_serial"),
        "mac": lic_data.get("mac"),
        "chave_licenca": lic_data.get("hardware_id"),
        "produto": "nanosip_vm" if lic_data.get("is_vm") else "nanosip_rasp"
    }

    try:
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
                hardware_id=payload["chave_licenca"],
                cpu_serial=payload["uuid"],
                mac=payload["mac"],
                status=status_api,
                valid_until=validade
            )

            log(f"✅ Licença atualizada: {status_api} | validade: {validade}")
            return True
        else:
            log(f"⚠️ Falha ao consultar licença: HTTP {response.status_code}")
            return False

    except Exception as e:
        log(f"⚠️ Erro ao consultar licença: {e}")
        return False

def main():
    """Fluxo principal do verificador automático."""
    log("🔍 Iniciando verificação automática da licença...")

    # Atualiza a licença no servidor
    updated = check_license_remote()

    # Valida licença local e decide ação do Asterisk
    license_info = lic.validate_license()
    action = "start" if license_info["valid"] else "stop"

    # Controla o Asterisk conforme a licença
    success, msg = lic.control_asterisk(action)
    log(f"Asterisk: {msg}")

    # --- Chamando o system_manager.sh ---
    try:
        sh_path = "/opt/nanosip/system_manager.sh"
        result = subprocess.run([sh_path, "apply_config"], capture_output=True, text=True, check=True)
        log(f"system_manager.sh executado com sucesso:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        log(f"❌ Erro ao executar system_manager.sh:\n{e.stderr}")

    if updated:
        log("✔️ Verificação concluída com sucesso.\n")
    else:
        log("❌ Verificação falhou. Verifique conectividade.\n")

if __name__ == "__main__":
    main()
