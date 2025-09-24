#!/usr/bin/env python3
# get_network_info.py (v2 - Usando o comando 'ip')
import subprocess
import json
import sys
import re

def main():
    """
    Coleta informações de rede usando os comandos 'ip addr' e 'ip route'.
    Este script é projetado para ser chamado com sudo.
    """
    network_info = {
        "iface": None,
        "gateway": None,
        "ip_atual": None,
        "netmask": None
    }
    try:
        # 1. Obter o gateway padrão e a interface principal
        route_output = subprocess.check_output(["ip", "route"], text=True)
        default_route_line = [line for line in route_output.splitlines() if line.startswith('default')]
        if not default_route_line:
            raise Exception("Não foi possível encontrar a rota padrão (default gateway).")
        
        parts = default_route_line[0].split()
        network_info["gateway"] = parts[2]
        network_info["iface"] = parts[4]
        
        # 2. Obter o IP e a máscara da interface encontrada
        addr_output = subprocess.check_output(["ip", "addr", "show", network_info["iface"]], text=True)
        inet_line = [line for line in addr_output.splitlines() if "inet " in line.strip()]
        if not inet_line:
            raise Exception(f"Não foi possível encontrar um endereço IPv4 na interface {network_info['iface']}.")
        
        # Extrai o IP e o CIDR (ex: 192.168.1.10/24)
        ip_cidr = inet_line[0].strip().split()[1]
        ip, cidr = ip_cidr.split('/')
        network_info["ip_atual"] = ip
        
        # Converte o CIDR (/24) para uma máscara de rede (255.255.255.0)
        cidr = int(cidr)
        mask = (0xffffffff << (32 - cidr)) & 0xffffffff
        network_info["netmask"] = '.'.join([str((mask >> i) & 0xff) for i in [24, 16, 8, 0]])

        print(json.dumps(network_info))
        sys.exit(0)

    except Exception as e:
        error_output = {"error": str(e)}
        print(json.dumps(error_output), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

