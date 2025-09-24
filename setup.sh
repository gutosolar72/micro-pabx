#!/bin/bash

# Script de Setup para o Micro PABX
# Este script deve ser executado com 'sudo' (ex: sudo ./setup.sh)

# Garante que o script pare se qualquer comando falhar
set -e

# Pega o caminho absoluto do diretório onde o script está
BASE_DIR=$(cd "$(dirname "$0")" && pwd)

echo "--- Iniciando Setup do Micro PABX ---"

# --- Passo 1: Configuração do sudoers ---
echo "[1/4] Configurando permissões do sudoers..."
# Cria o link simbólico do nosso arquivo de sudoers para o diretório do sistema
# O 'ln -sf' força a criação do link, sobrescrevendo se já existir
ln -sf "$BASE_DIR/config/pabx_sudoers" "/etc/sudoers.d/pabx_permissions"
# Valida a sintaxe do arquivo que acabamos de linkar
visudo -c -f /etc/sudoers.d/pabx_permissions
echo "Permissões do sudoers configuradas."

# --- Passo 2: Configuração dos serviços systemd ---
echo "[2/4] Configurando serviços do systemd..."
# Cria os links simbólicos para os nossos arquivos de serviço
ln -sf "$BASE_DIR/config/micropabx.service" "/etc/systemd/system/micropabx.service"
ln -sf "$BASE_DIR/config/pabx-admin@.service" "/etc/systemd/system/pabx-admin@.service"
echo "Serviços do systemd configurados."

# --- Passo 3: Instalação de dependências ---
echo "[3/4] Instalando dependências do sistema (jq)..."
# Garante que o 'jq' (processador de JSON) esteja instalado
apt-get update > /dev/null
apt-get install -y jq > /dev/null
echo "Dependências instaladas."

# --- Passo 4: Ativação dos serviços ---
echo "[4/4] Recarregando e ativando os serviços..."
# Recarrega o systemd para que ele reconheça os novos links
systemctl daemon-reload
# Habilita o serviço principal para iniciar com o boot
systemctl enable micropabx.service
# Inicia (ou reinicia) o serviço principal agora
systemctl restart micropabx.service
echo "Serviço principal 'micropabx.service' ativado e iniciado."

echo ""
echo "--- SETUP CONCLUÍDO! ---"
echo "Para verificar o status da aplicação, use: sudo systemctl status micropabx.service"

