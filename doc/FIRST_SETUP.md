# Guida First Setup - Nuovo PC

Questa guida spiega come configurare il progetto DataHub su un nuovo PC dopo aver spostato la cartella del progetto.

---

## Prerequisiti

Prima di iniziare, assicurati di avere installato sul nuovo PC:

1. **Docker** (versione 20.10 o superiore)
   - Verifica: `docker --version`
   - Installazione: https://docs.docker.com/get-docker/

2. **Docker Compose** (versione 2.0 o superiore)
   - Verifica: `docker compose version`
   - Solitamente incluso con Docker Desktop

3. **abctl** (Airbyte CLI) - per gestire Airbyte
   - Verifica: `abctl version`
   - Installazione: `curl -LsfS https://get.airbyte.com | bash -`

---

## Step 1: Verifica Struttura Progetto

Dopo aver spostato la cartella del progetto, verifica che la struttura sia completa:

```bash
cd /path/to/datahub

# Verifica file essenziali
ls -la docker-compose.yml
ls -la .env.example
ls -la scripts/setup.sh
ls -la scripts/start.sh
```

---

## Step 2: Setup Iniziale

Esegui lo script di setup che crea le directory necessarie e il file di configurazione:

```bash
# Rendi eseguibili gli script (se necessario)
chmod +x scripts/*.sh

# Esegui lo script di setup
./scripts/setup.sh
```

Questo script:
- Crea tutte le directory `volumes/` necessarie
- Crea il file `.env` da `.env.example` (se non esiste già)
- Imposta i permessi corretti

---

## Step 3: Configurazione File .env

**⚠️ IMPORTANTE**: Modifica il file `.env` e cambia tutte le password di default!

```bash
# Apri il file .env
nano .env
# oppure
code .env
```

Modifica almeno queste password:
- `POSTGRES_PASSWORD`
- `AIRBYTE_DB_PASSWORD`
- `METABASE_DB_PASSWORD`
- `WRAPPER_DB_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`
- `MINIO_ROOT_PASSWORD`

**Nota**: Se hai già un file `.env` dal PC precedente, puoi riutilizzarlo mantenendo le stesse password (o cambiarle per sicurezza).

---

## Step 4: Creazione Rete Docker

Il progetto richiede una rete Docker esterna chiamata `datahub-network`. Creala se non esiste:

```bash
# Verifica se esiste già
docker network ls | grep datahub-network

# Se non esiste, creala
docker network create datahub-network
```

---

## Step 5: Build e Avvio Servizi

### 5.1 Build Wrapper Application

Il wrapper application deve essere buildato:

```bash
docker compose build wrapper
```

### 5.2 Avvio Servizi Base

Avvia tutti i servizi Docker Compose:

```bash
# Usa lo script di start (consigliato)
./scripts/start.sh

# Oppure direttamente
docker compose up -d
```

**Nota**: Lo script `start.sh` avvia automaticamente anche **Airbyte** se è già installato (dopo il primo setup).

I servizi avviati includono:
- **PostgreSQL** (porta 15432)
- **MySQL** (porta 13306)
- **MinIO** (porte 19000, 19001)
- **Presto/Trino** (porta 18081)
- **Metabase** (porta 13000)
- **Wrapper** (porta 18080)
- **Airbyte** (porta 8000) - se già installato

### 5.3 Verifica Stato Servizi

```bash
# Verifica che tutti i container siano in esecuzione
docker compose ps

# Verifica i log se necessario
docker compose logs -f
```

---

## Step 6: Setup Airbyte (con abctl)

Airbyte è gestito separatamente tramite `abctl`:

```bash
# Verifica che abctl sia installato
abctl version

# Esegui lo script di setup Airbyte
./scripts/setup-airbyte.sh
```

**Nota**: L'installazione di Airbyte può richiedere 10-30 minuti.

Dopo l'installazione:
- Airbyte sarà disponibile su: http://localhost:8000
- Le credenziali verranno mostrate al termine dell'installazione
- **Dalle prossime volte**, lo script `./scripts/start.sh` avvierà automaticamente anche Airbyte

---

## Step 7: Verifica Accesso Servizi

Dopo aver avviato tutti i servizi, verifica l'accesso:

| Servizio | URL | Credenziali |
|----------|-----|-------------|
| **Dashboard Wrapper** | http://localhost:18080 | - |
| **Metabase** | http://localhost:13000 | (primo accesso: setup iniziale) |
| **Airbyte** | http://localhost:8000 | (vedi output `abctl local credentials`) |
| **MinIO Console** | http://localhost:19001 | (vedi `.env`: `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`) |
| **MinIO API** | http://localhost:19000 | (vedi `.env`) |

---

## Step 8: Configurazione Iniziale (Prima Volta)

### 8.1 MinIO - Creazione Bucket

1. Accedi a MinIO Console: http://localhost:19001
2. Crea un bucket chiamato `marketing-data` (o altro nome preferito)
3. Questo bucket sarà usato per salvare i dati Parquet da Airbyte

### 8.2 Metabase - Setup Iniziale

1. Accedi a Metabase: http://localhost:13000
2. Segui la procedura guidata di setup iniziale
3. Configura la connessione al database PostgreSQL se necessario

### 8.3 Airbyte - Configurazione Destination

1. Accedi ad Airbyte: http://localhost:8000
2. Crea una Destination di tipo **S3** configurata per MinIO:
   - Endpoint: `http://host.docker.internal:19000` (o `http://localhost:19000`)
   - Access Key: `minioadmin` (o valore da `.env`)
   - Secret Key: (valore da `.env`: `MINIO_ROOT_PASSWORD`)
   - Bucket: `marketing-data`
   - Format: **Parquet**

Per dettagli completi, vedi: [Guida Connessioni](CONNECTION_GUIDE.md)

---

## Comandi Utili

### Gestione Servizi

```bash
# Avvia tutti i servizi (incluso Airbyte se installato)
./scripts/start.sh
# oppure
docker compose up -d

# Ferma tutti i servizi
./scripts/stop.sh
# oppure
docker compose down

# Riavvia un servizio specifico
docker compose restart metabase

# Visualizza log
docker compose logs -f wrapper
docker compose logs -f metabase
```

### Gestione Airbyte

```bash
# Verifica stato
abctl local status

# Avvia Airbyte (se già installato)
abctl local start

# Ferma Airbyte
abctl local stop

# Mostra credenziali
abctl local credentials

# Disinstalla (se necessario)
abctl local uninstall
```

**Nota**: Dopo la prima installazione, `./scripts/start.sh` avvia automaticamente Airbyte se è installato. Puoi comunque gestirlo manualmente con i comandi sopra.

### Healthcheck

```bash
# Verifica stato di tutti i servizi
./scripts/healthcheck.sh
```

### Backup e Restore

I dati persistenti sono salvati in:
- `volumes/postgres/` - Database PostgreSQL
- `volumes/mysql/` - Database MySQL
- `volumes/minio/` - Dati MinIO (Parquet)
- `volumes/metabase/` - Configurazione Metabase

Per fare backup, copia semplicemente la cartella `volumes/` su un altro PC.

---

## Troubleshooting

### Problema: Porta già in uso

Se una porta è già occupata, modifica `docker-compose.yml` o ferma il servizio che la usa:

```bash
# Trova quale processo usa la porta
lsof -i :18080  # esempio per porta 18080

# Modifica la porta in docker-compose.yml se necessario
```

### Problema: Rete Docker non trovata

```bash
# Crea la rete se mancante
docker network create datahub-network

# Verifica che esista
docker network ls | grep datahub-network
```

### Problema: Container non si avvia

```bash
# Verifica i log per errori
docker compose logs <nome-servizio>

# Verifica che .env sia configurato correttamente
cat .env

# Riavvia i servizi
docker compose down
docker compose up -d
```

### Problema: Airbyte non si connette a MinIO

Se Airbyte è gestito da `abctl` (non in docker-compose), usa:
- Endpoint: `http://host.docker.internal:19000` (non `http://minio:9000`)

---

## Note Importanti

1. **File .env**: Non committare mai il file `.env` nel repository (dovrebbe essere in `.gitignore`)

2. **Volumi Docker**: I dati sono persistenti nella cartella `volumes/`. Se sposti il progetto, copia anche questa cartella.

3. **Airbyte**: Airbyte è gestito separatamente da `abctl` e non è parte di `docker-compose.yml`. Questo è normale e voluto.

4. **Password**: Cambia sempre le password di default nel file `.env` prima di usare il sistema in produzione.

5. **Porte**: Le porte usate sono alternative (15432, 13306, 19000, ecc.) per evitare conflitti con servizi esistenti.

---

## Prossimi Passi

Dopo aver completato il setup:

1. Leggi la [Guida Connessioni](CONNECTION_GUIDE.md) per configurare Airbyte → MinIO → Metabase
2. Consulta la [Documentazione Implementazione](IMPLEMENTATION.md) per dettagli tecnici
3. Configura le connessioni ai tuoi sorgenti dati in Airbyte

---

## Riepilogo Comandi Rapidi

```bash
# Setup completo su nuovo PC
chmod +x scripts/*.sh
./scripts/setup.sh
nano .env  # Modifica password
docker network create datahub-network
docker compose build wrapper
./scripts/start.sh
./scripts/setup-airbyte.sh

# Verifica
docker compose ps
abctl local status
```

---

**Fine guida setup iniziale**
