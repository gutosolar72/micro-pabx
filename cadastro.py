# /opt/micro-pbx/cadastro.py
import sqlite3
from database import get_db

# --- CRUD de Ramais (Já estava ok, mas limpando para consistência) ---

def adicionar_ramal(ramal, nome, senha, contexto):
    """Adiciona um novo ramal. Retorna False se já existir."""
    try:
        db = get_db()
        db.execute("INSERT INTO ramais (ramal, nome, senha, contexto) VALUES (?, ?, ?, ?)", (ramal, nome, senha, contexto))
        db.commit()
        db.close()
        return True, f"Ramal {ramal} criado com sucesso."
    except sqlite3.IntegrityError:
        return False, f"O ramal {ramal} já existe."
    except Exception as e:
        return False, str(e)

def atualizar_ramal(ramal_id, nome, senha, contexto):
    """Atualiza um ramal existente pelo seu ID."""
    try:
        db = get_db()
        db.execute("UPDATE ramais SET nome = ?, senha = ?, contexto = ? WHERE id = ?", (nome, senha, contexto, ramal_id))
        db.commit()
        db.close()
        return True, "Ramal atualizado com sucesso."
    except Exception as e:
        return False, str(e)

def remover_ramal(ramal_id): # <--- MUDANÇA AQUI
    """Remove um ramal e suas associações pelo ID do ramal."""
    try:
        db = get_db()
        db.execute("DELETE FROM ramal_fila WHERE ramal_id = ?", (ramal_id,))
        db.execute("DELETE FROM ramais WHERE id = ?", (ramal_id,)) # <--- MUDANÇA AQUI
        db.commit()
        db.close()
        return True, f"Ramal removido com sucesso."
    except Exception as e:
        return False, str(e)

# --- CRUD de Filas (CORREÇÃO PRINCIPAL) ---

def adicionar_fila(fila_num, nome):
    """Adiciona uma nova fila. Retorna False se já existir."""
    try:
        db = get_db()
        db.execute("INSERT INTO filas (fila, nome) VALUES (?, ?)", (fila_num, nome))
        db.commit()
        db.close()
        return True, f"Fila {fila_num} adicionada com sucesso."
    except sqlite3.IntegrityError:
        return False, f"A fila {fila_num} já existe."
    except Exception as e:
        return False, str(e)

def atualizar_fila(fila_id, nome):
    """Atualiza o nome de uma fila existente pelo seu ID."""
    try:
        db = get_db()
        db.execute("UPDATE filas SET nome = ? WHERE id = ?", (nome, fila_id))
        db.commit()
        db.close()
        return True, "Fila atualizada com sucesso."
    except Exception as e:
        return False, str(e)

def remover_fila(fila_id):
    """Remove uma fila e suas associações pelo ID da fila."""
    try:
        db = get_db()
        db.execute("DELETE FROM ramal_fila WHERE fila_id = ?", (fila_id,))
        db.execute("DELETE FROM filas WHERE id = ?", (fila_id,))
        db.commit()
        db.close()
        return True, "Fila removida com sucesso."
    except Exception as e:
        return False, str(e)

# --- Associações Ramais <-> Filas (CORREÇÃO PRINCIPAL) ---

def desassociar_todos_ramais_da_fila(fila_id):
    """Remove todas as associações de ramais para uma determinada fila (pelo ID)."""
    try:
        db = get_db()
        db.execute("DELETE FROM ramal_fila WHERE fila_id = ?", (fila_id,))
        db.commit()
        db.close()
    except Exception as e:
        print(f"Erro ao desassociar ramais da fila {fila_id}: {e}")

def associar_ramal_fila(ramal_id, fila_id):
    """Associa um ramal a uma fila usando os IDs de ambos."""
    try:
        db = get_db()
        db.execute("INSERT INTO ramal_fila (ramal_id, fila_id) VALUES (?, ?)", (ramal_id, fila_id))
        db.commit()
        db.close()
        return True, "Ramal associado com sucesso."
    except sqlite3.IntegrityError:
        return True, "Associação já existe."
    except Exception as e:
        return False, str(e)
