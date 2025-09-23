#!/bin/bash
set -e # Para o script se qualquer comando falhar

# Script central para todas as operações que exigem sudo
cd "$(dirname "$0")"
PYTHON_EXEC="./venv/bin/python3"

# O primeiro argumento ($1) define a ação a ser tomada
ACTION=$1

case $ACTION in
    "apply_config")
        echo "--- Aplicando configurações do PABX ---"
        $PYTHON_EXEC reload_queues.py
        $PYTHON_EXEC reload_sip.py
        asterisk -rx "core reload" > /dev/null 2>&1
        echo "--- Configurações aplicadas com sucesso! ---"
        ;;

    "get_network_info")
        echo "--- Obtendo informações de rede ---"
        $PYTHON_EXEC get_network_info.py
        ;;

    "update_network_config")
        echo "--- Atualizando configuração de rede ---"
        # $2 é o conteúdo do 'interfaces', $3 é o 'resolv.conf', $4 é a interface
        $PYTHON_EXEC update_network_files.py "$2" "$3"
        /sbin/ifdown "$4" && /sbin/ifup "$4"
        echo "--- Configuração de rede aplicada! ---"
        ;;

    *)
        echo "Erro: Ação desconhecida '$ACTION'"
        exit 1
        ;;
esac

exit 0

