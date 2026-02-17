# Fix Rapido: Airbyte → ClickHouse Connection

## Problema

Errore quando Airbyte prova a connettersi a ClickHouse:
```
javax.net.ssl.SSLException: Unsupported or unrecognized SSL message
```

Questo significa che Airbyte sta cercando di usare SSL/HTTPS, ma ClickHouse locale non ha SSL abilitato.

## Causa

Due problemi possibili:

1. **SSL abilitato**: Airbyte sta cercando di connettersi con SSL/HTTPS, ma ClickHouse locale non ha SSL abilitato
2. **Hostname errato**: Se usi `clickhouse` come host, Airbyte (gestito con `abctl`) non può risolvere l'hostname perché non è nella stessa rete Docker

## Soluzione

### Step 1: Modifica la Destination in Airbyte

1. Vai su **http://localhost:8000**
2. Vai su **Destinations** → Seleziona la tua destination ClickHouse
3. Clicca **"Edit"** o **"Settings"**

### Step 2: Cambia Host e Porta

**Cambia questi valori**:

```
❌ PRIMA (NON FUNZIONA):
Host: clickhouse
Port: 9000

✅ DOPO (FUNZIONA):
Host: host.docker.internal
Port: 19000
```

**Spiegazione**:
- `host.docker.internal` è un hostname speciale che punta all'host Docker (il tuo Mac)
- `19000` è la porta mappata da docker-compose (non `9000` che è la porta interna)

### Step 3: Verifica SSL (CRITICO!)

**⚠️ QUESTO È IL PROBLEMA PRINCIPALE!**

Assicurati che **SSL sia disabilitato**:
- ✅ SSL: **No** o **false** o **disabled**
- ✅ Secure: **false**
- ✅ TLS: **disabled**
- ❌ NON usare HTTPS
- ❌ NON usare SSL

**Dove trovare l'opzione SSL**:
- Cerca un campo chiamato "SSL", "Secure", "TLS", "Use SSL", "Enable SSL"
- Potrebbe essere in una sezione "Advanced" o "Security"
- Se non vedi l'opzione, potrebbe essere abilitata di default - cerca nelle impostazioni avanzate

**Se non trovi l'opzione SSL**:
Il connettore potrebbe usare HTTPS di default. In questo caso, potresti dover:
1. Verificare che stai usando la porta corretta (19000, non 8443)
2. Assicurarti che l'URL non inizi con `https://`
3. Controllare se c'è un campo "Protocol" o "Connection Type" e impostarlo su "HTTP" o "Native"

### Step 4: Test Connection

1. Clicca **"Test connection"**
2. Dovrebbe funzionare ora! ✅

---

## Configurazione Completa Corretta

```
Destination name: ClickHouse Marketing Data

Host: host.docker.internal
Port: 19000
Database: marketing_data
Username: default
Password: [tua password dal .env]

SSL: No
Tunnel method: No Tunnel
```

---

## Verifica Rapida

Dopo aver salvato, verifica che funzioni:

```bash
# Verifica che ClickHouse sia raggiungibile sulla porta mappata
curl http://localhost:18123/ping
# Dovrebbe rispondere: Ok

# Verifica che la porta 19000 sia aperta
nc -z localhost 19000 && echo "✓ Porta 19000 aperta" || echo "✗ Porta 19000 non raggiungibile"
```

---

## Se Ancora Non Funziona

### Su Linux

Se `host.docker.internal` non funziona su Linux:

1. Trova l'IP dell'host Docker:
   ```bash
   ip addr show docker0 | grep inet | awk '{print $2}' | cut -d/ -f1
   ```

2. Usa questo IP invece di `host.docker.internal`

### Verifica Network

Verifica che ClickHouse sia nella rete corretta:
```bash
docker network inspect datahub-network | grep clickhouse
```

### Verifica Porte

Verifica che le porte siano mappate correttamente:
```bash
docker-compose ps clickhouse
# Dovresti vedere: 0.0.0.0:19000->9000/tcp
```

---

## Riepilogo Valori Corretti

| Campo | Valore Corretto | Valore Sbagliato |
|-------|----------------|------------------|
| **Host** | `host.docker.internal` | `clickhouse` ❌ |
| **Port** | `19000` | `9000` ❌ |
| **SSL** | `No` / `false` | `Yes` ❌ |

---

## Dopo il Fix

Una volta che la connection funziona:
1. ✅ Test connection dovrebbe passare
2. ✅ Puoi creare connections Source → ClickHouse
3. ✅ Le sync dovrebbero funzionare correttamente
