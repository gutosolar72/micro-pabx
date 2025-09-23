import socket, subprocess
from config_rede import carrega_config

def get_system_info():
    info = {}
    network = carrega_config()
    info["hostname"] = network["hostname"]
    info["ip_atual"] = network["ip_atual"]
    info["netmask"] = network["netmask"]
    info["gateway"] = network["gateway"]
    info["dns"] = network["dns"]

    try:
        versao = subprocess.check_output("asterisk -V", shell=True).decode().strip()
        info["versao_asterisk"] = versao
    except:
        info["versao_asterisk"] = "Asterisk não encontrado"

    ramais = subprocess.check_output("asterisk -rx 'sip show peers' | grep Monitored | awk -F':' '{print $2}' | awk -F'U' '{print $1}'", shell=True).decode().strip()
    info["ramais_cadastrados"] = ramais
    #except:
    #    info["ramais_cadastrados"] = ramais    
    return info

