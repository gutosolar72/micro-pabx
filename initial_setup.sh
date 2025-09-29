#!/bin/bash

# Setup Inicial do Nanosip -- Rodar como root
set -e
apt-get update
apt-get upgrade
apt install -y build-essential subversion virtualenv git sudo

useradd admin
echo "nanosip" | passwd --stdin username

useradd -r -s /bin/false --no-create-home asterisk
useradd nanosip

su - nanosip
mkdir -p /home/nanosip/.ssh

# INSTALANDO PACOTES NECESSÁRIOS
#INSTALANDO O ASTERISK

cd /usr/src/
wget http://downloads.asterisk.org/pub/telephony/asterisk/asterisk-18-current.tar.gz
tar -xvzf asterisk-18-current.tar.gz
apt-get install libedit-dev uuid-dev libjansson-dev libxml2-dev libsqlite3-dev
./configure --with-jansson-bundled
make
make install
make samples

sed -i "/;runuser/runuser/" /etc/asterisk/asterisk.conf
sed -i "/;rungroup/rungroup/" /etc/asterisk/asterisk.conf

# ============= Systemd Asterisk =============
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

exec /opt/nanosip/setup.sh
