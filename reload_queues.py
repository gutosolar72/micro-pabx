# /opt/nanosip/reload_queues.py

from database import get_db # Usando a função centralizada

# --- Configurações ---
QUEUES_CONF_PATH = '/etc/asterisk/queues.conf'

# --- Funções de Acesso ao Banco de Dados ---

def get_all_filas():
    """Busca todas as filas (incluindo seus IDs) cadastradas no banco de dados."""
    db = get_db()
    filas_raw = db.execute("SELECT id, fila, nome FROM filas").fetchall()
    db.close()
    return [dict(row) for row in filas_raw]

def get_ramais_in_fila(fila_id):
    """Busca todos os ramais associados a uma fila específica pelo ID da fila."""
    db = get_db()
    # CORREÇÃO: A consulta agora usa a tabela 'ramal_fila' e faz JOIN com 'ramais'
    cursor = db.execute("""
        SELECT r.ramal
        FROM ramais r
        JOIN ramal_fila rf ON r.id = rf.ramal_id
        WHERE rf.fila_id = ?
    """, (fila_id,))
    ramais = cursor.fetchall()
    db.close()
    return [str(row['ramal']) for row in ramais]

# --- Lógica Principal ---

def generate_queues_conf():
    """Gera o conteúdo do arquivo queues.conf a partir dos dados do banco."""
    print("Iniciando a geração do arquivo queues.conf...")

    try:
        filas = get_all_filas()
        if not filas:
            conf_content = "; Arquivo gerado automaticamente pelo Micro PABX\n; Nenhuma fila configurada.\n"
        else:
            conf_parts = ["; Arquivo gerado automaticamente pelo Micro PABX\n"]

            for fila in filas:
                fila_id = fila['id']
                fila_num = fila['fila']
                fila_nome = fila['nome']

                print(f"Processando fila: [{fila_nome}]")
                conf_parts.append(f"[{fila_num}]")
                conf_parts.append("musicclass=default")
                conf_parts.append("strategy=ringall")
                conf_parts.append("timeout=20")
                conf_parts.append("retry=5")
                conf_parts.append("maxlen=1")
                conf_parts.append("joinempty=yes")
                conf_parts.append(f"context=interno")
                conf_parts.append("periodic-announce-frequency=30")
                conf_parts.append("announce-position=yes")
                conf_parts.append("announce-holdtime=yes")
                conf_parts.append('queue-thankyou="queue-thankyou"')

                # CORREÇÃO: Passando o ID da fila para a função
                ramais_membros = get_ramais_in_fila(fila_id)
                if ramais_membros:
                    print(f"  - Ramais encontrados: {', '.join(ramais_membros)}")
                    for ramal in ramais_membros:
                        conf_parts.append(f"member => SIP/{ramal}")
                else:
                    print(f"  - Aviso: A fila [{fila_nome}] não possui ramais associados.")

                conf_parts.append("\n")

            conf_content = "\n".join(conf_parts)

        # --- Escrita do Arquivo ---
        with open(QUEUES_CONF_PATH, 'w') as f:
            f.write(conf_content)
        print(f"Sucesso! Arquivo '{QUEUES_CONF_PATH}' foi gerado/atualizado.")

    except Exception as e:
        print(f"Ocorreu um erro durante a geração do queues.conf: {e}")

if __name__ == "__main__":
    generate_queues_conf()

