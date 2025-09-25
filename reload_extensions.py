# /opt/micro-pbx/reload_extensions.py

import os
from database import get_db

# --- Configurações ---
EXTENSIONS_CONF_PATH = '/etc/asterisk/extensions.conf'

# --- Funções de Geração de Dialplan ---

def get_all_internal_peers():
    """Busca todos os ramais que pertencem ao contexto 'interno'."""
    db = get_db()
    peers_raw = db.execute("SELECT ramal FROM ramais WHERE contexto = 'interno'").fetchall()
    db.close()
    return [str(p['ramal']) for p in peers_raw]

def get_all_routes():
    """Busca todas as rotas de entrada e os nomes das filas de destino."""
    db = get_db()
    routes_raw = db.execute("""
        SELECT 
            r.id, r.nome, r.numero_entrada, r.time_condition_enabled,
            r.time_start, r.time_end, r.days,
            f_if_time.nome as fila_nome_if_time,
            f_else.nome as fila_nome_else
        FROM rotas r
        JOIN filas f_else ON r.dest_fila_else = f_else.id
        LEFT JOIN filas f_if_time ON r.dest_fila_if_time = f_if_time.id
    """).fetchall()
    db.close()
    return [dict(row) for row in routes_raw]

def generate_internal_context(peers):
    """Gera o dialplan para o contexto [interno] que permite chamadas entre ramais."""
    if not peers:
        return ""
    
    lines = ["[interno] ; Contexto para ramais internos (porteiros, etc)"]
    
    peer_pattern = "|".join(peers)
    
    # --- AQUI ESTÁ A CORREÇÃO ---
    # As chaves da variável do Asterisk ${EXTEN} precisam ser escapadas com chaves duplas {{ e }}
    # E a expressão DIALMATCH também.
    lines.append(f"exten => _X.,1,NoOp(### Chamada interna para o ramal ${{EXTEN}} ###)")
    
    # A expressão complexa do DIALMATCH fica mais legível se construída separadamente
    dialmatch_expression = f"$[${{DIALMATCH(${{EXTEN}},{peer_pattern})}} = 1]"
    lines.append(f"exten => _X.,n,GotoIf({dialmatch_expression}?internal-call,1)")
    
    lines.append(f"exten => _X.,n,NoOp(Numero ${{EXTEN}} nao e um ramal interno valido.)")
    lines.append(f"exten => _X.,n,Hangup()")
    lines.append("")
    lines.append(f"exten => internal-call,1,Dial(SIP/${{EXTEN}},20,Ttr)")
    lines.append(f"exten => internal-call,n,Hangup()")
    lines.append("")

    # Regra para permitir que porteiros liguem para os portões (assumindo 4 dígitos)
    lines.append("; Regra para permitir que porteiros liguem para os portões")
    lines.append(f"exten => _XXXX,1,NoOp(### Chamada interna para equipamento externo/portão ${{EXTEN}} ###)")
    lines.append(f"exten => _XXXX,n,Dial(SIP/${{EXTEN}},20,Ttr)")
    lines.append(f"exten => _XXXX,n,Hangup()")
    lines.append("")

    return "\n".join(lines)

def generate_routes_context(routes):
    """Gera os contextos e dialplans para as rotas de entrada."""
    if not routes:
        return ""
        
    lines = []
    for route in routes:
        context_name = f"from-entrada-{route['id']}"
        numero_entrada = route['numero_entrada']
        
        lines.append(f"[{context_name}] ; Rota: {route['nome']}")
        
        if route['time_condition_enabled']:
            time_range = f"{route['time_start']}-{route['time_end']}"
            days = route['days']
            fila_if_time = route['fila_nome_if_time']
            fila_else = route['fila_nome_else']
            label_if_time = f"dentro-horario-{route['id']}"
            
            lines.append(f"exten => {numero_entrada},1,NoOp(### Chamada de Entrada para {numero_entrada} com Time Condition ###)")
            lines.append(f"exten => {numero_entrada},n,GotoIfTime({time_range},{days},*,*?{label_if_time})")
            lines.append(f"exten => {numero_entrada},n,NoOp(Fora do horario, encaminhando para fila padrao: {fila_else})")
            lines.append(f"exten => {numero_entrada},n,Queue({fila_else})")
            lines.append(f"exten => {numero_entrada},n,Hangup()")
            lines.append("")
            lines.append(f"exten => {numero_entrada},n({label_if_time}),NoOp(Dentro do horario, encaminhando para fila: {fila_if_time})")
            lines.append(f"exten => {numero_entrada},n,Queue({fila_if_time})")
            lines.append(f"exten => {numero_entrada},n,Hangup()")
        else:
            fila_destino = route['fila_nome_else']
            lines.append(f"exten => {numero_entrada},1,NoOp(### Chamada de Entrada para {numero_entrada} ###)")
            lines.append(f"exten => {numero_entrada},n,Queue({fila_destino})")
            lines.append(f"exten => {numero_entrada},n,Hangup()")
            
        lines.append("\n")

    return "\n".join(lines)

def generate_extensions_conf():
    """Função principal que gera o conteúdo completo do extensions.conf."""
    print("Iniciando a geração do arquivo extensions.conf...")
    
    internal_peers = get_all_internal_peers()
    routes = get_all_routes()
    
    # --- CORREÇÃO 1: Removido o [general] desnecessário ---
    header = ["; Arquivo gerado automaticamente pelo Micro PABX\n"]
    internal_context_content = generate_internal_context(internal_peers)
    routes_context_content = generate_routes_context(routes)
    
    # --- CORREÇÃO 2: Adicionado o internal_context_content ao arquivo final ---
    full_content = "\n".join(header) + internal_context_content + "\n" + routes_context_content
    
    try:
        with open(EXTENSIONS_CONF_PATH, 'w') as f:
            f.write(full_content)
        print(f"Sucesso! Arquivo '{EXTENSIONS_CONF_PATH}' foi gerado/atualizado.")
    except Exception as e:
        print(f"ERRO ao escrever o arquivo extensions.conf: {e}")

if __name__ == "__main__":
    generate_extensions_conf()

