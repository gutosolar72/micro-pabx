#!/bin/bash

# ==============================================================================
#   SCRIPT DE RESET DA REDE (Versão Segura)
#
#   Este script é projetado para ser executado pelo usuário 'admin' via sudo.
#   Ele não contém 'sudo' internamente; as permissões são gerenciadas
#   pelo arquivo /etc/sudoers.d/admin_network_reset.
#
# ==============================================================================

echo "--- Iniciando Reset da Configuração de Rede ---"
interface=`ip -o link show | awk -F': ' '{print $2}' | grep -vE 'lo|wlan' | head -n 1`

# Define o conteúdo padrão para /etc/network/interfaces 
CONFIG="auto lo
iface lo inet loopback

auto $interface
iface $interface inet dhcp
"

# 1. Sobrescreve o arquivo /etc/network/interfaces.
# Como o script inteiro será executado com 'sudo', o redirecionamento '>' terá permissão.
echo "$CONFIG" > /etc/network/interfaces
echo "-> Arquivo /etc/network/interfaces redefinido."

# 2. Reinicia o serviço de rede para aplicar as alterações.
echo "-> Reiniciando o serviço de rede..."
systemctl restart networking.service

echo ""
echo "--- Reset de Rede Concluído! ---"
echo "Verifique abaixo o IP atribuido por DHCP ao NanoSIP"
sleep 5
ip -4 -o addr show up scope global | awk '{print $4}' | cut -d/ -f1
