# Fix Protocol: Airbyte → ClickHouse Connection (HTTP 400)

## Problema

Errore quando Airbyte prova a connettersi a ClickHouse:
```
ServerException: Code: 0. DB::Exception: <Unreadable error message> (transport error: 400)
```

## Causa

Il connettore ClickHouse di Airbyte usa **HTTP/HTTPS** (non il protocollo nativo sulla porta 9000).

Il problema è che:
1. Il campo **"Protocol"** è impostato su `https` (default)
2. La porta potrebbe essere sbagliata (19000 è per il protocollo nativo, non HTTP)

## Soluzione

### Step 1: Modifica la Destination in Airbyte

1. Vai su **http://localhost:8000**
2. Vai su **Destinations** → Seleziona la tua destination ClickHouse
3. Clicca **"Edit"** o **"Settings"**

### Step 2: Cambia Protocol e Porta

**Cerca e modifica questi campi**:

```
Protocol: http
  ⚠️ IMPORTANTE: cambia da "https" a "http"
  (non usare HTTPS per ClickHouse locale)

Port: 18123
  ⚠️ IMPORTANTE: usa 18123 (porta HTTP mappata), NON 19000!
  (19000 è per il protocollo nativo, 18123 è per HTTP)
```

### Step 3: Verifica Configurazione Completa

La configurazione corretta dovrebbe essere:

```
Destination name: ClickHouse Marketing Data

Host: host.docker.internal
Protocol: http          ← IMPORTANTE! (non https)
Port: 18123            ← IMPORTANTE! (non 19000)
Database: marketing_data
Username: default
Password: [tua password dal .env]

SSL: false (se presente)
```

### Step 4: Test Connection

1. Clicca **"Test connection"**
2. Dovrebbe funzionare ora! ✅

---

## Spiegazione delle Porte

| Porta | Protocollo | Uso |
|-------|------------|-----|
| **18123** | HTTP | ✅ Usa questa per Airbyte (porta mappata) |
| **8123** | HTTP | Porta interna (non accessibile da host) |
| **19000** | Native | ❌ NON usare per Airbyte (protocollo nativo) |
| **9000** | Native | Porta interna (non accessibile da host) |

**Perché 18123?**
- ClickHouse espone HTTP sulla porta 8123 internamente
- Docker Compose mappa `18123:8123` (porta esterna:porta interna)
- Quindi dall'host devi usare `18123` per accedere all'HTTP di ClickHouse

---

## Se Non Vedi il Campo "Protocol"

Se non vedi un campo "Protocol" esplicito:

1. **Verifica la versione del connettore**: Potrebbe essere una versione diversa
2. **Cerca in "Advanced"**: Il campo potrebbe essere in una sezione avanzata
3. **Usa la porta HTTP**: Se non c'è il campo Protocol, assicurati almeno di usare la porta `18123`

---

## Troubleshooting

### Errore 400 persiste

1. **Verifica che Protocol sia "http"**:
   - Non "https"
   - Non lasciare il default

2. **Verifica la porta**:
   ```bash
   # Testa la porta HTTP
   curl http://localhost:18123/ping
   # Dovrebbe rispondere: Ok
   ```

3. **Verifica le credenziali**:
   - Username: `default`
   - Password: quella dal tuo `.env`

### Errore "Authentication failed"

Se vedi un errore di autenticazione:

1. Verifica la password nel file `.env`
2. Riavvia ClickHouse se hai cambiato la password:
   ```bash
   docker-compose restart clickhouse
   ```

---

## Riepilogo Valori Corretti

| Campo | Valore Corretto | Valore Sbagliato |
|-------|----------------|------------------|
| **Host** | `host.docker.internal` | `clickhouse` ❌ |
| **Protocol** | `http` | `https` ❌ |
| **Port** | `18123` | `19000` ❌ / `9000` ❌ |
| **Database** | `marketing_data` | `default` (opzionale) |
| **Username** | `default` | - |
| **Password** | Dal `.env` | - |
| **SSL** | `false` | `true` ❌ |

---

## Dopo il Fix

Una volta che la connection funziona:
1. ✅ Test connection dovrebbe passare
2. ✅ Puoi creare connections Source → ClickHouse
3. ✅ Le sync dovrebbero funzionare correttamente

---

## Nota Importante

**Metabase usa una configurazione diversa**:
- Metabase è nella stessa rete Docker, quindi può usare `clickhouse:8123`
- Airbyte è gestito con `abctl`, quindi deve usare `host.docker.internal:18123`

Non confondere le due configurazioni!
