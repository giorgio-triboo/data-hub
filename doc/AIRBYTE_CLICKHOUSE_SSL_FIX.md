# Fix SSL: Airbyte → ClickHouse Connection

## Problema

Errore quando Airbyte prova a connettersi a ClickHouse:
```
javax.net.ssl.SSLException: Unsupported or unrecognized SSL message
```

## Causa

Il connettore ClickHouse di Airbyte sta cercando di usare SSL/HTTPS, ma ClickHouse locale non ha SSL abilitato.

## Soluzione

### Step 1: Modifica la Destination in Airbyte

1. Vai su **http://localhost:8000**
2. Vai su **Destinations** → Seleziona la tua destination ClickHouse
3. Clicca **"Edit"** o **"Settings"**

### Step 2: Disabilita SSL

Cerca e modifica questi campi:

**Campi da cercare** (potrebbero avere nomi diversi):
- `SSL` → Imposta a **`false`** o **`No`** o **`disabled`**
- `Secure` → Imposta a **`false`**
- `TLS` → Imposta a **`disabled`**
- `Use SSL` → Imposta a **`false`**
- `Enable SSL` → Imposta a **`false`**
- `SSL Mode` → Imposta a **`disable`** o **`none`**

**Dove trovarli**:
- Potrebbero essere in una sezione "Advanced" o "Security"
- Potrebbero essere in fondo al form
- Potrebbero essere in un menu a tendina

### Step 3: Verifica Configurazione Completa

La configurazione corretta dovrebbe essere:

```
Destination name: ClickHouse Marketing Data

Host: host.docker.internal
Port: 19000
Database: marketing_data
Username: default
Password: [tua password dal .env]

SSL: false          ← IMPORTANTE!
Secure: false       ← IMPORTANTE!
TLS: disabled       ← IMPORTANTE!
```

### Step 4: Test Connection

1. Clicca **"Test connection"**
2. Dovrebbe funzionare ora! ✅

---

## Se Non Vedi l'Opzione SSL

Se non riesci a trovare un campo per disabilitare SSL:

### Opzione 1: Verifica la Versione del Connettore

1. Controlla quale versione del connettore ClickHouse stai usando
2. Potrebbe essere necessario aggiornare o usare una versione diversa

### Opzione 2: Usa la Porta HTTP

Alcuni connettori usano automaticamente HTTPS sulla porta 9000. Prova a:
1. Usare la porta **8123** (HTTP) invece di 9000
2. Cambia Host a `host.docker.internal:8123` (se supportato)

**⚠️ NOTA**: La porta 8123 è la porta HTTP di ClickHouse, ma Airbyte potrebbe richiedere la porta nativa 9000. Verifica nella documentazione del connettore.

### Opzione 3: Configurazione JSON (Avanzato)

Se hai accesso alla configurazione JSON della destination:

```json
{
  "host": "host.docker.internal",
  "port": 19000,
  "database": "marketing_data",
  "username": "default",
  "password": "tua_password",
  "ssl": false,
  "secure": false
}
```

---

## Verifica Rapida

Dopo aver disabilitato SSL:

```bash
# Verifica che ClickHouse risponda su HTTP (non HTTPS)
curl http://localhost:18123/ping
# Dovrebbe rispondere: Ok

# Verifica che la porta 19000 sia aperta
nc -z localhost 19000 && echo "✓ Porta 19000 aperta" || echo "✗ Porta 19000 non raggiungibile"
```

---

## Troubleshooting

### Errore persiste dopo aver disabilitato SSL

1. **Riavvia Airbyte**:
   ```bash
   abctl local restart
   ```

2. **Verifica che le modifiche siano state salvate**:
   - Ricarica la pagina della destination
   - Verifica che SSL sia ancora disabilitato

3. **Prova a ricreare la destination**:
   - Elimina la destination esistente
   - Creane una nuova con SSL disabilitato fin dall'inizio

### Il campo SSL non esiste

Alcune versioni del connettore potrebbero non avere un campo SSL esplicito. In questo caso:

1. Verifica la documentazione del connettore ClickHouse di Airbyte
2. Controlla se c'è un campo "Connection Type" o "Protocol"
3. Assicurati di usare `http://` invece di `https://` nell'URL (se supportato)

---

## Riepilogo

| Campo | Valore Corretto | Valore Sbagliato |
|-------|----------------|------------------|
| **Host** | `host.docker.internal` | `clickhouse` ❌ |
| **Port** | `19000` | `9000` ❌ |
| **SSL** | `false` / `No` | `true` / `Yes` ❌ |
| **Secure** | `false` | `true` ❌ |

---

## Dopo il Fix

Una volta che la connection funziona:
1. ✅ Test connection dovrebbe passare
2. ✅ Puoi creare connections Source → ClickHouse
3. ✅ Le sync dovrebbero funzionare correttamente
