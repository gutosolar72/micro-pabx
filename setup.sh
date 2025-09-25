#!/bin/bash

# Script de Setup para o Micro PABX
# Este script deve ser executado com 'sudo' (ex: sudo ./setup.sh)

# Garante que o script pare se qualquer comando falhar
set -e

# Pega o caminho absoluto do diretório onde o script está
BASE_DIR=$(cd "$(dirname "$0")" && pwd)

echo "--- Iniciando Setup do Micro PABX ---"

echo "[1/4] Configurando permissões do sudoers..."
ln -sf "$BASE_DIR/config/pabx_sudoers" "/etc/sudoers.d/pabx_permissions"
visudo -c -f /etc/sudoers.d/pabx_permissions
chown root:root "$BASE_DIR/config/pabx_sudoers"


echo "[2/4] Configurando serviços do systemd..."
ln -sf "$BASE_DIR/config/micropabx.service" "/etc/systemd/system/micropabx.service"
ln -sf "$BASE_DIR/config/pabx-admin@.service" "/etc/systemd/system/pabx-admin@.service"

echo "[3/4] Instalando dependências do sistema (jq)..."
apt-get update > /dev/null
apt-get install -y jq > /dev/null
echo "Dependências instaladas."

echo "[4/4] Recarregando e ativando os serviços..."
systemctl daemon-reload
systemctl enable micropabx.service
systemctl restart micropabx.service
echo "Serviço principal 'micropabx.service' ativado e iniciado."

echo ""
echo "--- SETUP CONCLUÍDO! ---"
echo "Para verificar o status da aplicação, use: sudo systemctl status micropabx.service"

