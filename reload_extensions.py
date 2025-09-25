# /opt/micro-pbx/reload_extensions.py
import os
from database import get_db

EXTENSIONS_CONF_PATH = '/etc/asterisk/extensions.conf'

# --- Funções de Busca no Banco de Dados ---

def get_all_peers(db):
    """Busca todos os NÚMEROS de ramais."""
    peers_raw = db.execute("SELECT ramal FROM ramais ORDER BY ramal").fetchall()
    return [str(p['ramal']) for p in peers_raw]

def get_all_queues(db):
    """Busca todos os NÚMEROS de filas."""
    queues_raw = db.execute("SELECT fila FROM filas ORDER BY fila").fetchall()
    return [str(q['fila']) for q in queues_raw]

def get_all_routes(db):
    """Busca todas as rotas customizadas."""
    return db.execute("SELECT * FROM rotas ORDER BY nome").fetchall()

# --- Função Principal de Geração ---

def generate_extensions_conf():
    """Gera o conteúdo completo do arquivo extensions.conf com um contexto unificado."""
    print("Iniciando a geração do arquivo extensions.conf...")
    db = get_db()
    
    peers = get_all_peers(db)
    queues = get_all_queues(db)
    routes = get_all_routes(db)
    
    # --- Inicia a construção do dialplan ---
    conf_parts = [
        "; Arquivo gerado automaticamente pelo Micro PABX",
        "[interno] ; Contexto Unificado para todas as chamadas"
    ]

    # --- 1. Lógica Customizada: Rotas de Entrada ---
    if routes:
        conf_parts.extend([
            "\n; --- Regras Customizadas: Rotas de Entrada ---"
        ])
        for route in routes:
            exten = route['numero_entrada']
            
            # Busca os NÚMEROS das filas de destino a partir de seus IDs
            fila_else_id = route['dest_fila_else']
            fila_else_num_row = db.execute("SELECT fila FROM filas WHERE id = ?", (fila_else_id,)).fetchone()
            
            if not fila_else_num_row: continue # Pula a rota se a fila de destino não existe mais

            fila_else_num = fila_else_num_row['fila']

            conf_parts.append(f"\n; Rota: {route['nome']}")
            conf_parts.append(f"exten => {exten},1,NoOp(### Rota de Entrada: {route['nome']} para o numero {exten} ###)")

            if route['time_condition_enabled']:
                time_range = f"{route['time_start']}-{route['time_end']}"
                days = route['days'].replace(",","|")
                fila_if_time_id = route['dest_fila_if_time']
                fila_if_time_num_row = db.execute("SELECT fila FROM filas WHERE id = ?", (fila_if_time_id,)).fetchone()

                if not fila_if_time_num_row: continue # Pula se a fila de tempo não existe

                fila_if_time_num = fila_if_time_num_row['fila']
                
                conf_parts.extend([
                    f"exten => {exten},n,GotoIfTime({time_range},{days},*,*?time-match)",
                    f"exten => {exten},n,Queue({fila_else_num}) ; Rota fora do horario",
                    f"exten => {exten},n,Hangup()",
                    f"exten => {exten},n(time-match),Queue({fila_if_time_num}) ; Rota dentro do horario",
                    f"exten => {exten},n,Hangup()"
                ])
            else:
                conf_parts.extend([
                    f"exten => {exten},n,Queue({fila_else_num})",
                    f"exten => {exten},n,Hangup()"
                ])

    # --- 2. Lógica Automática: Chamadas para Filas ---
    if queues:
        conf_parts.extend(["\n; --- Regra Automatica: Chamadas para Filas ---",])
        for queue in queues:
            conf_parts.extend([
                f"exten => {queue},1,NoOp(### Chamada interna para Fila ${{EXTEN}} ###)",
                f"exten => {queue},n,Queue(${{EXTEN}})", 
                f"exten => {queue},n,Hangup()\n"
            ])

    # --- 3. Lógica Automática: Chamadas para outros Ramais ---
    if peers:
        conf_parts.extend([
            "\n; --- Regra Automatica: Chamadas para outros Ramais ---",
            f"exten => _X,1,NoOp(### Chamada interna para Ramal ${{EXTEN}} ###)",
            f"exten => _X,n,Dial(SIP/${{EXTEN}},20,Ttr)",
            f"exten => _X,n,Hangup()\n\n"

            f"exten => _X.,1,NoOp(### Chamada interna para Ramal ${{EXTEN}} ###)",
            f"exten => _X.,n,Dial(SIP/${{EXTEN}},20,Ttr)",
            f"exten => _X.,n,Hangup()\n"
        ])


    
    db.close()

    # --- Finaliza e Escreve o Arquivo ---
    conf_content = "\n".join(conf_parts)
    try:
        with open(EXTENSIONS_CONF_PATH, 'w') as f:
            f.write(conf_content)
        print(f"Sucesso! Arquivo '{EXTENSIONS_CONF_PATH}' foi gerado/atualizado.")
    except Exception as e:
        print(f"ERRO ao escrever extensions.conf: {e}")

if __name__ == "__main__":
    generate_extensions_conf()

