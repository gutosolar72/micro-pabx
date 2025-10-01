#!/usr/bin/env python3
# update_network_files.py
import sys
import os
from pathlib import Path # Módulo moderno e orientado a objetos para lidar com caminhos de arquivo

def main():
    """
    Recebe o conteúdo dos arquivos 'interfaces' e 'resolv.conf' como argumentos,
    limpa o diretório /etc/network/interfaces.d/ para evitar conflitos,
    e escreve os novos arquivos de configuração. Este script deve ser rodado com sudo.
    """
    if len(sys.argv) != 3:
        print("Erro: Uso incorreto. São necessários 2 argumentos.", file=sys.stderr)
        sys.exit(1)

    interfaces_content = sys.argv[1]
    resolv_content = sys.argv[2]

    interfaces_d_path = Path("/etc/network/interfaces.d/")

    try:
        # --- INÍCIO DA MODIFICAÇÃO ---

        # 1. Limpa o diretório de configuração modular para evitar conflitos.
        # Verifica se o diretório existe antes de tentar fazer algo nele.
        if interfaces_d_path.is_dir():
            print(f"Limpando o diretório {interfaces_d_path}...")
            # Itera sobre todos os itens dentro do diretório
            for item in interfaces_d_path.iterdir():
                # Garante que estamos lidando apenas com arquivos, não subdiretórios
                if item.is_file():
                    try:
                        item.unlink() # O método .unlink() remove o arquivo
                        print(f"  - Removido: {item.name}")
                    except Exception as e:
                        print(f"  - Erro ao remover {item.name}: {e}", file=sys.stderr)
        
        # --- FIM DA MODIFICAÇÃO ---

        # 2. Escreve o arquivo de interfaces de rede
        print("Escrevendo /etc/network/interfaces...")
        with open('/etc/network/interfaces', 'w') as f:
            f.write(interfaces_content)

        # 3. Escreve o arquivo de configuração de DNS
        print("Escrevendo /etc/resolv.conf...")
        with open('/etc/resolv.conf', 'w') as f:
            f.write(resolv_content)

        print("Arquivos de rede atualizados com sucesso.")
        sys.exit(0)

    except Exception as e:
        print(f"Erro ao escrever arquivos de sistema: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
