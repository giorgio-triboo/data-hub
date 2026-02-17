# DataHub

Sistema integrato per gestione dati marketing con Airbyte, Metabase e storage Parquet.

## Primo setup

### Docker (servizi base)

```bash
# 1. Setup iniziale (directory, .env da .env.example)
./scripts/setup.sh

# 2. Modifica .env e cambia le password di default
nano .env

# 3. Crea la rete Docker (se non esiste)
docker network create datahub-network

# 4. Build del wrapper e avvio servizi (PostgreSQL, MySQL, MinIO, Metabase, Wrapper)
docker compose build wrapper
docker compose up -d

# 5. Verifica stato
docker compose ps
```

### Airbyte (abctl)

```bash
# 1. Installa abctl (se non presente)
curl -LsfS https://get.airbyte.com | bash -

# 2. Installa e configura Airbyte (10–30 min)
./scripts/setup-airbyte.sh

# 3. Verifica stato
abctl local status
abctl local credentials
```

Dopo il primo setup, `./scripts/start.sh` avvia sia i servizi Docker sia Airbyte (se installato).

---

## Come lanciare Airbyte

Airbyte **non** è nei container Docker del progetto: si installa e si avvia separatamente con **abctl** (CLI ufficiale Airbyte).

| Situazione | Cosa fare |
|------------|-----------|
| **Prima volta** (Airbyte non è mai stato installato) | Esegui **una sola volta** l’installazione: `./scripts/setup-airbyte.sh` (10–30 min). Poi per avviarlo: `abctl local start` oppure `./scripts/start.sh`. |
| **Già installato** | `abctl local start` oppure `./scripts/start.sh` (avvia anche i servizi Docker). |
| **Verifica stato** | `abctl local status` |
| **Credenziali UI** | `abctl local credentials` |
| **Ferma Airbyte** | `abctl local stop` |

**In sintesi:** se vedi *"Airbyte does not appear to be installed locally"*, lancia:

```bash
./scripts/setup-airbyte.sh
```

Al termine avrai Airbyte su http://localhost:8000. Le volte successive userai `./scripts/start.sh` o `abctl local start`.

---

## Ricostruzione / Rebuild

### Docker

```bash
# Ferma e rimuovi i container (mantiene i volumi)
docker compose down

# Ricostruisci il wrapper e riavvia
docker compose build wrapper
docker compose up -d
```

**Ricostruzione completa (cancella anche i dati nei volumi):**

```bash
docker compose down -v
./scripts/setup.sh    # ricrea directory e .env se necessario
docker compose build wrapper
docker compose up -d
```

### Airbyte

**Reinstallazione (abctl):**

```bash
# Disinstalla la versione corrente
abctl local uninstall

# Reinstalla
./scripts/setup-airbyte.sh
```

**Build locale immagini Airbyte** (solo se usi il repo `airbyte-official` e immagini custom):

```bash
./scripts/build-airbyte.sh
# Poi in .env: AIRBYTE_SERVER_IMAGE=airbyte/server:local, ecc.
```

---

## Quick Start (riepilogo)

```bash
./scripts/setup.sh
nano .env
docker network create datahub-network
docker compose build wrapper && docker compose up -d
./scripts/setup-airbyte.sh
docker compose ps && abctl local status
```

## Servizi

- **Dashboard Overview**: http://localhost:18080 (Monitoraggio servizi)
- **Metabase**: http://localhost:13000
- **Airbyte**: http://localhost:8000 (gestito da abctl)
- **MinIO Console**: http://localhost:19001
- **MinIO API**: http://localhost:19000

## Documentazione Completa

- **[First Setup](doc/FIRST_SETUP.md)** - ⭐ Guida per configurare il progetto su un nuovo PC
- **[Soluzione Sviluppo](doc/SOLUZIONE_SVILUPPO.md)** - Architettura e setup completo per sviluppo locale
- **[Setup Airbyte (abctl)](doc/ABCTL_SETUP.md)** - Installazione e configurazione Airbyte con abctl
- **[Guida Deployment](doc/DEPLOYMENT.md)** - Quick start per mettere online
- **[Guida Metabase](doc/METABASE_GUIDE.md)** - Come usare Metabase per visualizzare i dati
- **[Guida Connessioni](doc/CONNECTION_GUIDE.md)** - Airbyte → MinIO → Metabase
- **[Implementazione](doc/IMPLEMENTATION.md)** - Documentazione tecnica dettagliata

## Struttura

```
datahub/
├── docker-compose.yml      # Orchestrazione servizi
├── .env                    # Configurazione (da creare)
├── .env.example           # Template configurazione
├── doc/
│   └── IMPLEMENTATION.md  # Documentazione completa
├── wrapper/               # Wrapper application
├── volumes/               # Dati persistenti
└── scripts/               # Script di utilità
```

## Comandi Utili

```bash
# Avvia servizi (Docker + Airbyte se installato)
./scripts/start.sh

# Ferma servizi
./scripts/stop.sh

# Healthcheck
./scripts/healthcheck.sh

# Log
docker compose logs -f wrapper
```
# data-hub
