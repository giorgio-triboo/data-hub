# DataHub Wrapper

Wrapper moderno per gestione e monitoraggio del sistema DataHub.

## Funzionalità

- ✅ **Autenticazione Google OAuth** - Login tramite Google
- ✅ **Sistema Ruoli** - Admin, Developer, Viewer con permessi granulari
- ✅ **Healthcheck Servizi** - Monitoraggio in tempo reale di PostgreSQL, MySQL, ClickHouse, Metabase, Airbyte
- ✅ **Gestione Database ClickHouse** - Crea, elimina, visualizza database ClickHouse
- ✅ **Gestione Connessioni Airbyte** - Monitora e triggera sync manuali
- ✅ **Audit Log** - Tracciamento di tutte le azioni utente

## Configurazione

### Variabili d'Ambiente

Aggiungi al file `.env` nella root del progetto:

```bash
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8080/auth/google/callback
ALLOWED_GOOGLE_DOMAINS=example.com,another.com  # Opzionale, lascia vuoto per permettere qualsiasi dominio

# Database PostgreSQL (per utenti, ruoli, audit)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
WRAPPER_DB_NAME=wrapper_db

# ClickHouse
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your_clickhouse_password

# Airbyte
AIRBYTE_WEBAPP_URL=http://localhost:8000
AIRBYTE_API_URL=http://localhost:8000/api/v1

# Wrapper
WRAPPER_PORT=8080
CHECK_INTERVAL=60
LOG_LEVEL=INFO
WRAPPER_SECRET_KEY=your_secret_key_here  # Genera una chiave casuale
```

### Setup Google OAuth

1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto o seleziona uno esistente
3. Abilita **Google+ API**
4. Vai a **Credenziali** → **Crea credenziali** → **ID client OAuth 2.0**
5. Configura:
   - **Tipo applicazione**: Applicazione web
   - **URI di reindirizzamento autorizzati**: `http://localhost:8080/auth/google/callback`
6. Copia **ID client** e **Segreto client** nel `.env`

## Struttura

```
wrapper/
├── app.py                 # Main Flask application
├── config.py             # Configurazione
├── db.py                  # SQLAlchemy setup
├── models/                # Database models
│   ├── user.py           # User model
│   ├── role.py           # Role model
│   └── audit_log.py      # Audit log model
├── services/              # Business logic
│   ├── auth_service.py   # Authentication service
│   ├── clickhouse_service.py
│   └── airbyte_service.py
├── routes/                # Flask routes
│   ├── auth.py           # Authentication routes
│   ├── dashboard.py      # Dashboard routes
│   ├── healthcheck.py    # Healthcheck API
│   ├── clickhouse.py     # ClickHouse API
│   ├── airbyte.py        # Airbyte API
│   └── api.py            # General API
├── templates/             # Jinja2 templates
│   ├── base.html
│   ├── dashboard.html
│   ├── healthcheck.html
│   ├── clickhouse.html
│   └── airbyte.html
├── service_monitor.py     # Service monitoring (legacy, mantenuto)
├── airbyte_checker.py     # Airbyte checker (legacy, mantenuto)
├── sse_manager.py         # SSE manager (legacy, mantenuto)
└── requirements.txt       # Python dependencies
```

## Ruoli e Permessi

### Admin
- Accesso completo a tutte le funzionalità
- Gestione utenti e ruoli
- View audit log

### Developer
- View e manage ClickHouse
- View e manage Airbyte
- View healthcheck
- View audit log
- Restart servizi

### Viewer
- View healthcheck
- View ClickHouse (solo lettura)
- View Airbyte (solo lettura)

## Avvio

```bash
# Build Docker image
docker build -t datahub-wrapper ./wrapper

# Run container
docker run -d \
  --name datahub-wrapper \
  --network datahub-network \
  -p 8080:8080 \
  --env-file .env \
  datahub-wrapper
```

Oppure via docker-compose (aggiungi al `docker-compose.yml`):

```yaml
wrapper:
  build: ./wrapper
  container_name: datahub-wrapper
  ports:
    - "8080:8080"
  env_file:
    - .env
  depends_on:
    - postgres
  networks:
    - datahub-network
```

## Accesso

Dopo l'avvio, accedi a: `http://localhost:8080`

La prima volta verrai reindirizzato al login Google. Dopo il login, verrai creato automaticamente come utente con ruolo **viewer**.

Per promuovere un utente ad admin, esegui:

```sql
UPDATE users SET role_id = (SELECT id FROM roles WHERE name = 'admin') WHERE email = 'your-email@example.com';
```

## API Endpoints

### Healthcheck
- `GET /api/healthcheck/status` - Stato servizi
- `POST /api/healthcheck/run` - Esegui healthcheck manuale

### ClickHouse
- `GET /api/clickhouse/databases` - Lista database
- `POST /api/clickhouse/databases` - Crea database
- `DELETE /api/clickhouse/databases/<name>` - Elimina database
- `GET /api/clickhouse/databases/<name>/info` - Info database
- `GET /api/clickhouse/databases/<name>/tables/<table>/preview` - Preview tabella

### Airbyte
- `GET /api/airbyte/status` - Stato connessione
- `GET /api/airbyte/connections` - Lista connessioni
- `GET /api/airbyte/connections/<id>` - Dettagli connessione
- `POST /api/airbyte/connections/<id>/sync` - Trigger sync
- `GET /api/airbyte/sources` - Lista sources
- `GET /api/airbyte/destinations` - Lista destinations

### Auth
- `GET /api/user` - Utente corrente

### Audit Log
- `GET /api/audit-log` - Lista log (solo admin)

## Troubleshooting

### Errore: "Google OAuth non configurato"
Verifica che `GOOGLE_OAUTH_CLIENT_ID` e `GOOGLE_OAUTH_CLIENT_SECRET` siano impostati nel `.env`.

### Errore: "Database non inizializzato"
Il database viene inizializzato automaticamente al primo avvio. Verifica che PostgreSQL sia raggiungibile e le credenziali siano corrette.

### Errore: "ClickHouse non raggiungibile"
Verifica che ClickHouse sia avviato e che `CLICKHOUSE_HOST` e `CLICKHOUSE_PORT` siano corretti.

### Errore: "Airbyte non raggiungibile"
Verifica che Airbyte sia avviato e che `AIRBYTE_API_URL` sia corretto.
