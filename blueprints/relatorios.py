import csv
import os
import glob
from werkzeug.utils import safe_join
from .main import license_message,license_context
from flask import abort, send_from_directory, Blueprint, render_template, request, url_for
from datetime import datetime
from licenca import get_modulos

relatorios_bp = Blueprint("relatorios", __name__, template_folder="../templates")

CSV_DIR = "/var/log/asterisk/cdr-csv"
CSV_FILE_PATTERN = os.path.join(CSV_DIR, "Master.csv*")
MONITOR_DIR = "/var/spool/asterisk/monitor"
MAX_FILES = 7

def parse_cdr():
    registros = []

    # Lista e ordena os arquivos Master.csv* por data de modificação
    arquivos = sorted(
        glob.glob(CSV_FILE_PATTERN),
        key=os.path.getmtime,
        reverse=True  # do mais novo para o mais antigo
    )[:MAX_FILES]  # pega os últimos 7 arquivos

    for arquivo in arquivos:
        if not os.path.isfile(arquivo):
            continue
        try:
            with open(arquivo, newline="", encoding="utf-8") as f:
                reader = list(csv.reader(f))
                # Inverte linhas dentro do CSV para que o registro mais recente apareça primeiro
                for row in reversed(reader):
                    if not row or len(row) < 17:
                        continue
                    # Converte data/hora para formato BR
                    try:
                        dt = datetime.strptime(row[9], "%Y-%m-%d %H:%M:%S")
                        calldate_br = dt.strftime("%d/%m/%Y %H:%M:%S")
                    except Exception:
                        calldate_br = row[9]

                    uniqueid = row[16]
                    grava_file = os.path.join(MONITOR_DIR, f"{uniqueid}.wav")
                    recording = grava_file if os.path.isfile(grava_file) else None

                    disposition = row[14].strip().upper() if len(row) > 14 else "UNKNOWN"

                    status_map = {
                        "ANSWERED": "Atendida",
                        "BUSY": "Ocupado",
                        "FAILED": "Falha",
                        "NO ANSWER": "Não atendida",
                        "CANCEL": "Cancelada",
                        "CONGESTION": "Congestionada"
                    }

                    registro = {
                        "calldate": calldate_br,
                        "src": row[1],
                        "dst": row[2],
                        "clid": row[4],
                        "lastapp": row[7],
                        "lastdata": row[8],
                        "duration": row[12],
                        "billsec": row[13],
                        "disposition": status_map.get(disposition, disposition.capitalize()),
                        "uniqueid": uniqueid,
                        "recording": recording
                    }
                    registros.append(registro)
        except FileNotFoundError:
            print(f"Arquivo {arquivo} não encontrado.")
        except Exception as e:
            print(f"Erro ao processar {arquivo}: {e}")

    return registros

@relatorios_bp.route("/relatorios")
def relatorio_cdr():
    # parâmetros da paginação
    page = int(request.args.get("page", 1))
    per_page = 20

    registros = parse_cdr()
    total = len(registros)

    start = (page - 1) * per_page
    end = start + per_page
    registros_paginados = registros[start:end]

    total_pages = (total // per_page) + (1 if total % per_page else 0)

    # verifica se o módulo 'record' está ativo
    MODULOS = get_modulos() or ''  # garante que seja string
    MODULOS = MODULOS.lower().split(',')    # converte em lista, mesmo se vazio
    has_record = 'record' in MODULOS    
    
    # adiciona o caminho completo para o arquivo de gravação, se habilitado
    if has_record:
        for r in registros_paginados:
            # remove ponto e tudo depois do uniqueid
            uniqueid_safe = r['uniqueid'].split('.')[0]
            filename = f"{r['src']}-{r['dst']}-{uniqueid_safe}.wav"
            full_path = os.path.join(MONITOR_DIR, filename)

            if os.path.isfile(full_path) and os.path.getsize(full_path) > 44:    
                r['recording'] = url_for('relatorios.recordings', filename=filename)
            else:
                r['recording'] = None  # gravação não existe

    return render_template(
        "relatorio_cdr.html",
        registros=registros_paginados,
        page=page,
        total_pages=total_pages,
        has_record=has_record,
        LICENSE_VALID=license_context(),
        LICENSE_MSG=license_message()
    )

@relatorios_bp.route('/recordings/<path:filename>')
def recordings(filename):
    path = safe_join(MONITOR_DIR, filename)
    if not os.path.isfile(path):
        abort(404)
    return send_from_directory(MONITOR_DIR, filename)

