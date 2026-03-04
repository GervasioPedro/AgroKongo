#!/bin/bash
# =============================================================================
# Script de Backup Automatizado - AgroKongo
# Executar via cron: 0 2 * * * /app/scripts/backup.sh >> /var/log/backup.log 2>&1
# =============================================================================

set -euo pipefail

# Configurações
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${DB_NAME:-agrokongo}"
DB_USER="${DB_USER:-agrokongo}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
LOG_FILE="${LOG_FILE:-/var/log/backup.log}"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "Iniciando backup - AgroKongo"
log "========================================="

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

# -----------------------------------------------------------------------------
# 1. Backup do PostgreSQL
# -----------------------------------------------------------------------------
log "Iniciando backup do PostgreSQL..."

if [ -n "${DATABASE_URL:-}" ]; then
    # Extrair informações de conexão da URL
    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^/]+)/.*|\1|' | cut -d':' -f1)
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*@([^/]+)/.*|\1|' | cut -d':' -f2)
    DB_PASS=$(echo "$DATABASE_URL" | sed -E 's|.*:([^@]+)@.*|\1|')
    
    export PGPASSWORD="$DB_PASS"
    
    # Backup com compressão
    pg_dump -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "$DB_USER" "$DB_NAME" | \
        gzip > "$BACKUP_DIR/db_${DATE}.sql.gz"
    
    if [ $? -eq 0 ]; then
        log "Backup do PostgreSQL concluído: db_${DATE}.sql.gz"
    else
        log "ERRO: Falha no backup do PostgreSQL"
        exit 1
    fi
else
    log "AVISO: DATABASE_URL não definido, ignorando backup do PostgreSQL"
fi

# -----------------------------------------------------------------------------
# 2. Backup de ficheiros (uploads e dados)
# -----------------------------------------------------------------------------
log "Iniciando backup de ficheiros..."

DATA_STORAGE="${DATA_STORAGE:-./data_storage}"
if [ -d "$DATA_STORAGE" ]; then
    tar -czf "$BACKUP_DIR/files_${DATE}.tar.gz" -C "$(dirname "$DATA_STORAGE")" "$(basename "$DATA_STORAGE")"
    
    if [ $? -eq 0 ]; then
        log "Backup de ficheiros concluído: files_${DATE}.tar.gz"
    else
        log "ERRO: Falha no backup de ficheiros"
    fi
else
    log "AVISO: Diretório $DATA_STORAGE não encontrado, ignorando"
fi

# -----------------------------------------------------------------------------
# 3. Backup de configurações (sem segredos)
# -----------------------------------------------------------------------------
log "Criando backup de configurações..."

tar -czf "$BACKUP_DIR/config_${DATE}.tar.gz" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='data_storage' \
    --exclude='*.log' \
    --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='venv' \
    . 2>/dev/null || true

if [ $? -eq 0 ]; then
    log "Backup de configurações concluído: config_${DATE}.tar.gz"
fi

# -----------------------------------------------------------------------------
# 4. Limpeza de backups antigos
# -----------------------------------------------------------------------------
log "Limpando backups com mais de $RETENTION_DAYS dias..."

find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete

# Contar backups restantes
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*.gz" | wc -l)
log "Backups restantes: $BACKUP_COUNT"

# -----------------------------------------------------------------------------
# 5. Verificação de integridade (opcional)
# -----------------------------------------------------------------------------
log "Verificando integridade dos backups..."

for backup in "$BACKUP_DIR"/db_${DATE}.sql.gz; do
    if [ -f "$backup" ]; then
        if gzip -t "$backup" 2>/dev/null; then
            BACKUP_SIZE=$(du -h "$backup" | cut -f1)
            log "Backup verificado: $backup ($BACKUP_SIZE)"
        else
            log "ERRO: Backup corrompido: $backup"
            exit 1
        fi
    fi
done

# -----------------------------------------------------------------------------
# 6. Notificação de sucesso (opcional - configurar webhook)
# -----------------------------------------------------------------------------
if [ -n "${BACKUP_WEBHOOK:-}" ]; then
    curl -s -X POST "$BACKUP_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{\"status\": \"success\", \"date\": \"$DATE\", \"backups\": $BACKUP_COUNT}" || true
fi

log "========================================="
log "Backup concluído com sucesso!"
log "Data: $DATE"
log "========================================="

# Listar arquivos de backup
ls -lh "$BACKUP_DIR" | tail -5
