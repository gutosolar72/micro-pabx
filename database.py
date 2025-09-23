import sqlite3
import bcrypt

DB = "micro_pbx.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Cria tabela de usuários
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT
                 )""")

    # Cria tabela de ramais
    c.execute("""CREATE TABLE IF NOT EXISTS ramais (
                    ramal INTEGER PRIMARY KEY,  -- definido manualmente
                    nome TEXT NOT NULL,
                    senha TEXT,
                    contexto TEXT
                )""")

    # Cria tabela de filas
    c.execute("""CREATE TABLE IF NOT EXISTS filas (
                    fila INTEGER PRIMARY KEY,  -- definido manualmente
                    nome TEXT NOT NULL
                )""")

    # Cria tabela de associação ramais <-> filas
    c.execute("""CREATE TABLE IF NOT EXISTS ramais_filas (
                    num_fila INTEGER NOT NULL,
                    num_ramal INTEGER NOT NULL,
                    FOREIGN KEY (num_fila) REFERENCES filas(fila),
                    FOREIGN KEY (num_ramal) REFERENCES ramais(ramal),
                    PRIMARY KEY (num_fila, num_ramal)
                )""")
    # Cria a tabela de localnet
    c.execute("""CREATE TABLE IF NOT EXISTS config_geral (
                    id INTEGER PRIMARY KEY,
                    localnet TEXT NOT NULL,
                    nome TEXT NOT NULL
               )""")

    # Verifica se já existe usuário admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        # Cria hash da senha
        senha = "123mudar@".encode("utf-8")
        hashed = bcrypt.hashpw(senha, bcrypt.gensalt())
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                  ("admin", hashed.decode("utf-8")))
        print("Usuário 'admin' criado com senha padrão: 123mudar@")

    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_ramais():
    conn = get_db_connection()
    ramais_raw = conn.execute("SELECT ramal, nome, senha, contexto FROM ramais").fetchall()
    ramais = []
    for r in ramais_raw:
        ramais.append({
            "ramal": r["ramal"],
            "nome": r["nome"],
            "senha": r["senha"],
            "contexto": r["contexto"]
        })
    conn.close()
    return ramais


# Buscar filas e os ramais associados
def get_filas():
    """
    Retorna a lista de filas com os ramais associados
    """
    conn = get_db_connection()
    filas_raw = conn.execute("SELECT fila, nome FROM filas").fetchall()
    filas = []

    for f in filas_raw:
        # busca ramais associados
        ramais_associados = conn.execute(
            "SELECT r.ramal FROM ramais r "
            "JOIN ramais_filas rf ON r.ramal = rf.num_ramal "
            "WHERE rf.num_fila = ?", (f["fila"],)
        ).fetchall()
        ramais_list = [r["ramal"] for r in ramais_associados]

        filas.append({
            "fila": f["fila"],
            "nome": f["nome"],
            "ramais": ramais_list
        })

    conn.close()
    return filas

# -------------------------------
# Configurações gerais (localnets)
# -------------------------------
def get_localnets():
    conn = get_db_connection()
    rows = conn.execute("SELECT id, localnet, nome FROM config_geral").fetchall()
    conn.close()
    return [{"id": r["id"], "localnet": r["localnet"], "nome": r["nome"]} for r in rows]

# database.py
def update_localnets(localnets):
    """
    Substitui todos os localnets existentes pelos enviados
    Espera receber uma lista de dicts: [{"nome": "...", "localnet": "..."}, ...]
    """
    conn = get_db_connection()
    conn.execute("DELETE FROM config_geral")  # apaga todos
    for net in localnets:
        conn.execute(
            "INSERT INTO config_geral (nome, localnet) VALUES (?, ?)",
            (net["nome"], net["localnet"])
        )
    conn.commit()
    conn.close()

