import os
from database import get_db

EXTENSIONS_CONF_PATH = '/etc/asterisk/extensions.conf'

# --- Funções de Busca no Banco de Dados ---

def get_all_peers(db):
    peers_raw = db.execute("SELECT ramal FROM ramais ORDER BY ramal").fetchall()
    return [str(p['ramal']) for p in peers_raw]

def get_all_queues(db):
    queues_raw = db.execute("SELECT fila FROM filas ORDER BY fila").fetchall()
    return [str(q['fila']) for q in queues_raw]

def get_all_routes(db):
    """Busca todas as rotas customizadas com suas time conditions."""
    routes_raw = db.execute("SELECT * FROM rotas ORDER BY nome").fetchall()
    routes = []
    for r in routes_raw:
        time_conditions = db.execute("SELECT * FROM time_conditions WHERE rota_id = ?", (r['id'],)).fetchall()
        r = dict(r)
        r['time_conditions'] = [dict(tc) for tc in time_conditions]
        routes.append(r)
    return routes

# --- Função Principal de Geração ---

def generate_extensions_conf():
    print("Iniciando a geração do arquivo extensions.conf...")
    db = get_db()

    peers = get_all_peers(db)
    queues = get_all_queues(db)
    routes = get_all_routes(db)

    conf_parts = [
        "; Arquivo gerado automaticamente pelo Micro PABX",
        "[interno] ; Contexto Unificado para todas as chamadas"
    ]

    # --- Rotas de Entrada ---
    if routes:
        conf_parts.append("\n; --- Regras Customizadas: Rotas de Entrada ---")
        for route in routes:
            exten = route['numero_entrada']

            fila_else_num = None
            if route['dest_fila_else']:
                fila_else_row = db.execute("SELECT fila FROM filas WHERE id = ?", (route['dest_fila_else'],)).fetchone()
                if fila_else_row:
                    fila_else_num = fila_else_row['fila']

            conf_parts.append(f"\n; Rota: {route['nome']}")
            conf_parts.append(f"exten => {exten},1,NoOp(### Rota de Entrada: {route['nome']} para o numero {exten} ###)")

            if route['time_conditions']:
                # Para cada time condition
                for tc in route['time_conditions']:
                    if not tc['dest_fila_if_time']:
                        continue
                    fila_if_time_row = db.execute("SELECT fila FROM filas WHERE id = ?", (tc['dest_fila_if_time'],)).fetchone()
                    if not fila_if_time_row:
                        continue
                    fila_if_time_num = fila_if_time_row['fila']
                    time_start = tc['time_start']
                    time_end = tc['time_end']
                    days = tc['days'].split(',')  # separa dias individuais

                    for day in days:
                        day = day.strip()
                        if not day:
                            continue
                        conf_parts.append(f"exten => {exten},n,GotoIfTime({time_start}-{time_end},{day},*,*?time-{day}-{time_start})")

                    # Fora do horário (após todas as condições)
                    if fila_else_num:
                        conf_parts.append(f"exten => {exten},n,Queue({fila_else_num}) ; Rota fora do horario")
                    conf_parts.append(f"exten => {exten},n,Hangup()")

                    # Destino dentro do horário (para cada day)
                    for day in days:
                        day = day.strip()
                        if not day:
                            continue
                        conf_parts.append(f"exten => {exten},n(time-{day}-{time_start}),Queue({fila_if_time_num}) ; Rota dentro do horario")
                        conf_parts.append(f"exten => {exten},n,Hangup()")
            else:
                # Sem time condition
                if fila_else_num:
                    conf_parts.append(f"exten => {exten},n,Queue({fila_else_num})")
                conf_parts.append(f"exten => {exten},n,Hangup()")

    # --- Chamadas para Filas ---
    if queues:
        conf_parts.append("\n; --- Regra Automatica: Chamadas para Filas ---")
        for queue in queues:
            conf_parts.extend([
                f"exten => {queue},1,NoOp(### Chamada interna para Fila ${{EXTEN}} ###)",
                f"exten => {queue},n,Queue(${{EXTEN}})",
                f"exten => {queue},n,Hangup()\n"
            ])

    # --- Chamadas para Ramais ---
    if peers:
        conf_parts.extend([
            "\n; --- Regra Automatica: Chamadas para outros Ramais ---",
            f"exten => _X,1,NoOp(### Chamada interna para Ramal ${{EXTEN}} ###)",
            f"exten => _X,n,Dial(SIP/${{EXTEN}},20,Ttr)",
            f"exten => _X,n,Hangup()\n",
            f"exten => _X.,1,NoOp(### Chamada interna para Ramal ${{EXTEN}} ###)",
            f"exten => _X.,n,Dial(SIP/${{EXTEN}},20,Ttr)",
            f"exten => _X.,n,Hangup()\n"
        ])

    db.close()

    # --- Escreve o arquivo ---
    conf_content = "\n".join(conf_parts)
    try:
        with open(EXTENSIONS_CONF_PATH, 'w') as f:
            f.write(conf_content)
        print(f"Sucesso! Arquivo '{EXTENSIONS_CONF_PATH}' foi gerado/atualizado.")
    except Exception as e:
        print(f"ERRO ao escrever extensions.conf: {e}")

if __name__ == "__main__":
    generate_extensions_conf()

