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

	if [ -z "$HOSTNAME_CONTENT" ]; then
    		echo "ERRO: Não foi possível ler o hostname do arquivo temporário."
    		exit 1
	fi

	echo "$INTERFACES_CONTENT" > /etc/network/interfaces
	echo "$RESOLV_CONTENT" > /etc/resolv.conf

	hostnamectl set-hostname "$HOSTNAME_CONTENT"
 

	# Ajustando o hosts 
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

