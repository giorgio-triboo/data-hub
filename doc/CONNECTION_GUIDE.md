# Guida alle Connessioni: Airbyte → Parquet → Metabase

Questa guida spiega come collegare:
1. **Airbyte** → **MinIO (Parquet)**: Scrittura dati marketing in formato Parquet
2. **Parquet (MinIO)** → **Metabase**: Lettura dati Parquet per visualizzazione

---

## 1. Airbyte → MinIO (Parquet)

### Prerequisiti
- MinIO deve essere avviato e accessibile
- Bucket creato in MinIO per i dati Parquet

### Step 1: Configurare MinIO

1. **Accedi alla Console MinIO**:
   - URL: http://localhost:19001
   - Username: `minioadmin` (o `MINIO_ROOT_USER` dal file `.env`)
   - Password: `minioadmin_secure_pass_CHANGE_THIS` (o `MINIO_ROOT_PASSWORD` dal file `.env`)

2. **Crea un Bucket**:
   - Clicca su "Buckets" nel menu laterale
   - Clicca "Create Bucket"
   - Nome bucket: `marketing-data` (o altro nome preferito)
   - Clicca "Create Bucket"

### Step 2: Configurare Destination S3 in Airbyte

1. **Accedi ad Airbyte**:
   - URL: http://localhost:8000
   - Crea account admin se è il primo accesso

2. **Crea una nuova Destination**:
   - Vai su "Destinations" nel menu
   - Clicca "New Destination"
   - Cerca e seleziona **"S3"** o **"Amazon S3"**

3. **Configurazione S3 Destination**:
   
   **⚠️ IMPORTANTE - Scelta Endpoint**:
   - Se Airbyte è nella stessa rete Docker di MinIO (gestito via docker-compose): usa `http://minio:9000`
   - Se Airbyte è installato con `abctl` (gestito separatamente): usa `http://host.docker.internal:19000` o `http://localhost:19000`
   
   ```
   Destination Name: MinIO Marketing Data
   
   S3 Bucket Name: marketing-data
   S3 Bucket Path: marketing/  (⚠️ NON iniziare con /, MinIO non lo supporta)
   S3 Bucket Region: us-east-1 (qualsiasi, MinIO ignora questo)
   S3 Endpoint: http://minio:9000  (o http://host.docker.internal:19000 se abctl)
   Access Key ID: minioadmin  (o MINIO_ROOT_USER dal .env)
   Secret Access Key: minioadmin_secure_pass_CHANGE_THIS  (o MINIO_ROOT_PASSWORD dal .env)
   
   Format: Parquet
   Part Size: 10 (MB)
   ```

4. **Configurazione Output Format Parquet**:
   ```
   Format: Parquet
   Compression Codec: SNAPPY (consigliato) o GZIP
   Block Size: 128 MB
   Max Page Size: 8 MB
   ```

5. **⚠️ IMPORTANTE - Organizzare File per Data (S3 Path Format)**:
   
   Per organizzare i file per data (anno/mese/giorno), devi usare il campo **"S3 Path Format"** (NON "File Name Pattern"):
   
   ```
   S3 Path Format: ${NAMESPACE}/${STREAM_NAME}/${YEAR}/${MONTH}/${DAY}/
   ```
   
   **Variabili disponibili**:
   - `${NAMESPACE}`: Nome della sorgente (es. "facebook_marketing")
   - `${STREAM_NAME}`: Nome dello stream (es. "ad_account", "ad_sets")
   - `${YEAR}`: Anno (es. "2026")
   - `${MONTH}`: Mese (es. "01", "02", ...)
   - `${DAY}`: Giorno (es. "01", "02", ...)
   - `${EPOCH}`: Timestamp Unix (opzionale, per unicità)
   
   **Esempi di S3 Path Format**:
   - Organizzazione per giorno: `${NAMESPACE}/${STREAM_NAME}/${YEAR}/${MONTH}/${DAY}/`
   - Organizzazione per mese: `${NAMESPACE}/${STREAM_NAME}/${YEAR}/${MONTH}/`
   - Con timestamp: `${NAMESPACE}/${STREAM_NAME}/${YEAR}_${MONTH}_${DAY}_${EPOCH}_`
   
   **⚠️ ERRORE COMUNE**: Non usare `{date:yyyy}` nel campo "File Name Pattern" - questo viene interpretato letteralmente e crea cartelle chiamate `{date:yyyy}` invece di sostituire con l'anno!
   
   **Nota**: Se lasci "S3 Path Format" vuoto, Airbyte userà il formato predefinito che non organizza per data.

6. **Test e Salva**:
   - Clicca "Test" per verificare la connessione
   - Se il test passa, clicca "Set up destination"

### Step 3: Creare una Connection

1. **Crea una Source** (esempio: API marketing):
   - Vai su "Sources"
   - Seleziona la tua sorgente (es. Google Analytics, Facebook Ads, etc.)
   - Configura le credenziali

2. **Crea Connection**:
   - Vai su "Connections"
   - Clicca "New Connection"
   - Seleziona la Source creata
   - Seleziona la Destination "MinIO Marketing Data"
   - Configura la sincronizzazione:
     - **Sync Frequency**: Daily, Hourly, o Manual
     - **Sync Mode**: Full Refresh o Incremental Append
   - Clicca "Set up connection"

3. **Avvia Sync**:
   - Dalla pagina Connection, clicca "Sync Now"
   - I dati verranno scritti in formato Parquet su MinIO

### Verifica Dati su MinIO

1. **Tramite Console MinIO**:
   - Vai su http://localhost:19001
   - Seleziona il bucket `marketing-data`
   - Dovresti vedere i file `.parquet` nella struttura (se hai configurato S3 Path Format):
     ```
     marketing-data/
     └── marketing/
         └── [source_name]/
             └── [stream_name]/
                 └── 2026/
                     └── 01/
                         └── 17/
                             └── [timestamp]_[partition].parquet
     ```
   
   **⚠️ Se vedi cartelle chiamate `{date:yyyy}`, `{date:MM}`, `{date:dd}`**:
   - Significa che hai usato il pattern sbagliato
   - Vedi la sezione "Troubleshooting" qui sotto per la soluzione

2. **Tramite MinIO Client (mc)**:
   ```bash
   # Entra nel container MinIO
   docker-compose exec minio bash
   
   # Oppure installa mc localmente
   # macOS: brew install minio/stable/mc
   
   # Configura alias (usa i valori dal tuo .env)
   mc alias set local http://localhost:19000 minioadmin minioadmin_secure_pass_CHANGE_THIS
   
   # Lista bucket
   mc ls local/
   
   # Lista file nel bucket
   mc ls local/marketing-data --recursive
   ```

---

## 2. Parquet (MinIO) → Metabase

Metabase può leggere file Parquet da MinIO in diversi modi. Ecco le opzioni:

### Opzione A: Usando Presto/Trino (Consigliato)

Presto/Trino è un query engine che può leggere Parquet da S3-compatible storage.

#### Step 1: Aggiungere Presto/Trino al docker-compose.yml

Aggiungi questo servizio al `docker-compose.yml`:

```yaml
presto:
  image: trinodb/trino:latest
  container_name: datahub-presto
  restart: unless-stopped
  depends_on:
    - minio
  ports:
    - "8081:8080"
  volumes:
    - ./presto/config:/etc/trino
  environment:
    - JVM_OPTS=-Xmx2G
  networks:
    - datahub-network
```

#### Step 2: Configurare Presto per MinIO

Crea `presto/config/catalog/minio.properties`:

```properties
connector.name=hive
hive.metastore=file
hive.metastore.catalog.dir=file:///tmp/presto/metastore
hive.s3.endpoint=http://minio:9000
hive.s3.aws-access-key=minioadmin  # o MINIO_ROOT_USER dal .env
hive.s3.aws-secret-key=minioadmin_secure_pass_CHANGE_THIS  # o MINIO_ROOT_PASSWORD dal .env
hive.s3.path-style-access=true
hive.s3.ssl.enabled=false
```

#### Step 3: Collegare Metabase a Presto

**IMPORTANTE**: Usa **"Starburst (Trino)"** invece di "Presto" per evitare problemi di autenticazione!

1. **In Metabase**:
   - Vai su "Admin" → "Databases"
   - Clicca "Add Database"
   - Seleziona **"Starburst (Trino)"** (NON "Presto" - il driver Presto vecchio non funziona bene con Trino moderno)

2. **Configurazione**:
   ```
   Display Name: Presto (Parquet Data)
   Host: presto (se Metabase è nello stesso Docker network) oppure localhost (se accedi dall'host)
   Port: 8080 (porta interna del container) oppure 18081 (se accedi dall'host)
   Catalog: default (o minio per il catalogo MinIO)
   Schema: (lascia vuoto o usa "default")
   Username: trino (obbligatorio - usa qualsiasi valore, es: "trino", "admin", "user")
   Password: (lascia vuoto - Trino non richiede autenticazione)
   ```
   
   **Note importanti**: 
   - Usa **"Starburst (Trino)"** come tipo database, NON "Presto"
   - Il driver JDBC di Trino richiede che il campo "Username" non sia vuoto, anche se Trino non richiede autenticazione
   - Se Metabase è nello stesso Docker network, usa `presto` come host e `8080` come porta
   - Se accedi a Metabase dall'host (browser), usa `localhost` come host e `18081` come porta
   - Il campo si chiama "Catalog" non "Database" quando usi Starburst (Trino)

3. **Test e Salva**:
   - Clicca "Test Connection"
   - Se funziona, salva

### Opzione B: Usando Spark + JDBC (Alternativa)

Spark può leggere Parquet e esporre dati via JDBC.

### Opzione C: Usando Metabase S3 Connector (Se disponibile)

Alcune versioni di Metabase supportano direttamente S3:

1. **In Metabase**:
   - Vai su "Admin" → "Databases"
   - Clicca "Add Database"
   - Cerca "S3" o "Amazon S3"

2. **Configurazione**:
   ```
   Display Name: MinIO Parquet Data
   Endpoint: http://minio:9000
   Access Key: minioadmin  (o MINIO_ROOT_USER dal .env)
   Secret Key: minioadmin_secure_pass_CHANGE_THIS  (o MINIO_ROOT_PASSWORD dal .env)
   Bucket: marketing-data
   ```

**Nota**: Questo metodo potrebbe non essere disponibile in tutte le versioni di Metabase.

### Opzione D: Script Python per ETL (Soluzione Custom)

Crea uno script Python che legge Parquet da MinIO e scrive in MySQL:

```python
import boto3
import pandas as pd
import pyarrow.parquet as pq
from io import BytesIO

# Configurazione MinIO (usa i valori dal tuo .env)
s3_client = boto3.client(
    's3',
    endpoint_url='http://localhost:19000',  # Porta esterna
    aws_access_key_id='minioadmin',  # o MINIO_ROOT_USER dal .env
    aws_secret_access_key='minioadmin_secure_pass_CHANGE_THIS'  # o MINIO_ROOT_PASSWORD dal .env
)

# Leggi file Parquet
bucket = 'marketing-data'
key = 'marketing/source_name/stream_name/date/file.parquet'

obj = s3_client.get_object(Bucket=bucket, Key=key)
df = pd.read_parquet(BytesIO(obj['Body'].read()))

# Scrivi in MySQL
from sqlalchemy import create_engine
engine = create_engine('mysql://user:pass@mysql:3306/datahub_crud')
df.to_sql('marketing_data', engine, if_exists='append', index=False)
```

Poi Metabase legge direttamente da MySQL.

---

## 3. Configurazione Completa Consigliata

### Architettura Finale

```
┌─────────────┐
│   Sources   │ (Google Analytics, Facebook Ads, etc.)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Airbyte   │
└──────┬──────┘
       │
       ├───▶ ┌──────────┐      ┌──────────┐
       │     │  MinIO   │─────▶│ Parquet  │
       │     │  (S3)    │      │  Files   │
       │     └──────────┘      └──────────┘
       │                              │
       │                              ▼
       │                         ┌──────────┐
       │                         │ Presto/  │
       │                         │ Trino    │
       │                         └────┬─────┘
       │                              │
       └───▶ ┌──────────┐            │
             │  MySQL   │◄───────────┘
             │  (CRUD)  │
             └────┬─────┘
                  │
                  ▼
             ┌──────────┐
             │ Metabase │
             └──────────┘
```

### Flusso Dati

1. **Airbyte** sincronizza dati da sorgenti marketing
2. **Airbyte** scrive in **MinIO** come file Parquet
3. **Presto/Trino** legge Parquet da MinIO e li espone come tabelle SQL
4. **Metabase** si connette a **Presto/Trino** per query analitiche
5. **Metabase** si connette anche a **MySQL** per dati operativi CRUD

---

## 4. Query Example

### Query Parquet tramite Presto/Trino

```sql
-- In Metabase, usando la connessione Presto
SELECT 
    date,
    campaign_name,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    SUM(cost) as total_cost
FROM marketing_data.campaigns
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date, campaign_name
ORDER BY date DESC
```

### Query MySQL (CRUD)

```sql
-- In Metabase, usando la connessione MySQL
SELECT 
    user_id,
    action_type,
    COUNT(*) as action_count
FROM user_actions
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY user_id, action_type
```

---

## 5. Troubleshooting

### Problema: Errore "System call failure" o "HttpException" durante Check

**Sintomi**:
```
WARN Caught throwable during CHECK aws.smithy.kotlin.runtime.http.HttpException: 
software.amazon.awssdk.crt.http.HttpException: System call failure.
```

**Cause Possibili**:
1. **Endpoint errato**: L'endpoint non è raggiungibile dalla rete di Airbyte
2. **Porta sbagliata**: Uso della porta interna invece di quella esterna (o viceversa)
3. **Problema di rete Docker**: Airbyte e MinIO non sono nella stessa rete
4. **AWS CRT incompatibilità**: Il nuovo SDK AWS può avere problemi con endpoint HTTP non-standard

**Soluzioni**:

#### Soluzione 1: Verifica Endpoint Corretto

**Se Airbyte è gestito con `abctl` (installazione separata)**:
- Usa: `http://host.docker.internal:19000` (macOS/Windows)
- Oppure: `http://localhost:19000` (se funziona)
- **NON usare**: `http://minio:9000` (non risolvibile se non nella stessa rete)

**Se Airbyte è in docker-compose nella stessa rete**:
- Usa: `http://minio:9000` (porta interna del container)
- **NON usare**: `http://localhost:19000` (non funziona da dentro Docker)

#### Soluzione 2: Verifica Connessione di Rete

```bash
# Verifica che MinIO sia raggiungibile
docker-compose ps minio

# Testa connessione da host
curl http://localhost:19000/minio/health/live

# Se Airbyte è in Docker, testa da dentro il container Airbyte
docker-compose exec airbyte-worker curl http://minio:9000/minio/health/live
```

#### Soluzione 3: Verifica Porte

Dal `docker-compose.yml`:
- **Porta esterna (host)**: `19000` → `http://localhost:19000`
- **Porta interna (container)**: `9000` → `http://minio:9000`

#### Soluzione 4: Forza Path-Style Access

Se il problema persiste, assicurati che la configurazione S3 abbia:
- **Path-Style Access**: Abilitato (se disponibile nell'interfaccia)
- **Force Path Style**: `true` (se configurabile)

#### Soluzione 5: Usa Endpoint Alternativo

Prova questi endpoint in ordine:
1. `http://host.docker.internal:19000` (per abctl)
2. `http://172.17.0.1:19000` (IP bridge Docker su Linux)
3. `http://localhost:19000` (se Airbyte può accedere all'host)

### Problema: Errore "Failed to write to S3 bucket" durante Check

**Sintomi**:
```
WARN Caught throwable during CHECK java.lang.IllegalStateException: Failed to write to S3 bucket
INFO Successfully removed test file  (la connessione funziona, ma la scrittura fallisce)
```

**Cause Possibili**:
1. **Bucket Path errato**: Il path inizia con `/` che può causare problemi con MinIO
2. **Bucket non esiste**: Il bucket specificato non è stato creato
3. **Permessi insufficienti**: Le credenziali non hanno permessi di scrittura
4. **Formato path non valido**: Caratteri speciali o formato non supportato nel path

**Soluzioni**:

#### Soluzione 1: Verifica e Corregge il Bucket Path

**⚠️ IMPORTANTE**: Il `S3 Bucket Path` NON deve iniziare con `/` quando si usa MinIO!

**Sbagliato**:
```
S3 Bucket Path: /marketing/
```

**Corretto**:
```
S3 Bucket Path: marketing/
```
oppure
```
S3 Bucket Path: marketing
```

Il path viene automaticamente prefissato, quindi non serve il `/` iniziale.

#### Soluzione 2: Verifica che il Bucket Esista

```bash
# Tramite Console MinIO
# Vai su http://localhost:19001 e verifica che il bucket esista

# Oppure tramite CLI
mc ls local/
```

#### Soluzione 3: Verifica Permessi del Bucket

1. Vai su http://localhost:19001
2. Seleziona il bucket
3. Vai su "Access Policy"
4. Assicurati che le credenziali usate abbiano permessi di scrittura

#### Soluzione 4: Testa Scrittura Manuale

```bash
# Testa se puoi scrivere nel bucket
echo "test" | mc pipe local/marketing-data/test.txt
mc cat local/marketing-data/test.txt
mc rm local/marketing-data/test.txt
```

#### Soluzione 5: Usa Path Semplice

Se il problema persiste, prova con un path più semplice:
```
S3 Bucket Path: (lascia vuoto)
```

Poi organizza i dati dopo con script o policy MinIO.

### Problema: File Organizzati in Cartelle con Nome Letterale `{date:yyyy}`, `{date:MM}`, `{date:dd}`

**Sintomi**:
- Su MinIO vedi cartelle chiamate letteralmente `{date:yyyy}`, `{date:MM}`, `{date:dd}`
- I file non sono organizzati per data reale (es. `2026/01/17/`)
- La struttura è: `marketing-data/marketing/stream_name/{date:yyyy}/{date:MM}/{date:dd}/...`

**Causa**:
- Hai usato il campo sbagliato o il formato sbagliato per organizzare i file per data
- Il campo "File Name Pattern" NON organizza il path, solo il nome del file
- Il pattern `{date:yyyy}` non è supportato in Airbyte S3 destination

**Soluzione**:

1. **Usa il campo "S3 Path Format"** (non "File Name Pattern"):
   - Vai nella configurazione della Destination S3 in Airbyte
   - Cerca il campo **"S3 Path Format"** (potrebbe essere in una sezione avanzata)
   - Inserisci: `${NAMESPACE}/${STREAM_NAME}/${YEAR}/${MONTH}/${DAY}/`

2. **Variabili corrette da usare**:
   - ✅ `${YEAR}` → Anno (es. "2026")
   - ✅ `${MONTH}` → Mese (es. "01", "02")
   - ✅ `${DAY}` → Giorno (es. "01", "02")
   - ✅ `${NAMESPACE}` → Nome sorgente
   - ✅ `${STREAM_NAME}` → Nome stream
   - ❌ `{date:yyyy}` → NON funziona, viene interpretato letteralmente

3. **Pulisci i file vecchi** (opzionale):
   ```bash
   # Elimina le cartelle con pattern letterale
   docker-compose exec minio mc rm --recursive --force local/marketing-data/marketing/stream_name/{date:yyyy}
   ```

4. **Riconfigura e risincronizza**:
   - Modifica la Destination con il "S3 Path Format" corretto
   - Esegui una nuova sync
   - I nuovi file saranno organizzati correttamente: `2026/01/17/...`

**Esempio di configurazione corretta**:
```
S3 Bucket Path: marketing/
S3 Path Format: ${NAMESPACE}/${STREAM_NAME}/${YEAR}/${MONTH}/${DAY}/
File Name Pattern: {timestamp}_{part_number}  (opzionale, solo per il nome file)
```

**Risultato atteso**:
```
marketing-data/
└── marketing/
    └── facebook_marketing/
        └── ad_account/
            └── 2026/
                └── 01/
                    └── 17/
                        └── 1768612497647_0_...
```

### Problema: Airbyte non riesce a connettersi a MinIO

**Soluzione**:
- Verifica che MinIO sia avviato: `docker-compose ps minio`
- Verifica endpoint corretto (vedi sopra)
- Verifica credenziali nel `.env`
- Testa connessione: `curl http://localhost:19000/minio/health/live`
- Verifica che Airbyte e MinIO siano nella stessa rete Docker (se gestiti via docker-compose)

### Problema: Errore "Failed to write to S3 bucket" durante Check

**Sintomi**:
```
WARN Caught throwable during CHECK java.lang.IllegalStateException: Failed to write to S3 bucket
INFO Successfully removed test file  (la connessione funziona, ma la scrittura fallisce)
```

**Cause Principale**: Il `S3 Bucket Path` inizia con `/` che MinIO non supporta correttamente.

**Soluzione**:
- **Rimuovi il `/` iniziale** dal Bucket Path:
  - ❌ Sbagliato: `/marketing/` o `/airbyte/`
  - ✅ Corretto: `marketing/` o `airbyte/`
- Verifica che il bucket esista in MinIO
- Testa scrittura manuale: `echo "test" | mc pipe local/bucket-name/test.txt`

### Problema: File Parquet non visibili in MinIO

**Soluzione**:
- Verifica che la sync di Airbyte sia completata
- Controlla i log: `docker-compose logs airbyte-worker`
- Verifica path del bucket in Airbyte destination config (senza `/` iniziale)

### Problema: Metabase non vede dati da Presto

**Soluzione**:
- Verifica che Presto sia avviato: `docker-compose ps presto`
- Controlla catalog config in Presto
- Verifica che i file Parquet siano nel path corretto
- Testa query direttamente su Presto: `http://localhost:8081`

### Problema: Performance lente su query Parquet

**Soluzione**:
- Usa partizionamento intelligente in Airbyte (per data, per stream)
- Considera di aggregare dati in MySQL per query frequenti
- Usa compressione SNAPPY invece di GZIP per migliori performance
- Aumenta memoria Presto se disponibile

---

## 6. Best Practices

1. **Partizionamento Dati**:
   - Organizza Parquet per data: `marketing-data/YYYY/MM/DD/`
   - Usa naming convention consistente

2. **Compressione**:
   - Usa SNAPPY per balance tra compressione e performance
   - Usa GZIP se spazio disco è critico

3. **Sincronizzazione**:
   - Configura sync incrementali quando possibile
   - Usa full refresh solo per dati storici iniziali

4. **Monitoring**:
   - Monitora spazio disco MinIO
   - Monitora performance query Presto
   - Setup alerting per sync falliti

5. **Backup**:
   - Backup regolari dei file Parquet
   - Considera versioning su MinIO

---

## 7. Risorse Utili

- [Airbyte S3 Destination Docs](https://docs.airbyte.com/integrations/destinations/s3)
- [MinIO Documentation](https://min.io/docs/)
- [Presto/Trino Documentation](https://trino.io/docs/)
- [Metabase Database Connections](https://www.metabase.com/docs/latest/administration-guide/databases)

---

---

## 8. Note Tecniche: Endpoint e Porte

### Configurazione Porte MinIO

Dal `docker-compose.yml`:
- **Porta S3 API esterna**: `19000` (mappata da `9000` interna)
- **Porta Console esterna**: `19001` (mappata da `9001` interna)
- **Porta S3 API interna**: `9000` (usata tra container nella stessa rete)
- **Porta Console interna**: `9001` (usata tra container nella stessa rete)

### Scelta Endpoint in Base all'Installazione

| Scenario | Endpoint da Usare | Note |
|----------|------------------|------|
| Airbyte via `abctl` (separato) | `http://host.docker.internal:19000` | Accesso da container all'host |
| Airbyte in docker-compose (stessa rete) | `http://minio:9000` | Accesso diretto tra container |
| Airbyte locale (non Docker) | `http://localhost:19000` | Accesso diretto all'host |

### Verifica Rete Docker

```bash
# Verifica che i container siano nella stessa rete
docker network inspect datahub-network

# Verifica che MinIO sia raggiungibile
docker-compose exec minio curl http://localhost:9000/minio/health/live
```

---

**Ultimo aggiornamento**: 2026-01-17
