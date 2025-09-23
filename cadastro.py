from database import get_db_connection

# ---------------------------
# CRUD de Ramais
# ---------------------------

def adicionar_ramal(ramal, nome, senha, contexto):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM ramais WHERE ramal = ?", (ramal,))
    if c.fetchone():
        # Atualiza ramal existente
        c.execute("UPDATE ramais SET nome = ?, senha = ?, contexto = ? WHERE ramal = ?", (nome, senha, ramal, contexto))
        msg = "Ramal atualizado com sucesso!"
    else:
        # Cria novo ramal
        c.execute("INSERT INTO ramais (ramal, nome, senha, contexto) VALUES (?, ?, ?, ?)", (ramal, nome, senha, contexto))
        msg = "Ramal criado com sucesso!"
    conn.commit()
    conn.close()
    return True, msg

def remover_ramal(ramal):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM ramais WHERE ramal = ?", (ramal,))
    if not c.fetchone():
        conn.close()
        return False, "Ramal não encontrado"
    
    # Remove associações com filas antes
    c.execute("DELETE FROM ramais_filas WHERE num_ramal = ?", (ramal,))
    
    # Remove ramal
    c.execute("DELETE FROM ramais WHERE ramal = ?", (ramal,))
    conn.commit()
    conn.close()
    return True, "Ramal excluído com sucesso!"


def atualizar_ramal(ramal, nome=None, senha=None, contexto=None):
    conn = get_db_connection()
    try:
        if nome:
            conn.execute("UPDATE ramais SET nome = ? WHERE ramal = ?", (nome, ramal))
        if senha:
            conn.execute("UPDATE ramais SET senha = ? WHERE ramal = ?", (senha, ramal))
        if contexto:
            conn.execute("UPDATE ramais SET contexto = ? WHERE ramal = ?", (contexto, ramal))
        conn.commit()
        return True, "Ramal atualizado com sucesso."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# ---------------------------
# CRUD de Filas
# ---------------------------

def adicionar_fila(fila, nome):
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO filas (fila, nome) VALUES (?, ?)",
            (fila, nome)
        )
        conn.commit()
        return True, "Fila adicionada com sucesso."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def remover_fila(fila):
    conn = get_db_connection()
    c = conn.cursor()

    # Verifica se existe
    c.execute("SELECT * FROM filas WHERE fila = ?", (fila,))
    if not c.fetchone():
        conn.close()
        return False, "Fila não encontrada"

    # Remove associações de ramais
    c.execute("DELETE FROM ramais_filas WHERE num_fila = ?", (fila,))

    # Remove a fila
    c.execute("DELETE FROM filas WHERE fila = ?", (fila,))
    conn.commit()
    conn.close()
    return True, "Fila excluída com sucesso!"



def atualizar_fila(fila, nome=None):
    conn = get_db_connection()
    try:
        if nome:
            conn.execute("UPDATE filas SET nome = ? WHERE fila = ?", (nome, fila))
        conn.commit()
        return True, "Fila atualizada com sucesso."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def remover_fila(fila):
    conn = get_db_connection()
    try:
        # Remove associações antes
        conn.execute("DELETE FROM ramais_filas WHERE num_fila = ?", (fila,))
        # Remove a fila
        conn.execute("DELETE FROM filas WHERE fila = ?", (fila,))
        conn.commit()
        return True, "Fila removida com sucesso."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ---------------------------
# Associações Ramais <-> Filas
# ---------------------------

def associar_ramal_fila(ramal, fila):
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO ramais_filas (num_ramal, num_fila) VALUES (?, ?)",
            (ramal, fila)
        )
        conn.commit()
        return True, "Ramal associado à fila com sucesso."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def desassociar_ramal_fila(ramal, fila):
    conn = get_db_connection()
    try:
        conn.execute(
            "DELETE FROM ramais_filas WHERE num_ramal = ? AND num_fila = ?",
            (ramal, fila)
        )
        conn.commit()
        return True, "Ramal desassociado da fila com sucesso."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

