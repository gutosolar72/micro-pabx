import os
import subprocess
from database import get_ramais, get_localnets
from licenca import get_modulos_override

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'nanosip.db')

MODULOS = get_modulos_override()
video_chamada = 'video' in MODULOS.lower().split(',')

SIP_CONF = "/etc/asterisk/sip.conf"

def gerar_sip_conf():
    with open(SIP_CONF, "w") as f:
        # Cabeçalho
        f.write("[general]\n")
        f.write("language=pt_BR\n")
        f.write("externip=193.186.4.201\n")
        f.write("bindport=5060\n")
        f.write("useragent=asterisk\n")
        f.write("bindaddr=0.0.0.0\n")
        f.write("context=default\n")
        f.write("disallow=all\n")
        f.write("allow=alaw,ulaw,h264\n")
        if video_chamada:
            f.write("videosupport=yes\n")
        f.write("maxexpirey=3600\n")
        f.write("canreinvite=no\n")
        f.write("defaultexpirey=3600\n")

        # Localnets vindos do banco
        localnets = get_localnets()
        for net in localnets:
            f.write(f"localnet={net['localnet']}\n")

        f.write("\n")
        f.write("#include \"sip_custom.conf\"")
        f.write("\n")

        # Ramais
        ramais = get_ramais()
        for r in ramais:
            f.write(f"[{r['ramal']}]\n")
            f.write("type=friend\n")
            f.write(f"username={r['ramal']}\n")
            f.write(f"callerid=\"{r['nome']}\" <{r['ramal']}>\n")
            f.write(f"secret={r['senha']}\n")
            f.write("host=dynamic\n")
            f.write(f"context={r['contexto']}\n")
            f.write("nat=no\n")
            f.write("qualify=yes\n\n")

if __name__ == "__main__":
    gerar_sip_conf()

