#!/opt/nanosip/venv/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

# Adicionar o caminho do projeto
sys.path.append("/opt/nanosip")

import licenca as lic  # importa o módulo de licença

LOG_FILE = "/var/log/nanosip_licence.log"


def log(msg):
    """Grava logs simples com data e hora."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] {msg}\n")


def check_license_remote():
    """Consulta a licença no servidor remoto e atualiza o arquivo local."""
    info = lic.produce_hardware_info()
    lic_data = lic.load_hardware_file()

    hardware_id = lic_data.get("hardware_id")
    cpu_serial = lic_data.get("cpu_serial")
    mac = lic_data.get("mac")
    is_vm = info.get("is_vm", False)

    if not hardware_id or not cpu_serial or not mac:
        log("❌ Nenhuma licença local encontrada para consultar.")
        return False

    produto = "nanosip_vm" if is_vm else "nanosip_rasp"
    payload = {
        "uuid": cpu_serial,
        "mac": mac,
        "chave_licenca": hardware_id,
        "produto": produto
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
                hardware_id=hardware_id,
                cpu_serial=cpu_serial,
                mac=mac,
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

    updated = check_license_remote()

    # Controle do Asterisk independente
    status_msg, level = lic.control_asterisk()
    log(f"Asterisk: {status_msg}")

    if updated:
        log("✔️ Verificação concluída com sucesso.\n")
    else:
        log("❌ Verificação falhou. Verifique conectividade.\n")


if __name__ == "__main__":
    main()

