# Guida: Gestione Dati in ClickHouse

ClickHouse **non ha un'interfaccia grafica completa** per gestire i dati (come phpMyAdmin), ma offre diverse opzioni per eliminare e gestire i dati.

---

## Opzioni Disponibili

### 1. **ClickHouse Client (CLI)** - Consigliato ✅

Il modo più diretto per gestire i dati:

```bash
# Entra nel client ClickHouse
docker-compose exec clickhouse clickhouse-client

# Oppure esegui comandi direttamente
docker-compose exec clickhouse clickhouse-client --query "SHOW TABLES FROM marketing_data"
```

### 2. **Metabase** - Per Query e Visualizzazione ✅

Puoi usare Metabase per:
- ✅ Eseguire query SQL
- ✅ Visualizzare dati
- ✅ Creare dashboard
- ⚠️ **NON** puoi eliminare tabelle direttamente (solo query SELECT)

**Accesso**: http://localhost:13000

### 3. **HTTP Interface** - Per Query via Browser

ClickHouse espone un'interfaccia HTTP base su porta 8123, ma è **limitata**:
- ✅ Puoi eseguire query SQL via HTTP
- ❌ Non c'è un'interfaccia grafica completa
- ❌ Non ci sono pulsanti per eliminare tabelle

**Esempio**:
```bash
curl "http://localhost:18123/?query=SHOW+TABLES+FROM+marketing_data"
```

---

## Comandi SQL per Gestire i Dati

### Eliminare Tabelle

#### DROP TABLE (Elimina tabella e dati)

```sql
-- Elimina una tabella specifica
DROP TABLE IF EXISTS marketing_data.campaigns;

-- Elimina più tabelle
DROP TABLE IF EXISTS marketing_data.campaigns, marketing_data.ads;
```

**Via CLI**:
```bash
docker-compose exec clickhouse clickhouse-client --query "DROP TABLE IF EXISTS marketing_data.campaigns"
```

### Eliminare Dati (senza eliminare la tabella)

#### TRUNCATE TABLE (Svuota tabella)

```sql
-- Elimina tutti i dati ma mantiene la struttura
TRUNCATE TABLE marketing_data.campaigns;
```

#### DELETE FROM (Elimina record specifici)

**⚠️ Nota**: Funziona solo su ClickHouse 23.3+ o con setting abilitato.

```sql
-- Elimina record che matchano una condizione
DELETE FROM marketing_data.campaigns 
WHERE status = 'PAUSED';

-- Elimina record vecchi (es. più di 90 giorni)
DELETE FROM marketing_data.campaigns 
WHERE created_time < now() - INTERVAL 90 DAY;
```

**Via CLI**:
```bash
docker-compose exec clickhouse clickhouse-client --query "DELETE FROM marketing_data.campaigns WHERE status = 'PAUSED'"
```

#### ALTER TABLE ... DELETE (Mutation - più pesante)

```sql
-- Elimina fisicamente i dati (più lento ma più sicuro)
ALTER TABLE marketing_data.campaigns 
DELETE WHERE status = 'PAUSED';
```

### Eliminare Partizioni (se la tabella è partizionata)

```sql
-- Elimina una partizione specifica (es. dati di un mese)
ALTER TABLE marketing_data.campaigns 
DROP PARTITION '2026-01';
```

---

## Esempi Pratici

### Scenario 1: Eliminare una Tabella Completa

```bash
# Verifica che la tabella esista
docker-compose exec clickhouse clickhouse-client --query "SHOW TABLES FROM marketing_data"

# Elimina la tabella
docker-compose exec clickhouse clickhouse-client --query "DROP TABLE IF EXISTS marketing_data.campaigns"

# Verifica che sia stata eliminata
docker-compose exec clickhouse clickhouse-client --query "SHOW TABLES FROM marketing_data"
```

### Scenario 2: Svuotare una Tabella (mantenere struttura)

```bash
# Svuota tutti i dati
docker-compose exec clickhouse clickhouse-client --query "TRUNCATE TABLE marketing_data.campaigns"

# Verifica che sia vuota
docker-compose exec clickhouse clickhouse-client --query "SELECT COUNT(*) FROM marketing_data.campaigns"
```

### Scenario 3: Eliminare Record Vecchi

```bash
# Elimina record più vecchi di 30 giorni
docker-compose exec clickhouse clickhouse-client --query "DELETE FROM marketing_data.campaigns WHERE created_time < now() - INTERVAL 30 DAY"

# Verifica quanti record rimangono
docker-compose exec clickhouse clickhouse-client --query "SELECT COUNT(*) FROM marketing_data.campaigns"
```

### Scenario 4: Eliminare Record con Condizione

```bash
# Elimina campagne pausate
docker-compose exec clickhouse clickhouse-client --query "DELETE FROM marketing_data.campaigns WHERE status = 'PAUSED'"
```

---

## Gestione via Metabase

### Query SELECT (Visualizzazione)

1. Vai su **http://localhost:13000**
2. Clicca **"New"** → **"Question"**
3. Seleziona **"ClickHouse Marketing Data"**
4. Scrivi query SQL:

```sql
-- Visualizza tutte le tabelle
SHOW TABLES FROM marketing_data

-- Conta record
SELECT COUNT(*) FROM campaigns

-- Query dati
SELECT * FROM campaigns LIMIT 10
```

### ⚠️ Limitazioni Metabase

- ✅ Puoi eseguire query SELECT
- ✅ Puoi creare dashboard
- ❌ **NON** puoi eseguire DROP TABLE, DELETE, TRUNCATE
- ❌ Metabase blocca comandi DDL/DML per sicurezza

**Soluzione**: Usa il CLI per operazioni di modifica/eliminazione.

---

## Script di Gestione

Puoi creare script per automatizzare la gestione:

### Script: Elimina Tabelle Vecchie

```bash
#!/bin/bash
# elimina-tabelle-vecchie.sh

# Elimina tabelle create più di 30 giorni fa
docker-compose exec clickhouse clickhouse-client --query "
SELECT name 
FROM system.tables 
WHERE database = 'marketing_data' 
AND create_time < now() - INTERVAL 30 DAY
" | while read table; do
    echo "Eliminando tabella: $table"
    docker-compose exec clickhouse clickhouse-client --query "DROP TABLE IF EXISTS marketing_data.$table"
done
```

### Script: Backup Prima di Eliminare

```bash
#!/bin/bash
# backup-e-elimina.sh

TABLE_NAME=$1
BACKUP_DIR="./volumes/backups/clickhouse"

# Crea directory backup
mkdir -p "$BACKUP_DIR"

# Backup dati
echo "Creando backup di $TABLE_NAME..."
docker-compose exec clickhouse clickhouse-client --query "
SELECT * FROM marketing_data.$TABLE_NAME
FORMAT CSV
" > "$BACKUP_DIR/${TABLE_NAME}_$(date +%Y%m%d_%H%M%S).csv"

# Elimina tabella
echo "Eliminando tabella $TABLE_NAME..."
docker-compose exec clickhouse clickhouse-client --query "DROP TABLE IF EXISTS marketing_data.$TABLE_NAME"

echo "Backup salvato in: $BACKUP_DIR"
```

---

## Best Practices

### 1. Backup Prima di Eliminare

```bash
# Backup completo database
docker-compose exec clickhouse clickhouse-client --query "
BACKUP DATABASE marketing_data 
TO Disk('backups', 'marketing_data_backup_$(date +%Y%m%d)')
"
```

### 2. Verifica Prima di Eliminare

```bash
# Conta record prima di eliminare
docker-compose exec clickhouse clickhouse-client --query "SELECT COUNT(*) FROM marketing_data.campaigns"

# Visualizza alcuni record
docker-compose exec clickhouse clickhouse-client --query "SELECT * FROM marketing_data.campaigns LIMIT 5"
```

### 3. Usa IF EXISTS

Sempre usa `IF EXISTS` per evitare errori:

```sql
DROP TABLE IF EXISTS marketing_data.campaigns;  -- ✅ Buono
DROP TABLE marketing_data.campaigns;           -- ❌ Può dare errore se non esiste
```

### 4. Monitora Spazio

```sql
-- Verifica spazio utilizzato
SELECT 
    table,
    formatReadableSize(sum(bytes)) as size,
    sum(rows) as rows
FROM system.parts
WHERE database = 'marketing_data'
GROUP BY table
ORDER BY sum(bytes) DESC;
```

---

## Riepilogo Opzioni

| Metodo | Eliminare Tabelle | Eliminare Dati | Query SELECT | Interfaccia Grafica |
|--------|-------------------|----------------|--------------|---------------------|
| **CLI** | ✅ | ✅ | ✅ | ❌ |
| **Metabase** | ❌ | ❌ | ✅ | ✅ |
| **HTTP API** | ✅ | ✅ | ✅ | ❌ |

---

## Raccomandazione

Per gestire i dati in ClickHouse:

1. **Per query e visualizzazione**: Usa **Metabase** (http://localhost:13000)
2. **Per eliminare/modificare**: Usa **CLI** (`clickhouse-client`)
3. **Per automazione**: Crea **script bash**

---

## Comandi Utili

```bash
# Lista tabelle
docker-compose exec clickhouse clickhouse-client --query "SHOW TABLES FROM marketing_data"

# Conta record in tutte le tabelle
docker-compose exec clickhouse clickhouse-client --query "
SELECT table, COUNT(*) as records 
FROM (
    SELECT 'campaigns' as table, COUNT(*) FROM marketing_data.campaigns
    UNION ALL SELECT 'ads', COUNT(*) FROM marketing_data.ads
    UNION ALL SELECT 'ad_sets', COUNT(*) FROM marketing_data.ad_sets
    UNION ALL SELECT 'ad_creatives', COUNT(*) FROM marketing_data.ad_creatives
) GROUP BY table
"

# Spazio utilizzato
docker-compose exec clickhouse clickhouse-client --query "
SELECT 
    formatReadableSize(sum(bytes)) as total_size
FROM system.parts
WHERE database = 'marketing_data'
"

# Elimina tabella
docker-compose exec clickhouse clickhouse-client --query "DROP TABLE IF EXISTS marketing_data.campaigns"
```

---

## Conclusione

ClickHouse è **ottimizzato per performance** (query analitiche veloci), ma la gestione dati avviene principalmente via **SQL/CLI**, non tramite interfaccia grafica completa.

**Usa**:
- ✅ **Metabase** per query e visualizzazione
- ✅ **CLI** per eliminare/modificare dati
- ✅ **Script** per automazione
