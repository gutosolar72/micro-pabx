# reload_queues.py
import sqlite3
import os # <--- ADICIONADO

# --- Configurações ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'micro_pbx.db') 

QUEUES_CONF_PATH = '/etc/asterisk/queues.conf'

# --- Funções de Acesso ao Banco de Dados ---

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_filas(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT fila, nome FROM filas")
    return cursor.fetchall()

def get_ramais_in_fila(conn, fila_num):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT num_ramal
        FROM ramais_filas
        WHERE num_fila = ?
    """, (fila_num,))
    return [str(row['num_ramal']) for row in cursor.fetchall()]

# --- Lógica Principal ---

def generate_queues_conf():
    conn = get_db_connection()
    if not conn:
        print("Erro: Não foi possível conectar ao banco de dados.")
        return

    try:
        filas = get_all_filas(conn)
        if not filas:
            conf_content = "; Arquivo gerado automaticamente pelo Micro PABX\n; Nenhuma fila configurada.\n"
        else:
            conf_parts = ["; Arquivo gerado automaticamente pelo Micro PABX\n"]

            for fila in filas:
                fila_num = fila['fila']
                fila_nome = fila['nome']

                conf_parts.append(f"[{fila_nome}]")
                conf_parts.append("musicclass=default")
                conf_parts.append("strategy=ringall")
                conf_parts.append("timeout=20")
                conf_parts.append("retry=5")
                conf_parts.append("maxlen=1")
                conf_parts.append("joinempty=yes")
                conf_parts.append(f"context=from-{fila_nome}")
                conf_parts.append("periodic-announce-frequency=30")
                conf_parts.append("announce-position=yes")
                conf_parts.append("announce-holdtime=yes")
                conf_parts.append('queue-thankyou="queue-thankyou"')

                ramais_membros = get_ramais_in_fila(conn, fila_num)
                if ramais_membros:
                    for ramal in ramais_membros:
                        conf_parts.append(f"member => SIP/{ramal}")
                else:
                    print(f"  - Aviso: A fila [{fila_nome}] não possui ramais associados.")
                
                conf_parts.append("\n")

            conf_content = "\n".join(conf_parts)

        with open(QUEUES_CONF_PATH, 'w') as f:
            f.write(conf_content)

    except Exception as e:
        print(f"Ocorreu um erro durante a geração do queues.conf: {e}")

    finally:
        conn.close()

# --- Ponto de Entrada do Script ---
if __name__ == "__main__":
    generate_queues_conf()

