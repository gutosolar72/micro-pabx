#!/bin/bash
set -e

BASE_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$BASE_DIR"

PYTHON_EXEC="${BASE_DIR}/venv/bin/python3"
ACTION=$1

# Mensagens de status são enviadas para a saída de erro (stderr)
echo "--- Executando tarefa: $ACTION (rodando como $USER) ---" >&2

case $ACTION in
    "apply_config")
        echo "[1/4] Gerando plano de discagem (extensions.conf)..." >&2
        $PYTHON_EXEC "${BASE_DIR}/reload_extensions.py"

        echo "[2/4] Gerando filas (queues.conf)..." >&2
        $PYTHON_EXEC "${BASE_DIR}/reload_queues.py"

        echo "[3/4] Gerando ramais (sip.conf)..." >&2
        $PYTHON_EXEC "${BASE_DIR}/reload_sip.py"

        echo "[4/4] Recarregando o Asterisk..." >&2
        /usr/sbin/asterisk -rx "core reload" > /dev/null 2>&1
        ;;

    "get_network_info")
        # A saída deste script (o JSON) é a única coisa enviada para a saída padrão (stdout)
        $PYTHON_EXEC "${BASE_DIR}/get_network_info.py"
        ;;

    "update_network_config")
        TMP_FILE="/tmp/nanosip_net_config.json"
        if [ ! -f "$TMP_FILE" ]; then
            echo "Erro: Arquivo de configuração temporário não encontrado." >&2
            exit 1
        fi

        INTERFACES_CONTENT=$(jq -r '.interfaces' "$TMP_FILE")
        RESOLV_CONTENT=$(jq -r '.resolv' "$TMP_FILE")
        IFACE=$(jq -r '.iface' "$TMP_FILE")
        HOSTNAME_CONTENT=$(jq -r '.hostname' "$TMP_FILE")

        if [ -z "$HOSTNAME_CONTENT" ]; then
            echo "ERRO: Não foi possível ler o hostname do arquivo temporário." >&2
            exit 1
        fi

        echo "$INTERFACES_CONTENT" > /etc/network/interfaces
        echo "$RESOLV_CONTENT" > /etc/resolv.conf
        hostnamectl set-hostname "$HOSTNAME_CONTENT"

        HOSTS_FILE="/etc/hosts"
        LINE_127_0_0_1="127.0.0.1\tlocalhost ${HOSTNAME_CONTENT}"
        if grep -q "^127\.0\.0\.1" "${HOSTS_FILE}"; then
            sed -i "/^127\.0\.0\.1/c\\${LINE_127_0_0_1}" "${HOSTS_FILE}"
        else
            echo -e "${LINE_127_0_0_1}" >> "${HOSTS_FILE}"
        fi

        LINE_127_0_1_1="127.0.1.1\t${HOSTNAME_CONTENT}"
        if grep -q "^127\.0\.1\.1" "${HOSTS_FILE}"; then
            sed -i "/^127\.0\.1\.1/c\\${LINE_127_0_1_1}" "${HOSTS_FILE}"
        else
            echo -e "${LINE_127_0_1_1}" >> "${HOSTS_FILE}"
        fi

        echo "Aplicando configurações de rede para a interface $IFACE..." >&2
        /sbin/ifdown "$IFACE" && /sbin/ifup "$IFACE"

        rm "$TMP_FILE"
        ;;
    *)
        echo "Erro: Ação desconhecida '$ACTION'" >&2
        exit 1
        ;;
esac

# A mensagem de sucesso final também vai para stderr
echo "--- Tarefa '$ACTION' concluída com sucesso. ---" >&2
exit 0
