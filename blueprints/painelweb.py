from flask import Blueprint, render_template, jsonify, flash
import subprocess, re, sqlite3, os

painelweb_bp = Blueprint("painelweb", __name__)

DB_PATH = "/opt/nanosip/nanosip.db"
DEBUG = True


def coletar_chamadas():
    try:
        output = subprocess.check_output(
            ["asterisk", "-rx", "core show channels verbose"],
            text=True, stderr=subprocess.STDOUT
        )
        output = "\n".join(line for line in output.splitlines() if "AppDial" not in line)
    except subprocess.CalledProcessError as e:
        if DEBUG:
            flash(f"[PainelWeb] Erro ao executar 'core show channels': {e.output}", "danger")
        return []

    chamadas = []
    for linha in output.splitlines():
        if not linha.strip() or linha.startswith("Channel") or "active" in linha.lower():
            continue
        partes = re.split(r'\s{2,}', linha.strip())
        if len(partes) < 7:
            continue
        origem = partes[2] if len(partes) > 2 else "-"
        destino = partes[6] if len(partes) > 6 else "-"
        duracao = partes[7] if len(partes) > 7 else "-"
        chamadas.append({"origem": origem, "destino": destino, "duracao": duracao})
    return chamadas


def coletar_ramais():
    nomes_ramais = {}
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            for r in cursor.execute("SELECT ramal, nome FROM ramais"):
                nomes_ramais[str(r[0])] = r[1]
            conn.close()
        except Exception as e:
            if DEBUG:
                flash(f"[PainelWeb] Erro ao ler DB: {e}", "danger")

    chamadas = coletar_chamadas()
    ramais_em_chamada = set()
    for c in chamadas:
        if c["origem"].isdigit():
            ramais_em_chamada.add(c["origem"])
        if c["destino"].isdigit():
            ramais_em_chamada.add(c["destino"])

    try:
        output = subprocess.check_output(
            ["asterisk", "-rx", "sip show peers"],
            text=True, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        if DEBUG:
            flash(f"[PainelWeb] Erro ao executar 'sip show peers': {e.output}", "danger")
        return []

    padrao = re.compile(
        r'^(?P<name>\S+?)/\S+\s+'
        r'(?P<ip>(?:\d{1,3}\.){3}\d{1,3}|\(Unspecified\))\s+'
        r'(?:\S+\s+){2,}?'
        r'(?P<port>\d+)\s+'
        r'(?P<status>.*)$', re.IGNORECASE
    )

    ramais = []
    for linha in output.splitlines():
        linha = linha.strip()
        if not linha or linha.lower().startswith("name/username") or "peer" in linha.lower():
            continue
        m = padrao.match(linha)
        if not m:
            continue

        ramal = m.group("name").strip()
        ip = m.group("ip").strip()
        status_txt = m.group("status").strip().upper()

        latencia = "-"
        cor = "gray"
        status = "offline"

        if ip.upper() != "(UNSPECIFIED)" and ip != "":
            if "OK" in status_txt:
                status = "online"
                cor = "green"
                mlat = re.search(r'\(([^)]+)\)', status_txt)
                if mlat:
                    latencia = mlat.group(1)
            elif any(x in status_txt for x in ["UNREACHABLE", "LAGGED", "UNKNOWN"]):
                status = "offline"
                cor = "gray"
            else:
                status = "offline"
                cor = "gray"
        else:
            ip = "offline"
            status = "offline"
            cor = "gray"

        if ramal in ramais_em_chamada:
            status = "ocupado"
            cor = "red"

        nome = nomes_ramais.get(ramal, f"Ramal {ramal}")

        ramais.append({
            "ramal": ramal,
            "nome": nome,
            "status": status,
            "cor": cor,
            "ip": ip,
            "latencia": latencia
        })

    return ramais


def coletar_filas():
    filas = []
    if not os.path.exists(DB_PATH):
        return filas

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, fila, nome FROM filas")
        filas_data = cursor.fetchall()

        for f_id, fila_num, nome in filas_data:
            cursor.execute("""
                SELECT ramais.ramal, ramais.nome
                FROM ramal_fila
                JOIN ramais ON ramais.id = ramal_fila.ramal_id
                WHERE ramal_fila.fila_id = ?
            """, (f_id,))
            ramais_fila = [{"ramal": str(r[0]), "nome": r[1]} for r in cursor.fetchall()]
            filas.append({"fila": str(fila_num), "nome": nome, "ramais": ramais_fila})

        conn.close()
    except Exception as e:
        if DEBUG:
            flash(f"[PainelWeb] Erro ao coletar filas: {e}", "danger")

    return filas


@painelweb_bp.route("/painel")
def painel():
    return render_template("painelweb.html")


@painelweb_bp.route("/api/ramais")
def api_ramais():
    dados = {
        "ramais": coletar_ramais(),
        "filas": coletar_filas(),
        "chamadas": coletar_chamadas()
    }
    if DEBUG:
        print(dados)
    return jsonify(dados)

