# Guida: Configurare Sync Incrementale Giornaliera in Airbyte

Questa guida spiega come configurare Airbyte per scaricare dati con frequenza giornaliera (incrementale) invece di fare un full refresh lifetime.

---

## 🎯 Obiettivo

Configurare la sync per:
- ✅ Scaricare solo i dati nuovi/aggiornati ogni giorno
- ✅ Non rifare il download di tutti i dati storici
- ✅ Eseguire automaticamente ogni giorno (es. alle 2:00 AM)

---

## 📍 Dove Configurare: Interfaccia Airbyte

### Step 1: Accedi alla Connection

1. Vai su **http://localhost:8000**
2. Clicca su **"Connections"** nel menu laterale
3. Clicca sulla connection che vuoi modificare (es. "Facebook Marketing → ClickHouse")

### Step 2: Configura Sync Mode Incrementale per ogni Stream

1. Nella pagina della connection, cerca la sezione **"Streams"** o **"Sync Catalog"**
2. Per ogni stream che vuoi sincronizzare giornalmente:

   **Per ogni stream (es. `ads_insights`, `campaigns`)**:
   
   a. **Sync Mode**: Cambia da `Full Refresh | Overwrite` a **`Incremental | Append`**
   
   b. **Cursor Field**: Seleziona il campo data che indica quando il record è stato creato/aggiornato
      - Per Facebook Marketing `ads_insights`: usa **`date_start`** o **`date`**
      - Per altri stream: usa **`updated_at`**, **`created_time`**, o **`date`**
      - ⚠️ Il cursor field deve essere un campo data/timestamp
   
   c. **Primary Key**: Se disponibile, seleziona un campo univoco (es. `id`, `ad_id`)

   **Esempio configurazione per `ads_insights`**:
   ```
   Stream: ads_insights
   Sync Mode: Incremental | Append
   Cursor Field: date_start
   Primary Key: id (se disponibile)
   ```

### Step 3: Configura Schedule Giornaliero

1. Nella pagina della connection, vai alla sezione **"Schedule"** o **"Sync frequency"**
2. Seleziona:
   - **Schedule Type**: `Scheduled` (non "Manual")
   - **Frequency**: `Daily` (o "Every day")
   - **Time**: Scegli l'orario (es. `02:00 AM`)
   - **Timezone**: Seleziona il tuo timezone (es. `Europe/Rome`)

   **Esempio**:
   ```
   Schedule: Daily
   Time: 02:00 AM
   Timezone: Europe/Rome
   ```

3. Clicca **"Save changes"** o **"Update"**

---

## 🔧 Configurazione Avanzata: Limitare Range Date nella Source

Alcune sources (come Facebook Marketing) permettono di limitare il range di date da scaricare.

### Per Facebook Marketing:

1. Vai su **"Sources"** → Seleziona la tua source Facebook Marketing
2. Clicca **"Edit"** o **"Settings"**
3. Cerca la sezione **"Date Range"** o **"Data Range"**
4. Configura:
   - **Start Date**: Imposta la data iniziale da cui vuoi scaricare i dati storici (es. `2024-01-01T00:00:00Z`)
   - **End Date**: Lascia vuoto per scaricare fino a oggi
   - ⚠️ Con sync incrementale, Airbyte scaricherà automaticamente solo i dati nuovi dopo l'ultima sync

### ⭐ IMPORTANTE: Primo Download con Divisione per Giorno

Per scaricare i dati storici **divisi per giorno** anche nel primo download:

1. **Configura la Source con Start Date**:
   - Vai su **"Sources"** → Seleziona la tua source
   - Imposta **Start Date**: Data da cui iniziare (es. `2024-01-01T00:00:00Z`)
   - Salva le modifiche

2. **Usa Incremental | Append anche per il primo sync**:
   - Nella connection, configura ogni stream con:
     - **Sync Mode**: `Incremental | Append` (NON Full Refresh!)
     - **Cursor Field**: `date_start` (per insights) o `date` (per altri stream)
     - **Primary Key**: `id` (se disponibile)

3. **Come funziona**:
   - Airbyte parte dalla `start_date` configurata nella source
   - Con il cursor field `date_start`, scaricherà i dati **giorno per giorno**
   - La prima sync scaricherà tutti i giorni da `start_date` fino a oggi
   - Le sync successive scaricheranno solo i giorni nuovi

**Esempio configurazione per primo download storico**:
```
Source Settings:
  Start Date: 2024-01-01T00:00:00Z
  End Date: (vuoto)

Connection Stream (ads_insights):
  Sync Mode: Incremental | Append
  Cursor Field: date_start
  Primary Key: id
```

**Risultato**:
- Prima sync: Scarica dati dal 2024-01-01 fino a oggi, giorno per giorno
- Sync successive: Scarica solo i giorni nuovi (es. ieri se fai sync giornaliera)

### Per Google Analytics:

1. Nelle impostazioni della source, cerca **"Date Range"**
2. Configura il range iniziale (solo per la prima sync)
3. Le sync successive useranno automaticamente il cursor field

---

## 📋 Checklist Configurazione

Per ogni stream che vuoi sincronizzare giornalmente:

- [ ] **Sync Mode** impostato su `Incremental | Append`
- [ ] **Cursor Field** selezionato (campo data, es. `date_start`, `updated_at`)
- [ ] **Primary Key** selezionato (se disponibile)
- [ ] **Schedule** configurato su `Daily` con orario preferito
- [ ] **Timezone** corretto

---

## 🎯 Esempi Specifici per Source Comuni

### Facebook Marketing

**Stream `ads_insights`** (dati di performance giornalieri):
```
Sync Mode: Incremental | Append
Cursor Field: date_start
Primary Key: id
Schedule: Daily at 02:00 AM
```

**Stream `campaigns`** (metadati campagne):
```
Sync Mode: Incremental | Append
Cursor Field: updated_time
Primary Key: id
Schedule: Daily at 02:00 AM
```

### Google Analytics

**Stream `analytics_events`**:
```
Sync Mode: Incremental | Append
Cursor Field: event_date
Primary Key: (se disponibile)
Schedule: Daily at 02:00 AM
```

### Google Ads

**Stream `campaign_performance`**:
```
Sync Mode: Incremental | Append
Cursor Field: date
Primary Key: (se disponibile)
Schedule: Daily at 02:00 AM
```

---

## ⚠️ Note Importanti

### Prima Sync vs Sync Successive

1. **Prima Sync**: 
   - Puoi fare un `Full Refresh | Overwrite` per scaricare tutti i dati storici
   - Oppure iniziare direttamente con `Incremental | Append` (scaricherà solo dati recenti)

2. **Sync Successive**:
   - Con `Incremental | Append`, Airbyte ricorda l'ultimo valore del cursor field
   - Scaricherà solo i record con cursor field maggiore dell'ultimo valore sincronizzato

### Cursor Field

- ⚠️ Il cursor field deve essere un campo **data** o **timestamp**
- ⚠️ Deve essere **crescente** nel tempo (non può essere casuale)
- ✅ Esempi validi: `date`, `date_start`, `updated_at`, `created_time`
- ❌ Esempi non validi: `id`, `name`, `status`

### Primary Key

- ✅ Usa sempre se disponibile (evita duplicati)
- ✅ Migliora le performance
- ⚠️ Se non disponibile, Airbyte userà tutti i campi come chiave (meno efficiente)

---

## 🔍 Verifica Configurazione

Dopo aver configurato:

1. **Verifica Sync Mode**:
   - Vai alla connection → Streams
   - Controlla che ogni stream abbia `Incremental | Append`

2. **Verifica Schedule**:
   - Vai alla connection → Settings
   - Controlla che sia configurato `Daily` con orario

3. **Test Manuale**:
   - Clicca **"Sync now"** per testare
   - Verifica nei log che usi il cursor field
   - Controlla che scarichi solo dati nuovi

---

## 🚀 Prossimi Passi

1. ✅ Configura tutti gli streams con sync incrementale
2. ✅ Imposta schedule giornaliero
3. ✅ Esegui una sync di test manuale
4. ✅ Verifica che i dati arrivino correttamente in ClickHouse
5. ✅ Monitora le sync automatiche giornaliere

---

## 📚 Riferimenti

- [Airbyte Sync Modes Documentation](https://docs.airbyte.com/understanding-airbyte/connections/)
- [Incremental Sync Guide](https://docs.airbyte.com/understanding-airbyte/connections/incremental-append)
