#!/bin/bash
set -e

# Garante que o script rode a partir do seu próprio diretório
cd "$(dirname "$0")"
PYTHON_EXEC="./venv/bin/python3"
ACTION=$1

echo "--- Executando tarefa: $ACTION (rodando como $USER) ---"

case $ACTION in
    "apply_config")
        echo "[1/4] Gerando plano de discagem (extensions.conf)..."
        $PYTHON_EXEC reload_extensions.py

        echo "[2/4] Gerando filas (queues.conf)..."
        $PYTHON_EXEC reload_queues.py

        echo "[3/4] Gerando ramais (sip.conf)..."
        $PYTHON_EXEC reload_sip.py

        echo "[4/4] Recarregando Asterisk..."
        # Usamos 'core reload' para aplicar todas as mudanças de uma vez
        /usr/sbin/asterisk -rx "core reload" > /dev/null 2>&1
        ;;

    "get_network_info")
        $PYTHON_EXEC get_network_info.py
        ;;

    "update_network_config")
        # Lê os dados do arquivo temporário criado pelo Flask
        TMP_FILE="/tmp/nanosip_net_config.json"
        if [ ! -f "$TMP_FILE" ]; then
            echo "Erro: Arquivo de configuração temporário não encontrado." >&2
            exit 1
        fi

        # Extrai os dados usando 'jq'
        # Garanta que o jq esteja instalado: sudo apt-get install jq -y
        INTERFACES_CONTENT=$(jq -r '.interfaces' "$TMP_FILE")
        RESOLV_CONTENT=$(jq -r '.resolv' "$TMP_FILE")
        IFACE=$(jq -r '.iface' "$TMP_FILE")
        HOSTNAME_CONTENT=$(jq -r '.hostname' "$TMP_FILE")

        # Escreve os arquivos de configuração
        echo "$INTERFACES_CONTENT" > /etc/network/interfaces
        echo "$RESOLV_CONTENT" > /etc/resolv.conf
        echo "$HOSTNAME_CONTENT" > /etc/hostname
        echo "$HOSTNAME_CONTENT" > /proc/sys/kernel/hostname
        sed -i "1s/.*/127.0.0.1       localhost $HOSTNAME_CONTENT/" /etc/hosts 
        sed -i "2s/.*/127.0.1.1       $HOSTNAME_CONTENT/" /etc/hosts
       

        # Aplica as configurações
        echo "Aplicando configurações de rede para a interface $IFACE..."
        /sbin/ifdown "$IFACE" && /sbin/ifup "$IFACE"

        # Limpa o arquivo temporário
        rm "$TMP_FILE"
        ;;
    *)
        echo "Erro: Ação desconhecida '$ACTION'" >&2
        exit 1
        ;;
esac

echo "--- Tarefa '$ACTION' concluída com sucesso. ---"
exit 0

