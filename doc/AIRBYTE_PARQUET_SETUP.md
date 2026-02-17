# Guida Rapida: Collegare Airbyte al Volume Parquet

Questa guida ti mostra come configurare Airbyte per scrivere file Parquet su MinIO (il tuo volume Parquet).

## Prerequisiti

1. ✅ MinIO deve essere avviato: `docker-compose ps minio`
2. ✅ Airbyte deve essere avviato: `abctl local status`
3. ✅ Bucket creato in MinIO (vedi sotto)

---

## Step 1: Creare il Bucket in MinIO

### Opzione A: Tramite Console Web

1. Apri http://localhost:19001
2. Login con:
   - Username: `minioadmin` (o `MINIO_ROOT_USER` dal file `.env`)
   - Password: `minioadmin_secure_pass_CHANGE_THIS` (o `MINIO_ROOT_PASSWORD` dal file `.env`)
3. Vai su **Buckets** → **Create Bucket**
4. Nome: `parquet-data` (o altro nome)
5. Clicca **Create Bucket**

### Opzione B: Tramite MinIO Client

```bash
# Installa mc se non ce l'hai
brew install minio/stable/mc  # macOS

   # Configura alias (usa i valori dal tuo .env)
   mc alias set local http://localhost:19000 minioadmin minioadmin_secure_pass_CHANGE_THIS

# Crea bucket
mc mb local/parquet-data
```

---

## Step 2: Configurare Destination in Airbyte

### 2.1 Seleziona il Connettore

Dalla schermata che vedi:

1. **Cerca "S3"** nella barra di ricerca
2. Seleziona **"S3 Data Lake"** (consigliato per Parquet) oppure **"S3"**
3. Clicca sul connettore

### 2.2 Configurazione Base

Compila i campi:

```
Destination name: MinIO Parquet Storage

S3 Bucket Name: parquet-data
S3 Bucket Path: airbyte/  (⚠️ NON iniziare con /, MinIO non lo supporta)
S3 Bucket Region: us-east-1  (qualsiasi, MinIO ignora)
S3 Endpoint: http://host.docker.internal:19000
```

**⚠️ IMPORTANTE**: 
- Se Airbyte è nella stessa rete Docker di MinIO, usa: `http://minio:9000`
- Se Airbyte è installato separatamente (con abctl), usa: `http://host.docker.internal:19000`

### 2.3 Credenziali

```
Access Key ID: minioadmin  (o MINIO_ROOT_USER dal .env)
Secret Access Key: minioadmin_secure_pass_CHANGE_THIS  (o MINIO_ROOT_PASSWORD dal .env)
```

**⚠️ IMPORTANTE**: Usa sempre i valori dal tuo file `.env`, non i valori di default!

### 2.4 Formato Parquet

Cerca la sezione **"Format"** o **"Output Format"**:

```
Format: Parquet
Compression Codec: SNAPPY  (consigliato per performance)
Block Size: 128 MB
Max Page Size: 8 MB
```

### 2.5 Test e Salva

1. Clicca **"Test connection"** o **"Test"**
2. Se il test passa ✅, clicca **"Set up destination"** o **"Save"**

---

## Step 3: Verificare la Connessione

### Test da Airbyte

1. Vai su **Connections**
2. Crea una nuova Connection:
   - Seleziona una Source (es. Google Analytics, API, Database)
   - Seleziona la Destination appena creata
   - Configura sync frequency
   - Clicca **"Set up connection"**
3. Avvia una sync manuale: **"Sync Now"**

### Verifica File su MinIO

**Tramite Console Web:**
1. Vai su http://localhost:19001
2. Apri il bucket `parquet-data`
3. Dovresti vedere la struttura:
   ```
   parquet-data/
   └── airbyte/
       └── [source_name]/
           └── [stream_name]/
               └── [date]/
                   └── [timestamp]_[partition].parquet
   ```

**Tramite CLI:**
```bash
mc ls local/parquet-data --recursive
```

---

## Troubleshooting

### ❌ Errore "System call failure" o "HttpException" durante Check

**Sintomi**:
```
WARN Caught throwable during CHECK aws.smithy.kotlin.runtime.http.HttpException: 
software.amazon.awssdk.crt.http.HttpException: System call failure.
```

**Causa**: Problema di connessione tra Airbyte e MinIO, spesso dovuto a endpoint o porta errata.

**Soluzioni**:

1. **Verifica Endpoint Corretto**:
   - Se Airbyte è gestito con `abctl`: usa `http://host.docker.internal:19000`
   - Se Airbyte è in docker-compose: usa `http://minio:9000`
   - **NON mescolare**: porta interna (9000) con esterna (19000) o viceversa

2. **Testa Connessione**:
   ```bash
   # Da host
   curl http://localhost:19000/minio/health/live
   
   # Se Airbyte è in Docker, testa da dentro
   docker-compose exec airbyte-worker curl http://minio:9000/minio/health/live
   ```

3. **Prova Endpoint Alternativi** (in ordine):
   - `http://host.docker.internal:19000` (per abctl su macOS/Windows)
   - `http://172.17.0.1:19000` (IP bridge Docker su Linux)
   - `http://localhost:19000` (se Airbyte può accedere all'host)

4. **Verifica Rete Docker**:
   ```bash
   # Verifica che MinIO sia nella rete corretta
   docker network inspect datahub-network | grep minio
   ```

**Nota**: Anche se vedi un warning, il check può comunque completarsi con successo (exit code 0). Se la sync funziona, puoi ignorare il warning.

### ❌ Errore "Failed to write to S3 bucket" durante Check

**Sintomi**:
```
WARN Caught throwable during CHECK java.lang.IllegalStateException: Failed to write to S3 bucket
INFO Successfully removed test file  (la connessione funziona, ma la scrittura fallisce)
```

**Causa**: Il `S3 Bucket Path` inizia con `/` che MinIO non supporta correttamente.

**Soluzione**:
1. **Rimuovi il `/` iniziale** dal Bucket Path:
   - ❌ Sbagliato: `/airbyte/` o `/marketing/`
   - ✅ Corretto: `airbyte/` o `marketing/`

2. **Verifica che il bucket esista**:
   ```bash
   mc ls local/
   ```

3. **Testa scrittura manuale**:
   ```bash
   echo "test" | mc pipe local/parquet-data/test.txt
   mc cat local/parquet-data/test.txt
   mc rm local/parquet-data/test.txt
   ```

**⚠️ IMPORTANTE**: MinIO tratta i path che iniziano con `/` in modo diverso da AWS S3. Sempre usare path relativi senza `/` iniziale.

### ❌ Test Connection Fallisce

**Problema**: Airbyte non riesce a connettersi a MinIO

**Soluzioni**:
1. Verifica che MinIO sia avviato:
   ```bash
   docker-compose ps minio
   ```

2. Verifica l'endpoint:
   - Se Airbyte è gestito da `abctl` (separato): usa `http://host.docker.internal:19000`
   - Se Airbyte è nella stessa rete Docker: usa `http://minio:9000`

3. Testa MinIO direttamente:
   ```bash
   curl http://localhost:19000/minio/health/live
   ```

4. Verifica le credenziali nel file `.env`:
   ```bash
   grep MINIO docker-compose.yml
   ```

### ❌ File Parquet Non Appaiono

**Problema**: La sync completa ma non vedi file

**Soluzioni**:
1. Controlla i log di Airbyte:
   ```bash
   docker logs <airbyte-worker-container>
   ```

2. Verifica il path del bucket in Airbyte (deve essere esatto)

3. Controlla i permessi del bucket in MinIO (deve essere accessibile in scrittura)

### ❌ Errore "Access Denied"

**Problema**: MinIO rifiuta le credenziali

**Soluzioni**:
1. Verifica username/password nel file `.env`
2. Ricrea il bucket se necessario
3. Verifica che le credenziali in Airbyte corrispondano esattamente a quelle in MinIO

---

## Configurazione Avanzata

### Usare S3 Data Lake invece di S3

**S3 Data Lake** è ottimizzato per:
- Formati columnar (Parquet, Iceberg)
- Query analytics
- Partizionamento intelligente

**Configurazione aggiuntiva per S3 Data Lake**:
```
Partitioning: Date-based (YYYY/MM/DD)
File Naming: {stream}/{date}/{timestamp}
```

### Collegare MinIO a Metabase

Dopo che i file Parquet sono su MinIO, puoi leggerli con Metabase usando:
- Presto/Trino (vedi `doc/CONNECTION_GUIDE.md`)
- DuckDB
- Script Python ETL

---

## Esempio Completo: Configurazione JSON

Se preferisci configurare via API, ecco un esempio JSON:

```json
{
  "name": "MinIO Parquet Storage",
  "destinationDefinitionId": "<s3-destination-id>",
  "connectionConfiguration": {
    "s3_bucket_name": "parquet-data",
    "s3_bucket_path": "airbyte/",  // ⚠️ NON iniziare con /, MinIO non lo supporta
    "s3_bucket_region": "us-east-1",
    "s3_endpoint": "http://host.docker.internal:19000",
    "access_key_id": "minioadmin",  // o MINIO_ROOT_USER dal .env
    "secret_access_key": "minioadmin_secure_pass_CHANGE_THIS",  // o MINIO_ROOT_PASSWORD dal .env
    "format": {
      "format_type": "Parquet",
      "compression_codec": "SNAPPY",
      "block_size_mb": 128,
      "max_padding_size_mb": 8
    },
    "part_size": 10
  }
}
```

---

## Riferimenti

- [Guida Completa Connessioni](doc/CONNECTION_GUIDE.md)
- [Setup Airbyte](doc/ABCTL_SETUP.md)
- [Guida MinIO](doc/MINIO_GUIDE.md)
- [Airbyte S3 Destination Docs](https://docs.airbyte.com/integrations/destinations/s3)

---

**Ultimo aggiornamento**: 2026-01-17
