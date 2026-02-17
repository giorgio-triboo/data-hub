# Guida: Primo Download Storico con Divisione per Giorno

Questa guida spiega come configurare Airbyte per scaricare i dati storici **divisi per giorno** anche nel primo download iniziale.

---

## 🎯 Obiettivo

Configurare il primo sync per:
- ✅ Scaricare dati storici partendo da una data specifica (es. 2024-01-01)
- ✅ Organizzare i dati giorno per giorno (non tutti insieme)
- ✅ Usare sync incrementale anche per il primo download
- ✅ Permettere sync giornaliere successive che scaricano solo i giorni nuovi

---

## 📍 Configurazione Step-by-Step

### Step 1: Configura Start Date nella Source

1. Vai su **http://localhost:8000**
2. Clicca su **"Sources"** nel menu laterale
3. Seleziona la tua source (es. "Facebook Marketing")
4. Clicca **"Edit"** o **"Settings"**

5. Nelle impostazioni della source, cerca **"Start Date"**:
   - **Start Date**: Imposta la data iniziale (es. `2024-01-01T00:00:00Z`)
     - Formato: `YYYY-MM-DDTHH:MM:SSZ`
     - Esempio: `2024-01-01T00:00:00Z` (1 gennaio 2024)
   - **End Date**: Lascia vuoto (scaricherà fino a oggi)

6. Clicca **"Save"** o **"Update"**

**Esempio per Facebook Marketing**:
```
Start Date: 2024-01-01T00:00:00Z
End Date: (vuoto)
```

---

### Step 2: Configura Connection con Incremental Mode

1. Vai su **"Connections"** → Seleziona la tua connection
2. Nella sezione **"Streams"** o **"Sync Catalog"**, per ogni stream:

   **Per stream `ads_insights` (dati di performance giornalieri)**:
   ```
   Sync Mode: Incremental | Append
   Cursor Field: date_start
   Primary Key: id
   ```

   **Per altri stream (es. `campaigns`, `ads`)**:
   ```
   Sync Mode: Incremental | Append
   Cursor Field: updated_time (o date, a seconda del stream)
   Primary Key: id
   ```

3. **⚠️ IMPORTANTE**: Usa `Incremental | Append` anche per il primo sync, NON `Full Refresh | Overwrite`

---

### Step 3: Avvia il Primo Sync

1. Dalla pagina della connection, clicca **"Sync now"**
2. Airbyte inizierà a scaricare i dati:
   - Partirà dalla `start_date` configurata (es. 2024-01-01)
   - Scaricherà giorno per giorno fino a oggi
   - Ogni giorno verrà processato separatamente

3. Monitora il progresso:
   - Vedrai i record scaricati aumentare giorno per giorno
   - I log mostreranno le date processate

---

## 🔍 Come Funziona

### Meccanismo Incrementale con Start Date

1. **Prima Sync**:
   - Airbyte legge la `start_date` dalla configurazione della source
   - Con cursor field `date_start`, parte da quella data
   - Scarica tutti i giorni da `start_date` fino a oggi
   - Salva l'ultimo valore del cursor field (es. `2024-12-31`)

2. **Sync Successive**:
   - Airbyte legge l'ultimo valore del cursor field salvato
   - Scarica solo i giorni successivi a quella data
   - Aggiorna il cursor field con la nuova data più recente

### Esempio Pratico

**Configurazione**:
```
Source Start Date: 2024-01-01T00:00:00Z
Stream: ads_insights
Sync Mode: Incremental | Append
Cursor Field: date_start
```

**Prima Sync (2024-12-31)**:
- Scarica: 2024-01-01, 2024-01-02, ..., 2024-12-31
- Salva cursor: `2024-12-31`

**Seconda Sync (2025-01-01)**:
- Legge cursor: `2024-12-31`
- Scarica solo: 2025-01-01 (giorno nuovo)
- Aggiorna cursor: `2025-01-01`

---

## 📋 Checklist Configurazione

Prima di avviare il primo sync:

- [ ] **Source Start Date** configurata (es. `2024-01-01T00:00:00Z`)
- [ ] **Source End Date** vuota (scarica fino a oggi)
- [ ] **Stream Sync Mode** impostato su `Incremental | Append`
- [ ] **Cursor Field** selezionato (es. `date_start` per insights)
- [ ] **Primary Key** selezionato (se disponibile)
- [ ] **Schedule** configurato su `Daily` (per sync successive)

---

## ⚠️ Note Importanti

### Vantaggi di questo Approccio

✅ **Dati organizzati per giorno**: Ogni giorno viene processato separatamente
✅ **Efficiente**: Non scarica tutto insieme, ma giorno per giorno
✅ **Resumable**: Se la sync si interrompe, può riprendere dall'ultimo giorno
✅ **Incrementale**: Le sync successive sono automaticamente incrementali

### Limitazioni

⚠️ **Prima sync più lunga**: Scaricare molti giorni può richiedere tempo
⚠️ **Rate Limits**: Facebook/altre API potrebbero limitare le richieste
⚠️ **Cursor Field obbligatorio**: Deve essere un campo data valido

### Se la Sync si Interrompe

Se la prima sync si interrompe:
- Airbyte salva lo stato del cursor field
- Puoi riavviare la sync e continuerà dall'ultimo giorno processato
- Non ricomincerà da capo

---

## 🎯 Esempi Specifici per Source

### Facebook Marketing - Stream `ads_insights`

**Source Configuration**:
```
Start Date: 2024-01-01T00:00:00Z
End Date: (vuoto)
```

**Connection Stream Configuration**:
```
Stream: ads_insights
Sync Mode: Incremental | Append
Cursor Field: date_start
Primary Key: id
```

**Risultato**:
- Prima sync: Scarica insights dal 2024-01-01 a oggi, giorno per giorno
- Sync successive: Scarica solo il giorno precedente

### Google Analytics - Stream `analytics_events`

**Source Configuration**:
```
Start Date: 2024-01-01T00:00:00Z
```

**Connection Stream Configuration**:
```
Stream: analytics_events
Sync Mode: Incremental | Append
Cursor Field: event_date
Primary Key: (se disponibile)
```

---

## 🚀 Prossimi Passi

1. ✅ Configura Start Date nella source
2. ✅ Configura stream con Incremental | Append
3. ✅ Avvia prima sync e monitora il progresso
4. ✅ Configura schedule giornaliero per sync automatiche
5. ✅ Verifica i dati in ClickHouse organizzati per giorno

---

## 📚 Riferimenti

- [Airbyte Incremental Sync Documentation](https://docs.airbyte.com/understanding-airbyte/connections/incremental-append)
- [Facebook Marketing Source Configuration](https://docs.airbyte.com/integrations/sources/facebook-marketing)
