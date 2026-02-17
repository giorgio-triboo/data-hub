# Guida Completa: Configurazione ClickHouse con Airbyte e Metabase

Questa guida ti accompagna passo-passo per configurare:
1. **Airbyte → ClickHouse**: Scrittura dati marketing in ClickHouse
2. **ClickHouse → Metabase**: Lettura dati per visualizzazione

---

## Prerequisiti

✅ ClickHouse deve essere avviato e accessibile
✅ Airbyte deve essere avviato (http://localhost:8000)
✅ Metabase deve essere avviato (http://localhost:13000)

Verifica che ClickHouse sia attivo:
```bash
curl http://localhost:18123/ping
# Dovrebbe rispondere: Ok
```

---

## PARTE 1: Configurare Airbyte → ClickHouse

### Step 1: Accedi ad Airbyte

1. Apri il browser e vai su: **http://localhost:8000**
2. Accedi con le tue credenziali (o crea un account se è il primo accesso)

### Step 2: Crea una nuova Destination

1. Nel menu laterale, clicca su **"Destinations"**
2. Clicca sul pulsante **"+ New destination"** (in alto a destra)
3. Nella barra di ricerca, digita: **"ClickHouse"**
4. Seleziona il connettore **"ClickHouse"** dalla lista

### Step 3: Configurazione ClickHouse Destination

Compila i seguenti campi con i valori dal tuo `.env`:

#### 3.1 Informazioni Base

```
Destination name: ClickHouse Marketing Data
```

#### 3.2 Configurazione Connessione

**⚠️ IMPORTANTE - Host e Porta**:
- **Se Airbyte è gestito con `abctl`** (come nel tuo caso): usa `host.docker.internal` come host
- Se Airbyte è nella stessa rete Docker: usa `clickhouse` come host

**Configurazione**:

```
Host: host.docker.internal
  ⚠️ IMPORTANTE: usa host.docker.internal (non clickhouse!)
  (su Linux potrebbe essere necessario usare l'IP dell'host)

Protocol: http
  ⚠️ IMPORTANTE: usa "http" (non "https")!

Port: 18123
  ⚠️ IMPORTANTE: usa 18123 (porta HTTP mappata), NON 19000!
  (19000 è per il protocollo nativo, 18123 è per HTTP)

Database: marketing_data
  (o CLICKHOUSE_DB dal tuo .env)

Username: default
  (o CLICKHOUSE_USER dal tuo .env)

Password: [inserisci CLICKHOUSE_PASSWORD dal .env]
  (es: clickhouse_secure_pass_CHANGE_THIS)
```

**⚠️ NOTA CRITICA**: 
- **Host**: `host.docker.internal` (non `clickhouse`!)
- **Protocol**: `http` (non `https`!)
- **Porta**: `18123` (porta HTTP mappata, non `19000` che è per protocollo nativo!)
- **SSL**: Disabilitato (non usare HTTPS)

#### 3.3 Configurazione Avanzata (Opzionale)

```
Tunnel method: No Tunnel
  (per connessioni locali)

SSL: false
  (per connessioni locali non crittografate)
```

#### 3.4 Test della Connessione

1. Clicca sul pulsante **"Test connection"** (o "Test")
2. Attendi qualche secondo per il test
3. Se vedi un messaggio verde **"Connection successful"** o **"Test passed"**, procedi
4. Se vedi un errore, controlla:
   - Che ClickHouse sia avviato: `docker-compose ps clickhouse`
   - Che le credenziali siano corrette nel `.env`
   - Che la porta sia corretta (9000, non 8123)

#### 3.5 Salva la Destination

1. Se il test è passato, clicca **"Set up destination"** (o "Save")
2. La destination verrà salvata e apparirà nella lista delle destinations

---

### Step 4: Crea una Connection (Source → ClickHouse)

Ora devi collegare una Source (es. Google Analytics, Facebook Ads) alla Destination ClickHouse.

#### 4.1 Crea o Seleziona una Source

1. Vai su **"Sources"** nel menu
2. Se hai già una source, selezionala
3. Se non ce l'hai, creane una nuova:
   - Clicca **"+ New source"**
   - Cerca e seleziona la tua source (es. "Google Analytics", "Facebook Marketing")
   - Configura le credenziali della source
   - Salva

#### 4.2 Crea la Connection

1. Vai su **"Connections"** nel menu
2. Clicca **"+ New connection"**
3. Seleziona:
   - **Source**: La tua source (es. "Google Analytics")
   - **Destination**: "ClickHouse Marketing Data" (quella appena creata)
4. Clicca **"Next"**

#### 4.3 Configura Sync Mode

Per i dati marketing, consigliamo:

```
Sync mode: 
  - Full Refresh | Overwrite (per la prima sync)
  - oppure Incremental | Append (per sync successive)

Destination Namespace: 
  - Source default (usa il nome della source)
  - oppure Custom: marketing (per organizzare meglio)
```

#### 4.4 Seleziona Streams

1. Seleziona gli streams che vuoi sincronizzare (es. "ad_accounts", "campaigns", etc.)
2. Per ogni stream, puoi configurare:
   - **Sync mode**: Full Refresh o Incremental
   - **Primary key**: Campo univoco (se disponibile)
   - **Cursor field**: Campo per sync incrementale (es. "date", "updated_at")

#### 4.5 Salva e Avvia Sync

1. Clicca **"Set up connection"** (o "Save")
2. Dalla pagina della connection, clicca **"Sync now"** per avviare la prima sincronizzazione
3. Attendi che la sync completi (puoi vedere lo stato nella pagina della connection)

---

## PARTE 2: Configurare Metabase → ClickHouse

### Step 1: Accedi a Metabase

1. Apri il browser e vai su: **http://localhost:13000**
2. Accedi con le tue credenziali (o completa il setup iniziale se è la prima volta)

### Step 2: Aggiungi Database ClickHouse

1. Clicca sull'icona **⚙️ Settings** (in alto a destra)
2. Nel menu laterale, clicca su **"Admin settings"**
3. Clicca su **"Databases"** nel menu
4. Clicca sul pulsante **"Add database"** (in alto a destra)

### Step 3: Seleziona ClickHouse

1. Nella lista dei database, cerca **"ClickHouse"**
2. Se non lo vedi, usa la barra di ricerca
3. Clicca su **"ClickHouse"**

### Step 4: Configurazione ClickHouse in Metabase

Compila i seguenti campi:

#### 4.1 Informazioni Base

```
Display name: ClickHouse Marketing Data
```

#### 4.2 Configurazione Connessione

**⚠️ IMPORTANTE - Host e Porta**:
- Se Metabase è nella stessa rete Docker: usa `clickhouse` come host
- Se accedi da browser (host): usa `localhost`

**Configurazione**:

```
Host: clickhouse
  (oppure: localhost se accedi dall'host)

Port: 8123
  (porta HTTP ClickHouse, NON 9000)

Database: marketing_data
  (o CLICKHOUSE_DB dal tuo .env)

Username: default
  (o CLICKHOUSE_USER dal tuo .env)

Password: [inserisci CLICKHOUSE_PASSWORD dal .env]
  (es: clickhouse_secure_pass_CHANGE_THIS)
```

#### 4.3 Configurazione Avanzata (Opzionale)

```
Use a secure connection (SSL): No
  (per connessioni locali)

Additional JDBC connection string options: 
  (lascia vuoto per default)
```

#### 4.4 Test della Connessione

1. Clicca sul pulsante **"Test connection"** (in basso)
2. Attendi qualche secondo per il test
3. Se vedi un messaggio verde **"Successfully connected to the database"**, procedi
4. Se vedi un errore, controlla:
   - Che ClickHouse sia avviato: `docker-compose ps clickhouse`
   - Che le credenziali siano corrette nel `.env`
   - Che la porta sia corretta (8123 per HTTP, non 9000)
   - Che Metabase possa raggiungere ClickHouse (stessa rete Docker)

#### 4.5 Salva il Database

1. Se il test è passato, clicca **"Save"** (in basso)
2. Il database verrà salvato e apparirà nella lista dei database

---

### Step 5: Esplora i Dati in Metabase

Ora puoi creare query e dashboard con i dati da ClickHouse!

#### 5.1 Crea una Query

1. Clicca su **"New"** → **"Question"** (o "Ask a question")
2. Seleziona **"ClickHouse Marketing Data"** come database
3. Seleziona una tabella (es. "ad_accounts", "campaigns")
4. Costruisci la tua query usando l'interfaccia visuale o SQL

#### 5.2 Esempio Query SQL

```sql
SELECT 
    date,
    campaign_name,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    SUM(spend) as total_spend
FROM campaigns
WHERE date >= today() - 30
GROUP BY date, campaign_name
ORDER BY date DESC
```

#### 5.3 Crea Dashboard

1. Clicca su **"New"** → **"Dashboard"**
2. Aggiungi le tue query come cards
3. Personalizza layout e filtri

---

## Troubleshooting

### Problema: Airbyte non riesce a connettersi a ClickHouse

**Sintomi**: Errore "Connection refused", "Host unreachable" o "UnknownHostException: clickhouse"

**Soluzioni**:
1. Verifica che ClickHouse sia avviato:
   ```bash
   docker-compose ps clickhouse
   ```

2. Verifica che ClickHouse sia raggiungibile:
   ```bash
   curl http://localhost:18123/ping
   ```

3. **Se Airbyte è gestito con `abctl`** (come nel tuo caso):
   - ✅ Usa **`host.docker.internal`** come host (NON `clickhouse`)
   - ✅ Usa porta **`19000`** (porta mappata, NON `9000`)
   - ❌ NON usare `clickhouse:9000` - non funzionerà!

4. Verifica che la porta 19000 sia raggiungibile dall'host:
   ```bash
   nc -z localhost 19000 && echo "Porta 19000 aperta" || echo "Porta 19000 non raggiungibile"
   ```

5. **Su Linux**: Se `host.docker.internal` non funziona, usa l'IP dell'host:
   ```bash
   # Trova l'IP dell'host
   ip addr show docker0 | grep inet | awk '{print $2}' | cut -d/ -f1
   # Usa questo IP invece di host.docker.internal
   ```

6. Verifica che SSL sia disabilitato (non usare HTTPS)

### Problema: Metabase non riesce a connettersi a ClickHouse

**Sintomi**: Errore "Connection refused" o "Host unreachable"

**Soluzioni**:
1. Verifica che ClickHouse sia avviato:
   ```bash
   docker-compose ps clickhouse
   ```
2. Verifica che Metabase sia nella stessa rete Docker:
   ```bash
   docker network inspect datahub-network | grep -E "clickhouse|metabase"
   ```
3. Se accedi da browser (host), usa `localhost` invece di `clickhouse`
4. Verifica che la porta sia corretta: **8123** (non 9000) per Metabase

### Problema: Password non funziona

**Sintomi**: Errore "Authentication failed" o "Invalid credentials"

**Soluzioni**:
1. Verifica il valore di `CLICKHOUSE_PASSWORD` nel file `.env`
2. Se hai cambiato la password, riavvia ClickHouse:
   ```bash
   docker-compose restart clickhouse
   ```
3. Verifica che non ci siano spazi o caratteri speciali nella password

### Problema: Database non trovato

**Sintomi**: Errore "Database does not exist"

**Soluzioni**:
1. Crea il database in ClickHouse:
   ```bash
   docker-compose exec clickhouse clickhouse-client --query "CREATE DATABASE IF NOT EXISTS marketing_data"
   ```
2. Verifica che il nome del database corrisponda a `CLICKHOUSE_DB` nel `.env`

### Problema: Tabelle non visibili in Metabase

**Sintomi**: Database connesso ma nessuna tabella visibile

**Soluzioni**:
1. Verifica che i dati siano stati sincronizzati da Airbyte
2. Controlla le tabelle in ClickHouse:
   ```bash
   docker-compose exec clickhouse clickhouse-client --query "SHOW TABLES FROM marketing_data"
   ```
3. Se le tabelle esistono ma non sono visibili, prova a ricaricare lo schema in Metabase:
   - Vai su Settings → Databases → ClickHouse Marketing Data
   - Clicca "Sync database schema now"

---

## Verifica Finale

### Verifica Dati in ClickHouse

```bash
# Entra nel container ClickHouse
docker-compose exec clickhouse clickhouse-client

# Lista database
SHOW DATABASES;

# Seleziona database
USE marketing_data;

# Lista tabelle
SHOW TABLES;

# Conta record in una tabella
SELECT COUNT(*) FROM [nome_tabella];

# Esempio query
SELECT * FROM [nome_tabella] LIMIT 10;
```

### Verifica Connection in Airbyte

1. Vai su **Connections** in Airbyte
2. Controlla lo stato della connection
3. Verifica che l'ultima sync sia completata con successo

### Verifica Database in Metabase

1. Vai su **Settings** → **Databases** in Metabase
2. Verifica che "ClickHouse Marketing Data" sia connesso
3. Crea una query di test per verificare i dati

---

## Prossimi Passi

1. ✅ Configura altre sources in Airbyte
2. ✅ Crea dashboard personalizzate in Metabase
3. ✅ Configura sync schedule in Airbyte (automatiche)
4. ✅ Ottimizza le query ClickHouse per performance migliori

---

## Note Importanti

- **Porte ClickHouse**:
  - `8123`: HTTP interface (usata da Metabase)
  - `9000`: Native protocol (usata da Airbyte)
  - `9004`: Inter-server communication

- **Compressione**: ClickHouse usa compressione LZ4 di default, simile a Parquet

- **Performance**: ClickHouse è ottimizzato per query analitiche su grandi volumi di dati

- **Backup**: I dati sono salvati in `volumes/clickhouse/data` - fai backup regolari!
