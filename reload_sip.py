import os
import subprocess
from database import get_ramais, get_localnets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'micro_pbx.db')

SIP_CONF = "/etc/asterisk/sip.conf"

def gerar_sip_conf():
    with open(SIP_CONF, "w") as f:
        # Cabeçalho
        f.write("[general]\n")
        f.write("context=default\n")
        f.write("allowguest=no\n")
        f.write("srvlookup=no\n")
        f.write("udpbindaddr=0.0.0.0\n")
        f.write("tcpenable=no\n")

        # Localnets vindos do banco
        localnets = get_localnets()
        for net in localnets:
            f.write(f"localnet={net['localnet']}\n")

        f.write("\n")

        # Ramais
        ramais = get_ramais()
        for r in ramais:
            f.write(f"[{r['ramal']}]\n")
            f.write("type=friend\n")
            f.write(f"username={r['ramal']}\n")
            f.write(f"secret={r['senha']}\n")
            f.write("host=dynamic\n")
            f.write(f"context={r['contexto']}\n")
            f.write("nat=no\n")
            f.write("qualify=yes\n\n")

def reload_sip():
    gerar_sip_conf()
    subprocess.run(["asterisk", "-rx", "sip reload"])

if __name__ == "__main__":
    reload_sip()

