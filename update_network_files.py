#!/usr/bin/env python3
# update_network_files.py
import sys

def main():
    """
    Recebe o conteúdo dos arquivos 'interfaces' e 'resolv.conf' como argumentos
    e os escreve em /etc/. Este script deve ser rodado com sudo.
    """
    if len(sys.argv) != 3:
        print("Erro: Uso incorreto. São necessários 2 argumentos.", file=sys.stderr)
        sys.exit(1)

    interfaces_content = sys.argv[1]
    resolv_content = sys.argv[2]

    try:
        # Escreve o arquivo de interfaces de rede
        with open('/etc/network/interfaces', 'w') as f:
            f.write(interfaces_content)
        
        # Escreve o arquivo de configuração de DNS
        with open('/etc/resolv.conf', 'w') as f:
            f.write(resolv_content)
        
        print("Arquivos de rede atualizados com sucesso.")
        sys.exit(0)

    except Exception as e:
        print(f"Erro ao escrever arquivos de sistema: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

