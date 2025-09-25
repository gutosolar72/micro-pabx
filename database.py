import sqlite3
import bcrypt
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'micro_pbx.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():

    print(f"Inicializando banco de dados em: {DB_PATH}")
    conn = get_db()
    c = conn.cursor()

    # --- Tabela de Usuários ---
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                 )""")

    # --- Tabela de Ramais ---
    # Modificada para usar ID autoincremental, o que é melhor para Foreign Keys.
    c.execute("""CREATE TABLE IF NOT EXISTS ramais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ramal INTEGER UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    senha TEXT NOT NULL,
                    contexto TEXT DEFAULT 'interno'
                )""")

    # --- Tabela de Filas ---
    # Modificada para usar ID autoincremental.
    c.execute("""CREATE TABLE IF NOT EXISTS filas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fila INTEGER UNIQUE NOT NULL,
                    nome TEXT NOT NULL
                )""")

    # --- Tabela de Associação Ramais <-> Filas ---
    # Modificada para usar os novos IDs das tabelas ramais e filas.
    c.execute("""CREATE TABLE IF NOT EXISTS ramal_fila (
                    ramal_id INTEGER NOT NULL,
                    fila_id INTEGER NOT NULL,
                    FOREIGN KEY (ramal_id) REFERENCES ramais(id) ON DELETE CASCADE,
                    FOREIGN KEY (fila_id) REFERENCES filas(id) ON DELETE CASCADE,
                    PRIMARY KEY (ramal_id, fila_id)
                )""")

    # --- Tabela de Redes Locais (localnet) ---
    c.execute("""CREATE TABLE IF NOT EXISTS localnets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    localnet TEXT NOT NULL
               )""")

    # --- NOVA Tabela de Rotas de Entrada ---
    c.execute("""CREATE TABLE IF NOT EXISTS rotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    numero_entrada TEXT UNIQUE NOT NULL,
                    time_condition_enabled BOOLEAN NOT NULL DEFAULT 0,
                    time_start TEXT,
                    time_end TEXT,
                    days TEXT, -- Armazenado como string separada por vírgulas, ex: "mon,tue,wed"
                    dest_fila_if_time INTEGER, -- FK para o ID da tabela de filas
                    dest_fila_else INTEGER NOT NULL, -- FK para o ID da tabela de filas
                    FOREIGN KEY (dest_fila_if_time) REFERENCES filas(id) ON DELETE SET NULL,
                    FOREIGN KEY (dest_fila_else) REFERENCES filas(id) ON DELETE CASCADE
                )""")

    # --- Verificação e Criação do Usuário Admin ---
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        print("Usuário 'admin' não encontrado. Criando com senha padrão...")
        senha_padrao = "123mudar@".encode("utf-8")
        hashed = bcrypt.hashpw(senha_padrao, bcrypt.gensalt())
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                  ("admin", hashed.decode("utf-8")))
        print(">>> Usuário 'admin' criado com senha padrão: 123mudar@ <<<")

    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso.")

def get_ramais():
    conn = get_db()
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

def get_filas():
    db = get_db()
    filas_raw = db.execute("SELECT id, fila, nome FROM filas").fetchall()
    filas = []
    for f in filas_raw:
        ramais_associados = db.execute(
            "SELECT ramal_id FROM ramal_fila WHERE fila_id = ?", (f["id"],) # CORRIGIDO
        ).fetchall()
        ramais_id_list = [r["ramal_id"] for r in ramais_associados]
        filas.append({
            "id": f["id"], "fila": f["fila"], "nome": f["nome"], "ramais": ramais_id_list
        })
    db.close()
    return filas

# -------------------------------
# Configurações gerais (localnets)
# -------------------------------
def get_localnets():
    conn = get_db()
    rows = conn.execute("SELECT id, localnet, nome FROM localnets").fetchall()
    conn.close()
    return [{"id": r["id"], "localnet": r["localnet"], "nome": r["nome"]} for r in rows]

# database.py
def update_localnets(localnets):
    """
    Substitui todos os localnets existentes pelos enviados
    Espera receber uma lista de dicts: [{"nome": "...", "localnet": "..."}, ...]
    """
    conn = get_db()
    conn.execute("DELETE FROM localnets")  # apaga todos
    for net in localnets:
        conn.execute(
            "INSERT INTO localnets (nome, localnet) VALUES (?, ?)",
            (net["nome"], net["localnet"])
        )
    conn.commit()
    conn.close()

