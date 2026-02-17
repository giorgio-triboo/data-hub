# Guida Completa: Configurare Sync Marketing Data in Airbyte → ClickHouse

Questa guida ti mostra come configurare una sync completa per scaricare tutti i dati di marketing da varie sorgenti in ClickHouse.

---

## Prerequisiti

✅ Airbyte attivo (http://localhost:8000)
✅ Destination ClickHouse configurata e testata
✅ ClickHouse attivo e accessibile

---

## PARTE 1: Creare o Selezionare una Source

### Step 1: Accedi ad Airbyte

1. Apri **http://localhost:8000**
2. Accedi con le tue credenziali

### Step 2: Vai su Sources

1. Nel menu laterale, clicca su **"Sources"**
2. Se hai già una source configurata, puoi usarla
3. Se non ce l'hai, creane una nuova

### Step 3: Crea una nuova Source (se necessario)

1. Clicca **"+ New source"** (in alto a destra)
2. Nella barra di ricerca, cerca la tua source marketing:
   - **Google Analytics** (GA4 o Universal Analytics)
   - **Facebook Marketing** (Facebook Ads)
   - **Google Ads**
   - **LinkedIn Ads**
   - **Twitter Ads**
   - **TikTok Ads**
   - **Snapchat Ads**
   - **Pinterest Ads**
   - Altri...

3. Seleziona il connettore dalla lista
4. Configura le credenziali della source:
   - Segui le istruzioni specifiche per ogni source
   - Potrebbe richiedere OAuth o API keys
   - Testa la connessione prima di salvare

5. Clicca **"Set up source"** (o "Save")

---

## PARTE 2: Creare una Connection (Source → ClickHouse)

### Step 1: Vai su Connections

1. Nel menu laterale, clicca su **"Connections"**
2. Clicca **"+ New connection"** (in alto a destra)

### Step 2: Seleziona Source e Destination

1. **Source**: Seleziona la tua source marketing (es. "Google Analytics", "Facebook Marketing")
2. **Destination**: Seleziona **"ClickHouse Marketing Data"** (quella che hai configurato)
3. Clicca **"Next"** o **"Continue"**

---

## PARTE 3: Configurare Sync Settings

### Step 1: Destination Namespace (Opzionale)

Questo determina come organizzare i dati in ClickHouse:

```
Destination Namespace: 
  - Source default (usa il nome della source)
  - oppure Custom: marketing (per organizzare meglio)
```

**Consiglio**: Usa **"Source default"** per mantenere i dati organizzati per source.

### Step 2: Seleziona Streams

Gli **streams** sono le tabelle/dataset che vuoi sincronizzare.

#### 2.1 Visualizza gli Streams Disponibili

Airbyte mostrerà una lista di tutti gli streams disponibili dalla source. Esempi comuni:

**Per Google Analytics**:
- `analytics_events`
- `analytics_sessions`
- `analytics_users`
- etc.

**Per Facebook Marketing**:
- `ad_accounts`
- `campaigns`
- `ad_sets`
- `ads`
- `insights` (dati di performance)
- etc.

#### 2.2 Seleziona gli Streams

1. **Per scaricare TUTTI i dati**: 
   - Seleziona tutti gli streams disponibili (checkbox in alto)
   - Oppure seleziona manualmente quelli che ti interessano

2. **Per ogni stream**, configura:

   **Sync Mode**:
   - **Full Refresh | Overwrite**: 
     - ✅ Usa per la **prima sync**
     - ✅ Usa per dati che cambiano completamente
     - ⚠️ Sostituisce tutti i dati esistenti
   
   - **Incremental | Append**:
     - ✅ Usa per **sync successive**
     - ✅ Usa per dati che si aggiungono nel tempo
     - ✅ Più efficiente (solo nuovi dati)
     - ⚠️ Richiede un campo "Cursor field"

   **Primary Key** (se disponibile):
   - Campo univoco per identificare i record
   - Es: `id`, `campaign_id`, `ad_id`
   - ✅ Usa sempre se disponibile

   **Cursor Field** (per Incremental):
   - Campo per determinare quali record sono nuovi
   - Es: `date`, `updated_at`, `created_time`
   - ✅ Necessario per sync incrementali

#### 2.3 Configurazione Consigliata per Marketing Data

**Prima Sync (Full Refresh)**:
```
Stream: campaigns
Sync Mode: Full Refresh | Overwrite
Primary Key: id (se disponibile)
Cursor Field: (non necessario per Full Refresh)
```

**Sync Successive (Incremental)**:
```
Stream: campaigns
Sync Mode: Incremental | Append
Primary Key: id
Cursor Field: updated_at (o date, a seconda del stream)
```

### Step 3: Configurazione Avanzata (Opzionale)

Alcune sources hanno opzioni avanzate:

- **Date Range**: Limita il periodo di dati da scaricare
- **Custom Reports**: Per Google Analytics, puoi configurare report personalizzati
- **Filters**: Filtra i dati prima della sync

---

## PARTE 4: Salvare e Avviare la Sync

### Step 1: Salva la Connection

1. Rivedi tutte le impostazioni
2. Clicca **"Set up connection"** (o "Save")
3. La connection verrà creata e apparirà nella lista

### Step 2: Avvia la Prima Sync

1. Dalla pagina della connection, clicca **"Sync now"** (o "Run sync")
2. La sync inizierà immediatamente
3. Puoi vedere lo stato in tempo reale:
   - **Running**: Sync in corso
   - **Success**: Sync completata con successo
   - **Failed**: Sync fallita (controlla i log)

### Step 3: Monitora la Sync

Durante la sync, puoi vedere:
- **Progress**: Percentuale completata
- **Records synced**: Numero di record sincronizzati
- **Status**: Stato corrente
- **Logs**: Log dettagliati per troubleshooting

---

## PARTE 5: Configurare Sync Automatiche (Schedule)

### Step 1: Vai alle Impostazioni della Connection

1. Dalla lista delle connections, clicca sulla tua connection
2. Vai su **"Settings"** o **"Schedule"**

### Step 2: Configura Schedule

```
Schedule Type:
  - Manual: Solo quando clicchi "Sync now"
  - Scheduled: Automatico a intervalli regolari
```

**Per dati marketing, consigliamo**:
- **Daily**: Una volta al giorno (es. alle 2:00 AM)
- **Hourly**: Ogni ora (per dati in tempo reale)
- **Custom**: Intervalli personalizzati

**Esempio configurazione**:
```
Schedule: Daily
Time: 02:00 AM (UTC o tuo timezone)
```

### Step 3: Salva Schedule

1. Configura l'orario desiderato
2. Clicca **"Save"**
3. Le sync partiranno automaticamente secondo lo schedule

---

## PARTE 6: Verificare i Dati in ClickHouse

Dopo la prima sync, verifica che i dati siano arrivati:

### Via ClickHouse Client

```bash
# Entra nel container ClickHouse
docker-compose exec clickhouse clickhouse-client

# Lista database
SHOW DATABASES;

# Seleziona database
USE marketing_data;

# Lista tabelle (dovrebbero corrispondere agli streams)
SHOW TABLES;

# Conta record in una tabella
SELECT COUNT(*) FROM [nome_tabella];

# Visualizza alcuni record
SELECT * FROM [nome_tabella] LIMIT 10;
```

### Via Metabase

1. Vai su **http://localhost:13000**
2. Clicca **"New"** → **"Question"**
3. Seleziona **"ClickHouse Marketing Data"**
4. Dovresti vedere le tabelle corrispondenti agli streams
5. Crea una query per verificare i dati

---

## Esempi di Configurazione per Sources Comuni

### Google Analytics (GA4)

**Streams consigliati**:
- `analytics_events` (eventi)
- `analytics_sessions` (sessioni)
- `analytics_users` (utenti)

**Sync Mode**:
- Prima sync: **Full Refresh | Overwrite**
- Sync successive: **Incremental | Append** (con cursor field `event_date`)

### Facebook Marketing

**Streams consigliati**:
- `ad_accounts` (account pubblicitari)
- `campaigns` (campagne)
- `ad_sets` (set di annunci)
- `ads` (annunci)
- `insights` (metriche di performance) ⭐ **IMPORTANTE**

**Sync Mode**:
- Prima sync: **Full Refresh | Overwrite**
- Sync successive: **Incremental | Append** (con cursor field `date_start` per insights)

### Google Ads

**Streams consigliati**:
- `accounts` (account)
- `campaigns` (campagne)
- `ad_groups` (gruppi di annunci)
- `ads` (annunci)
- `keyword_performance` (performance keyword)

**Sync Mode**:
- Prima sync: **Full Refresh | Overwrite**
- Sync successive: **Incremental | Append** (con cursor field `date`)

---

## Troubleshooting

### Sync Fallita

1. **Controlla i Logs**:
   - Vai alla pagina della connection
   - Clicca su "Logs" o "View logs"
   - Cerca errori specifici

2. **Errori Comuni**:
   - **Rate Limit**: Troppe richieste all'API
     - Soluzione: Aumenta l'intervallo tra le sync
   - **Authentication Failed**: Credenziali scadute
     - Soluzione: Riconfigura la source
   - **Timeout**: Sync troppo lunga
     - Soluzione: Aumenta il timeout o sincronizza meno dati alla volta

### Dati Non Apparsi in ClickHouse

1. **Verifica che la sync sia completata**:
   - Controlla lo stato nella pagina della connection
   - Dovrebbe essere "Success"

2. **Verifica le tabelle in ClickHouse**:
   ```bash
   docker-compose exec clickhouse clickhouse-client --query "SHOW TABLES FROM marketing_data"
   ```

3. **Verifica il namespace**:
   - Se hai usato un namespace custom, le tabelle potrebbero essere in un database diverso

### Performance Lente

1. **Riduci il numero di streams**:
   - Sincronizza solo quelli necessari

2. **Usa Incremental invece di Full Refresh**:
   - Più efficiente per sync successive

3. **Configura date range**:
   - Limita il periodo di dati da scaricare

---

## Best Practices

### 1. Prima Sync

- ✅ Usa **Full Refresh | Overwrite** per tutti gli streams
- ✅ Sincronizza **tutti gli streams** disponibili
- ✅ Lascia completare la prima sync prima di configurare schedule

### 2. Sync Successive

- ✅ Cambia a **Incremental | Append** dopo la prima sync
- ✅ Configura **Cursor Field** appropriato per ogni stream
- ✅ Configura **Schedule** automatico

### 3. Organizzazione

- ✅ Usa **Destination Namespace** per organizzare i dati
- ✅ Mantieni nomi consistenti per le sources
- ✅ Documenta quali streams usi per ogni source

### 4. Monitoraggio

- ✅ Controlla regolarmente lo stato delle sync
- ✅ Monitora i log per errori
- ✅ Verifica che i dati arrivino correttamente in ClickHouse

---

## Riepilogo Checklist

Prima di avviare la sync:

- [ ] Source configurata e testata
- [ ] Destination ClickHouse configurata e testata
- [ ] Connection creata (Source → ClickHouse)
- [ ] Streams selezionati
- [ ] Sync Mode configurato (Full Refresh per prima sync)
- [ ] Primary Key configurato (se disponibile)
- [ ] Connection salvata
- [ ] Prima sync avviata manualmente
- [ ] Dati verificati in ClickHouse
- [ ] Schedule configurato (opzionale)

---

## Prossimi Passi

Dopo aver configurato la sync:

1. ✅ Verifica i dati in ClickHouse
2. ✅ Crea query in Metabase
3. ✅ Crea dashboard in Metabase
4. ✅ Configura alert se le sync falliscono
5. ✅ Monitora regolarmente le performance

---

## Note Importanti

- **Prima sync**: Può richiedere molto tempo a seconda della quantità di dati
- **Incremental sync**: Più veloce ma richiede un cursor field appropriato
- **Storage**: ClickHouse comprime i dati automaticamente, ma monitora lo spazio
- **Backup**: Fai backup regolari dei dati in `volumes/clickhouse/data`
