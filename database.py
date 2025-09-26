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
    c.execute("""CREATE TABLE IF NOT EXISTS ramais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ramal INTEGER UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    senha TEXT NOT NULL,
                    contexto TEXT DEFAULT 'interno'
                )""")

    # --- Tabela de Filas ---
    c.execute("""CREATE TABLE IF NOT EXISTS filas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fila INTEGER UNIQUE NOT NULL,
                    nome TEXT NOT NULL
                )""")

    # --- Tabela de Associação Ramais <-> Filas ---
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

    c.execute("""CREATE TABLE IF NOT EXISTS rotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    numero_entrada TEXT UNIQUE NOT NULL,
                    dest_fila_else INTEGER NOT NULL, -- FK para o ID da tabela de filas
                    FOREIGN KEY (dest_fila_else) REFERENCES filas(id) ON DELETE CASCADE
                )""")

    # --- NOVA Tabela de Time Conditions ---
    c.execute("""CREATE TABLE IF NOT EXISTS time_conditions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rota_id INTEGER NOT NULL,
                    time_start TEXT NOT NULL,
                    time_end TEXT NOT NULL,
                    days TEXT NOT NULL, -- Armazenado como string separada por vírgulas, ex: "mon,tue,wed"
                    dest_fila_if_time INTEGER NOT NULL, -- FK para o ID da tabela de filas
                    FOREIGN KEY (rota_id) REFERENCES rotas(id) ON DELETE CASCADE,
                    FOREIGN KEY (dest_fila_if_time) REFERENCES filas(id) ON DELETE CASCADE
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
    ramais_raw = conn.execute("SELECT id, ramal, nome, senha, contexto FROM ramais order by ramal").fetchall()
    ramais = []
    for r in ramais_raw:
        ramais.append({
            "id": r["id"],
            "ramal": r["ramal"],
            "nome": r["nome"],
            "senha": r["senha"],
            "contexto": r["contexto"]
        })
    conn.close()
    return ramais

def get_filas():
    db = get_db()
    filas_raw = db.execute("SELECT id, fila, nome FROM filas order by fila").fetchall()
    filas = []
    for f in filas_raw:
        ramais_associados = db.execute(
            "SELECT ramal_id FROM ramal_fila WHERE fila_id = ?", (f["id"],)
        ).fetchall()
        ramais_id_list = [r["ramal_id"] for r in ramais_associados]
        filas.append({
            "id": f["id"], "fila": f["fila"], "nome": f["nome"], "ramais": ramais_id_list
        })
    db.close()
    return filas

# Nova função para buscar time conditions de uma rota
def get_time_conditions_by_rota_id(rota_id):
    db = get_db()
    tcs_raw = db.execute("SELECT id, time_start, time_end, days, dest_fila_if_time FROM time_conditions WHERE rota_id = ? ORDER BY id", (rota_id,)).fetchall()
    db.close()
    return [dict(tc) for tc in tcs_raw]

def get_routes(include_time_conditions=False):
    db = get_db()
    cursor = db.execute("SELECT id, nome, numero_entrada, dest_fila_else FROM rotas")
    rotas = []
    for row in cursor.fetchall():
        rota = {
            "id": row[0],
            "nome": row[1],
            "numero_entrada": row[2],
            "dest_fila_else": row[3],
        }

        if include_time_conditions:
            tc_cursor = db.execute(
                """SELECT id, time_start, time_end, days, dest_fila_if_time
                   FROM time_conditions WHERE rota_id = ?""",
                (row[0],),
            )
            time_conditions = []
            for tc in tc_cursor.fetchall():
                time_conditions.append({
                    "id": tc[0],
                    "time_start": tc[1],
                    "time_end": tc[2],
                    "days": tc[3],
                    "dest_fila_if_time": tc[4],
                })
            rota["time_conditions"] = time_conditions

        rotas.append(rota)

    db.close()
    return rotas

# -------------------------------
# Configurações gerais (localnets)
# -------------------------------
def get_localnets():
    conn = get_db()
    rows = conn.execute("SELECT id, localnet, nome FROM localnets").fetchall()
    conn.close()
    return [{"id": r["id"], "localnet": r["localnet"], "nome": r["nome"]} for r in rows]

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

