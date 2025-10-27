#!/bin/bash

# ==============================================================================
#
#   SCRIPT DE INSTALAÇÃO COMPLETO - ASTERISK & NANOSIP
#
#   Este script deve ser executado como root.
#   Ele irá:
#   1. Instalar todas as dependências de sistema.
#   2. Criar os usuários 'asterisk' e 'nanosip'.
#   3. Baixar e compilar a versão 18 do Asterisk.
#   4. Verificar e reparar a instalação do Python se corrompida pela compilação.
#   5. Configurar e iniciar o Asterisk como um serviço.
#   6. Configurar e iniciar os serviços do Nanosip.
#
# ==============================================================================


# --- CONFIGURAÇÃO INICIAL E FUNÇÃO DE REPARO ---

# Garante que o script pare se algum comando falhar
set -e

# Verifica se o script está sendo executado como root
if [ "$(id -u)" -ne 0 ]; then
  echo "ERRO: Este script precisa ser executado como root. Por favor, use 'sudo bash $0'" >&2
  exit 1
fi

# Função de Verificação e Reparo do Python
check_and_repair_python() {
    echo "################# Verificando a integridade do Python #################"
    if ! python3 --version &> /dev/null; then
        echo "AVISO: O comando 'python3' está quebrado. Iniciando reparo automático..."
        local PY_VERSION_FULL=$( (dpkg-query -W -f='${Version}' python3 || apt-cache policy python3 | grep 'Installed:' | awk '{print $2}') | head -n 1)
        local PY_MAJOR_VERSION=$(echo $PY_VERSION_FULL | cut -d. -f1,2)
        local PY_MINIMAL_PKG="python${PY_MAJOR_VERSION}-minimal"
        if [ -z "$PY_MAJOR_VERSION" ]; then echo "ERRO CRÍTICO: Não foi possível determinar a versão do Python."; exit 1; fi
        echo "Pacote a ser reparado: ${PY_MINIMAL_PKG}"
        rm -f /usr/bin/python /usr/bin/python3 "/usr/bin/python${PY_MAJOR_VERSION}"
        apt-get install --reinstall -y "${PY_MINIMAL_PKG}"
        ln -sf "/usr/bin/python${PY_MAJOR_VERSION}" /usr/bin/python3
        ln -sf /usr/bin/python3 /usr/bin/python
        if python3 --version &> /dev/null; then echo "SUCESSO: Python reparado."; python3 --version; else echo "ERRO CRÍTICO: Reparo do Python falhou."; exit 1; fi
    else
        echo "Python está funcional. Nenhuma ação necessária."
    fi
}


# ==============================================================================
#   PARTE 1: INSTALAÇÃO DE DEPENDÊNCIAS E ASTERISK
# ==============================================================================

echo "--- [PARTE 1/3] Iniciando Instalação do Asterisk e Dependências ---"

echo "################# Atualizando pacotes e instalando dependências ###############################"
apt-get update

#apt-get install -y wget build-essential libedit-dev uuid-dev libjansson-dev libxml2-dev libsqlite3-dev subversion virtualenv sudo python3 jq libcurl4-openssl-dev reportbug sngrep tcpdump

cd /usr/src
wget https://www.python.org/ftp/python/3.11.10/Python-3.11.10.tgz
tar xvf Python-3.11.10.tgz
cd Python-3.11.10
./configure --enable-optimizations --with-ensurepip=install
make -j$(nproc)
make altinstall

apt-get install -y wget build-essential libedit-dev uuid-dev libxml2-dev libsqlite3-dev subversion sudo jq libcurl4-openssl-dev reportbug sngrep tcpdump

# configurando Time zone
timedatectl set-timezone America/Sao_Paulo

echo "################# Criando usuários do sistema #################################"
# Cria o usuário nanosip se ele não existir
useradd -m -s /bin/bash nanosip
echo "Usuário 'nanosip' criado."

# Cria o usuário nanosip se ele não existir
useradd -m -s /bin/bash admin
echo "Usuário 'admin' criado."
chpasswd <<<"admin:nanosip"

useradd -r -s /bin/false --no-create-home asterisk
echo "Usuário 'asterisk' criado."

usermod -aG sudo,systemd-journal,netdev,asterisk nanosip

echo "################# Configurando aliases convenientes ###########################"
echo "alias vim='vim.tiny'" | tee -a /root/.bashrc > /dev/null

echo "alias vim='vim.tiny'" >> /home/nanosip/.bashrc
chown nanosip:nanosip /home/nanosip/.bashrc

echo "######### Configurando script de reset network #########"
chmod +x /opt/nanosip/config/reset_network.sh
chown admin:admin /opt/nanosip/config/reset_network.sh

echo "alias reset_network='sudo /opt/nanosip/config/reset_network.sh'" >> /home/admin/.bashrc
  
echo "Configurando permissões de sudo para o script de reset..."
cat << EOF > /etc/sudoers.d/admin_network_reset
# Permite ao usuário 'admin' executar o script de reset de rede sem senha.
admin ALL=(root) NOPASSWD: /opt/nanosip/config/reset_network.sh
EOF
chmod 440 /etc/sudoers.d/admin_network_reset
visudo -c -f /etc/sudoers.d/admin_network_reset

echo "Configuração do usuário 'admin' e do script de reset concluída."

# Navega para o diretório de fontes
cd /usr/src/

echo "################# Baixando e descompactando o jansson ##################"
if [ ! -d "jansson-2.14" ]; then
wget -q https://gerenciamento.nanosip.com.br/static/src/jansson-2.14.tar.gz
tar -xzf jansson-2.14.tar.gz
    cd jansson-2.14
    ./configure
    make
    make install
    cd ..
fi
echo "################# Baixando e descompactando o pjproject ##################"
if [ ! -d "pjproject-2.14" ]; then
    wget -q https://gerenciamento.nanosip.com.br/static/src/pjproject-2.14.tar.bz2
    tar -xjf pjproject-2.14.tar.bz2
    cd pjproject-2.14
    ./configure
    make dep
    make
    make install
    cd ..
fi

echo "################# Baixando e descompactando o Asterisk ##################"
if [ ! -f "asterisk-18-current.tar.gz" ]; then
    wget https://gerenciamento.nanosip.com.br/static/src/asterisk-18-current.tar.gz
    tar -xvzf asterisk-18-current.tar.gz

    cd asterisk-18.*/

    echo "################# Configurando, compilando e instalando o Asterisk ####################"
    ./configure
    make
    make install
    make samples
    make config
fi


# Chamada da função de reparo do Python
check_and_repair_python

echo "################# Configurando permissões e serviço do Asterisk ########################"
#sed -i 's/;runuser = asterisk/runuser = asterisk/' /etc/asterisk/asterisk.conf
#sed -i 's/;rungroup = asterisk/rungroup = asterisk/' /etc/asterisk/asterisk.conf
chown -R asterisk:asterisk /var/log/asterisk /var/spool/asterisk /var/lib/asterisk /etc/asterisk

ln -s /opt/nanosip/config/asterisk.service /etc/systemd/system/asterisk.service
mkdir -p /var/run/asterisk
chown asterisk:asterisk /var/run/asterisk
sed -i 's/^usegmtime=yes/usegmtime=no/' /etc/asterisk/cdr.conf

# Desabilitando modulos desnecessarios do asterisk
sed -i 's/noload = chan_sip.so/;noload = chan_sip.so/' /etc/asterisk/modules.conf
cat /opt/nanosip/config/asterisk_modules >> /etc/asterisk/modules.conf
mkdir -p /etc/asterisk/sip_custom.conf
mkdir -p /etc/asterisk/extensions_custom.conf
chown asterisk:asterisk /etc/asterisk/sip_custom.conf
chown  asterisk:asterisk /etc/asterisk/extensions_custom.conf
rm /var/lib/asterisk/moh/macroform-robot_dity.wav


systemctl daemon-reload
systemctl enable asterisk
systemctl restart asterisk
ldconfig
echo "--- [PARTE 1/3] Instalação do Asterisk Concluída ---"
echo ""


# ==============================================================================
#   PARTE 2: CONFIGURAÇÃO DO AMBIENTE PYTHON DO NANOSIP
# ==============================================================================

echo "--- [PARTE 2/3] Configurando Ambiente Python do Nanosip ---"

# Pega o caminho absoluto do diretório onde o Nanosip está (assumindo /opt/nanosip )
BASE_DIR="/opt/nanosip"
VENV_DIR="$BASE_DIR/venv"

if [ ! -d "$BASE_DIR" ]; then
    echo "ERRO: O diretório do Nanosip ($BASE_DIR) não foi encontrado."
    exit 1
fi

echo "Configurando permissões para o diretório Nanosip..."
chown -R nanosip:nanosip "$BASE_DIR"

echo "Criando ambiente virtual Python em $VENV_DIR..."
# Executa a criação do virtualenv como o usuário 'nanosip'
su - nanosip -c "/usr/local/bin/python3.11 -m venv $VENV_DIR"

echo "Instalando dependências Python no ambiente virtual..."
# Executa a instalação dos pacotes como 'nanosip'
su - nanosip -c "source $VENV_DIR/bin/activate && pip install -r $BASE_DIR/requirements.txt"

echo "--- [PARTE 2/3] Ambiente Python Concluído ---"
echo ""


# ==============================================================================
#   PARTE 3: CONFIGURAÇÃO DOS SERVIÇOS DO NANOSIP
# ==============================================================================

echo "--- [PARTE 3/3] Configurando Serviços do Nanosip ---"

echo "[1/4] Configurando permissões do sudoers..."
# Cria o arquivo de configuração do sudoers
cat << EOF > /etc/sudoers.d/nanosip_sudoers
# Permite ao usuário nanosip gerenciar serviços e o Asterisk sem senha.
nanosip ALL=(root) NOPASSWD: /bin/systemctl start nanosip-admin@*.service
nanosip ALL=(root) NOPASSWD: /usr/sbin/asterisk -rx *
nanosip ALL=(root) NOPASSWD: /opt/nanosip/system_manager.sh *
EOF
# Valida e define as permissões corretas para o arquivo sudoers
visudo -c -f /etc/sudoers.d/nanosip_sudoers
chmod 440 /etc/sudoers.d/nanosip_sudoers
chown root:root /etc/sudoers.d/nanosip_sudoers
ln -s /opt/nanosip/config/nanosip_cron /etc/cron.d/nanosip
chmod 644 /etc/cron.d/nanosip

# Ajustando o hosts para não dar pau no sudo
HOSTNAME=$(hostname)
TARGET_LINE="127.0.1.1\t${HOSTNAME}"
echo -e "${TARGET_LINE}" >> /etc/hosts

echo "[2/4] Configurando serviços do systemd..."
ln -sf "$BASE_DIR/config/nanosip.service" "/etc/systemd/system/nanosip.service"
ln -sf "$BASE_DIR/config/nanosip-admin@.service" "/etc/systemd/system/nanosip-admin@.service"

echo "[3/4] Recarregando e ativando os serviços..."
systemctl daemon-reload
systemctl enable nanosip.service
systemctl restart nanosip.service

echo "[4/4] Setando as configurações iniciais de rede..."
interface=`ip -o link show | awk -F': ' '{print $2}' | grep -vE 'lo|wlan' | head -n 1`
cat << EOF > /etc/network/interfaces
# Arquivo gerado pelo Micro PABX
auto lo
iface lo inet loopback

auto $interface
iface $interface inet static
    address 172.16.0.10
    netmask 255.255.255.0
    gateway 172.16.0.10
EOF

cat "$BASE_DIR/config/05-nanosip-info" > /etc/update-motd.d/05-nanosip-info
chmod -x /etc/update-motd.d/10-uname
echo "" > /etc/motd

cp "$BASE_DIR/config/nanosip_logrotate" /etc/logrotate.d/

echo "=============================================================================="
echo "--- SETUP GERAL CONCLUÍDO! ---"
echo "Para verificar o status da aplicação, use: sudo systemctl status nanosip.service"
echo "Para verificar o status do Asterisk, use: sudo systemctl status asterisk.service"
echo "=============================================================================="

