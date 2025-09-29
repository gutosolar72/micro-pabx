#!/bin/bash

echo "--- Iniciando Setup do Nanosip ---"

# Pega o caminho absoluto do diretório onde o script está
BASE_DIR=$(cd "$(dirname "$0")" && pwd)
virtualenv "$BASEDIR/"

echo "[1/4] Configurando permissões do sudoers..."
echo "# Permite ao usuário pabx iniciar os serviços de tarefa do NanoSip sem senha." > "$BASE_DIR/config/nanosip_sudoers"
echo "nanosip ALL=(root) NOPASSWD: /bin/systemctl start nanosip-admin@*.service, /usr/sbin/asterisk" >> "$BASE_DIR/config/nanosip_sudoers"

ln -sf "$BASE_DIR/config/nanosip_sudoers" "/etc/sudoers.d/nanosip_sudoers"
visudo -c -f /etc/sudoers.d/nanosip_sudoers
chown root:root "$BASE_DIR/config/nanosip_sudoers"


echo "[2/4] Configurando serviços do systemd..."
ln -sf "$BASE_DIR/config/nanosip.service" "/etc/systemd/system/nanosip.service"
ln -sf "$BASE_DIR/config/nanosip-dmin@.service" "/etc/systemd/system/nanosip-admin@.service"

echo "[3/4] Instalando dependências do sistema (jq)..."
apt-get update > /dev/null
apt-get install -y jq > /dev/null
echo "Dependências instaladas."

echo "[4/4] Recarregando e ativando os serviços..."
systemctl daemon-reload
systemctl enable asterisk.service
systemctl restart asterisk.service
systemctl enable nanosip.service
systemctl restart nanosip.service
echo "Serviço principal 'nanosip.service' ativado e iniciado."

echo ""
echo "--- SETUP CONCLUÍDO! ---"
echo "Para verificar o status da aplicação, use: sudo systemctl status nanosip.service"

