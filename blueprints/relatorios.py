# blueprints/relatorios.py
import csv
from flask import Blueprint, render_template, request
from datetime import datetime

relatorios_bp = Blueprint("relatorios", __name__, template_folder="../templates")

CSV_FILE = "/var/log/asterisk/cdr-csv/Master.csv"

def parse_cdr():
    registros = []
    try:
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 16:
                    continue
                try:
                    dt = datetime.strptime(row[9], "%Y-%m-%d %H:%M:%S")
                    calldate_br = dt.strftime("%d/%m/%Y %H:%M:%S")
                except Exception:
                    calldate_br = row[9] 

                registro = {
                    "calldate": calldate_br,
                    "src": row[1],
                    "dst": row[2],
                    "clid": row[4],
                    "lastapp": row[7],
                    "lastdata": row[8],
                    "duration": row[12],
                    "billsec": row[13],
                    "disposition": "Atendida" if row[14].upper() == "ANSWERED" else (
                        "Ocupado" if row[14].upper() == "BUSY" else row[14].capitalize()
                    ),
                }
                registros.append(registro)
    except FileNotFoundError:
        print(f"Arquivo {CSV_FILE} não encontrado.")
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

    return render_template(
        "relatorio_cdr.html",
        registros=registros_paginados,
        page=page,
        total_pages=total_pages
    )

