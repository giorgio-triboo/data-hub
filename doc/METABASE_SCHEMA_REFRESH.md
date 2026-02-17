# Come Aggiornare lo Schema in Metabase

Metabase mantiene una cache dello schema del database. Quando elimini tabelle in ClickHouse, devi aggiornare lo schema in Metabase per vedere le modifiche.

## Metodo 1: Da Interfaccia Web (Consigliato) ✅

1. **Accedi a Metabase**: http://localhost:13000
2. **Vai su Settings**:
   - Clicca sull'icona ⚙️ **Settings** (in alto a destra)
   - Oppure vai direttamente su: http://localhost:13000/admin/databases
3. **Trova il Database ClickHouse**:
   - Cerca "ClickHouse Marketing Data" nella lista
   - Clicca sul database
4. **Aggiorna lo Schema**:
   - Scorri fino alla sezione "Sync database schema"
   - Clicca sul pulsante **"Sync database schema now"** (o "Sync now")
   - Attendi qualche secondo per il completamento
5. **Verifica**:
   - Torna alla pagina "Browse Data"
   - Le tabelle eliminate non dovrebbero più essere visibili

## Metodo 2: Via API (Avanzato)

Se preferisci automatizzare, puoi usare l'API di Metabase:

```bash
# Prima ottieni il database ID
curl -X GET "http://localhost:13000/api/database" \
  -H "X-Metabase-Session: YOUR_SESSION_TOKEN"

# Poi triggera il sync
curl -X POST "http://localhost:13000/api/database/DATABASE_ID/sync_schema" \
  -H "X-Metabase-Session: YOUR_SESSION_TOKEN"
```

## Metodo 3: Auto-sync Periodico

Puoi configurare Metabase per aggiornare automaticamente lo schema:

1. Vai su **Settings** → **Databases** → **ClickHouse Marketing Data**
2. Nella sezione **"Sync database schema"**
3. Imposta **"Scan for new tables"** su un intervallo (es. ogni ora)
4. Salva le modifiche

---

## Troubleshooting

### Le tabelle appaiono ancora dopo il sync

1. **Forza un refresh completo**:
   - Vai su Settings → Databases → ClickHouse Marketing Data
   - Clicca su **"Re-scan field values now"** (se disponibile)
   - Poi clicca su **"Sync database schema now"**

2. **Verifica che le tabelle siano realmente eliminate**:
   ```bash
   docker exec datahub-clickhouse clickhouse-client --password="clickhouse_secure_pass_CHANGE_THIS" --query "SHOW TABLES FROM marketing_data"
   ```

3. **Se necessario, disconnetti e riconnetti il database**:
   - Settings → Databases → ClickHouse Marketing Data
   - Clicca "Remove" (rimuove solo la connessione, non i dati)
   - Ricrea la connessione

---

## Note Importanti

- ⚠️ Metabase mantiene una cache dello schema per performance
- 🔄 Il sync può richiedere alcuni secondi
- 📊 Le query esistenti potrebbero fallire se riferiscono a tabelle eliminate
- 🔍 Dopo il sync, le tabelle eliminate non saranno più visibili
