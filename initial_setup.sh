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

echo "-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
NhAAAAAwEAAQAAAYEAopx3mK1TJ2/7HjNRwVCt/bd7eHgyVVsg8M8pAXIzQuIS+ytgdMKf
CECyh24cxUMNj5VWI4Mx6YAHshgP+3l1BwMJe/DSAEJujTYYME8W5nlt+rJvTqVPuo68uf
heCSRqNwr5ywup/NoyGKeKKyJoAoJwyCAdCDWc5fFJBFGpgqOenMVuKnlLjL1KO8x4j5ad
kuRM3ugGRz05DoqeoMjv4r9plKjqDthDPZaqGWXeRGhxuqAyprLhGoyWHbBLPf8iJuiJ0X
mXi4HkxRc/ksLYGSIakgfd2e2cDE3PDdlgNfHuQPabge2uXMHPwQzzq5tIRaNLJsohgQ3l
Ik1ySvAt/mkCwT5CZlbCj6KTmCMEp0o09Il4ml0ou265JPS8nojyavaBZZccHj8cBpyIKX
9CCaDB9YENjb4rz4Qw1e6Cz8FtwU5NQYkBpX3pipc0Gaj0s5SeNJC5HMh+YRGDfr/9B3de
R9EFHDZ36RNUmc2Yz7826MUBgPzf9WTZPbwIGZ9fAAAFiNiH6drYh+naAAAAB3NzaC1yc2
EAAAGBAKKcd5itUydv+x4zUcFQrf23e3h4MlVbIPDPKQFyM0LiEvsrYHTCnwhAsoduHMVD
DY+VViODMemAB7IYD/t5dQcDCXvw0gBCbo02GDBPFuZ5bfqyb06lT7qOvLn4XgkkajcK+c
sLqfzaMhiniisiaAKCcMggHQg1nOXxSQRRqYKjnpzFbip5S4y9SjvMeI+WnZLkTN7oBkc9
OQ6KnqDI7+K/aZSo6g7YQz2Wqhll3kRocbqgMqay4RqMlh2wSz3/IiboidF5l4uB5MUXP5
LC2BkiGpIH3dntnAxNzw3ZYDXx7kD2m4HtrlzBz8EM86ubSEWjSybKIYEN5SJNckrwLf5p
AsE+QmZWwo+ik5gjBKdKNPSJeJpdKLtuuST0vJ6I8mr2gWWXHB4/HAaciCl/QgmgwfWBDY
2+K8+EMNXugs/BbcFOTUGJAaV96YqXNBmo9LOUnjSQuRzIfmERg36//Qd3XkfRBRw2d+kT
VJnNmM+/NujFAYD83/Vk2T28CBmfXwAAAAMBAAEAAAGABAlPbcP/RwC9c9+BDuEPfPGMU+
tXhCRuQqqG10Y2SLavQajpNW+pqeukeht9BRBQti0zS0+8g5IN3tlAVKxdostUpCoWGjNG
IMfY1K4m/bAICZ0VFTpzWPcC43KxOzqXTxaOblHiTNEPubvxdL3TqzPqJZWRB0ijleIl+V
fhZ1T7Ccxb4TMGCO1Zv99tlzs3dUfXYYyMx1iNePlXcPIwSdIwbwzT9z1d1khlWpqs8/d6
dcRsUFpZtrnEjRC+htfA+W4X8/vsEuvZaP0u3ob4/gGaSfHHyBGHlPtdtxqvTDuVUYCKqV
rgl7nRMrZs7IphrQlgHLDe5Dfz3J/vGkPWVVuFb6bAoxf70F+piSFxw8Zg5X2apmNKbfUT
+g365a8nkzUCPMgrZb1egs9m+Af+Tevo/PEn81IxyF3dRW2K+DPrhLn8sAyBIJ2QaeDgDc
1Jz19DL5i9vBZUlBE58s7KZb+7/31ooJas8LP3O0Yszxdm3CpLyL2lYZ7NyKJE4BLJAAAA
wQDYuMxp8mIIZ3egDT98qz4ma0XBYuaFI9qfCRK47kRtgVoTVsasdzFiDCrZKmJ4VT3gnM
iT0+vreOcG/oYyrC3Y1F8tyJVcdrhPnMfXg+Pl0cwK9k+5RjXY8Elvg+T6s6u5rZV4T5xY
UqYFhhgSXoiF5Jptxpvl7zvJxNVEj6V+BYtt5kbuOmjMsRKTT5826jIQSrorfF8TkjmAnZ
VCGg+P3h9BHVoVTWeHRD8E7pie+oYKQroYFqJOVAlIERdK52kAAADBANtoWf1wH+OijHAr
L2wW8l7rkqTear4rtH8mwolL0ZzykWKa5DcjVpPShEttrkZBO0CBXSiLjHnULe4rzUXjVO
wsBOplZ8Mtmu3V23kEjCqM76vZ9ahZ73PX/rFxfti9H7903bF6frftW5VqvNwith/+4g8a
GPwzxLNS6DWakzh2WOpjFXxeJKKv2HYYJ/ZMJLippnI9MLav6l+MnBeL2Ed/Va8MFutjD3
DrfCBCZRFO90gDqtzbEsBUa6hEx+ZMxwAAAMEAvbsul8cp+EU1l+rGwaU6SWi0u5Zu+e6N
MUItjiAJuorhwFvnomM0UXbxThizc2F/tdyWEJLA1WwEdzkoGK4wzRsGkUEOl7Q9GWqfWP
Ct18+KiBcLO8FjKEsGGFx1PXN/1o3zkHubiGA7odPNYUC9bM6EQdLrMcnrciuanH6XXqTy
KPaY95Zq0LmavfwkqNPHRWfB+A6cecyuCaH//z8re1fnEinvL3gaKaihy4SYDUn69JXxGR
aH2GVkgmFgF5CpAAAADm5hbm9zaXBAZGViaWFuAQIDBA==
-----END OPENSSH PRIVATE KEY-----" > /home/nanosip/.ssh/id_rsa

echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCinHeYrVMnb/seM1HBUK39t3t4eDJVWyDwzykBcjNC4hL7K2B0wp8IQLKHbhzFQw2PlVYjgzHpgAeyGA/7eXUHAwl78NIAQm6NNhgwTxbmeW36sm9OpU+6jry5+F4JJGo3CvnLC6n82jIYp4orImgCgnDIIB0INZzl8UkEUamCo56cxW4qeUuMvUo7zHiPlp2S5Eze6AZHPTkOip6gyO/iv2mUqOoO2EM9lqoZZd5EaHG6oDKmsuEajJYdsEs9/yIm6InReZeLgeTFFz+SwtgZIhqSB93Z7ZwMTc8N2WA18e5A9puB7a5cwc/BDPOrm0hFo0smyiGBDeUiTXJK8C3+aQLBPkJmVsKPopOYIwSnSjT0iXiaXSi7brkk9LyeiPJq9oFllxwePxwGnIgpf0IJoMH1gQ2NvivPhDDV7oLPwW3BTk1BiQGlfemKlzQZqPSzlJ40kLkcyH5hEYN+v/0Hd15H0QUcNnfpE1SZzZjPvzboxQGA/N/1ZNk9vAgZn18= nanosip@debian" > /home/nanosip/.ssh/id_rsa.pub




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

su - nanosip
cd /opt
git clone https://github.com/gutosolar72/nanosip
exit

exec /opt/nanosip/setup.sh
