#!/bin/bash

# Garante que o script pare se algum comando falhar
set -e

echo "################# Instalando dependências ###############################"
echo ""
apt-get install -y build-essential libedit-dev uuid-dev libjansson-dev libxml2-dev libsqlite3-dev subversion virtualenv sudo

useradd -m nanosip

useradd -r -s /bin/false --no-create-home asterisk

echo "alias vim='vim.tiny'" >> /root/.bashrc
echo "alias vim='vim.tiny'" >> /home/nanosip/.bashrc
echo "alias vim='vim.tiny'" >> /home/admin/.bashrc

# Navega para o diretório de fontes
cd /usr/src/

echo "################# Baixando e descompactando o Asterisk ##################"
echo ""
# Descomente a linha abaixo se precisar baixar o arquivo
wget http://downloads.asterisk.org/pub/telephony/asterisk/asterisk-18-current.tar.gz
tar -xvzf asterisk-18-current.tar.gz

cd asterisk-18.*/

echo "################# Configurando o Asterisk ###############################"
echo ""
./configure --with-jansson-bundled

echo "################# Compilando a ferramenta menuselect ####################"
echo ""
make menuselect.makeopts

echo "################# Desabilitando módulos desnecessários ##################"
echo ""
./menuselect/menuselect --disable res_pjproject --disable chan_pjsip menuselect.makeopts 

echo "################# Compilando e instalando o Asterisk ####################"
echo ""
make
make install
make samples

echo "################# Alterando usuarios do asterisk ########################"
echo ""
sed -i "/;runuser/runuser/" /etc/asterisk/asterisk.conf
sed -i "/;rungroup/rungroup/" /etc/asterisk/asterisk.conf

echo "################# Setando Permissões do Asterisk ########################"
echo ""
chown -R asterisk:asterisk /var/log/asterisk
chown -R asterisk:asterisk /var/spool/asterisk
chown -R asterisk:asterisk /var/lib/asterisk
chown -R asterisk:asterisk /etc/asterisk

echo "################# Criando Systemd Asterisk ##############################"
echo ""
cat << EOF > /etc/systemd/system/asterisk.service
[Unit]
Description=Asterisk

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/asterisk start -q
ExecStop=/usr/sbin/asterisk stop -q

[Install]
WantedBy=multi-user.target
EOF
# ==============================================

systemctl enable asterisk.service
systemctl start asterisk.service

chown -R nanosip:nanosip /opt/nanosip
#exec /opt/nanosip/setup.sh
