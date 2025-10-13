#!/bin/bash
# cleanup_recordings.sh
# Remove gravações antigas de mais de 7 dias do Asterisk

# Diretório onde as gravações ficam
MONITOR_DIR="/var/spool/asterisk/monitor"

# Log de limpeza
LOG_FILE="/var/log/nanosip/cleanup_recordings.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando limpeza de gravações..." >> "$LOG_FILE"

# Encontrar e remover arquivos com mais de 7 dias
find "$MONITOR_DIR" -type f -name "*.wav" -mtime +7 -print -exec rm -f {} \; >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Limpeza concluída." >> "$LOG_FILE"

