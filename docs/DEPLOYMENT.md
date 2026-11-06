# Deployment runbook

This project ships with two Compose layers:

- `compose.yml` — local development (Postgres + API).
- `compose.prod.yml` — production overlay (no published API/DB ports, Caddy reverse proxy, log rotation, read-only containers).

The production overlay can be run locally without a VPS, which is useful for verifying the deployment shape.

## Local production-style run

```bash
cp .env.example .env   # once; fill in SECRET_KEY and POSTGRES_* values
docker compose -f compose.yml -f compose.prod.yml up --build
```

What happens:

1. PostgreSQL starts and becomes healthy.
2. `migrate` runs `alembic upgrade head` and exits.
3. The API starts behind Caddy.
4. Caddy listens on `http://localhost` (port 80). The API itself is **not** published to the host.

Verify:

```bash
curl http://localhost/health/ready
curl http://localhost/openapi.json
```

Stop it with:

```bash
docker compose -f compose.yml -f compose.prod.yml down
```

To use TLS locally, set `SITE_ADDRESS=https://localhost` and trust Caddy's internal CA, or simply keep `http://localhost` for the demo.

## Deploying to a VPS (when you have one)

### 1. Prerequisites

- A Linux VPS (Ubuntu 24.04 or similar).
- A domain or subdomain, with an `A` record pointing at the VPS IP.
- SSH access with a key.

### 2. Prepare the server

```bash
# As a sudo-capable user
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl git ufw

# Install Docker Engine and the Compose plugin
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"

# Firewall: SSH, HTTP and HTTPS only
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Log out and back in so the Docker group membership applies.

### 3. Configure the application

```bash
git clone git@github.com:GuilhermeValerioDev/expense-tracker-api.git
cd expense-tracker-api
cp .env.example .env
```

Set production values in `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://app_user:strong-password@localhost:5432/expense_tracker
SECRET_KEY=<output of: openssl rand -base64 48>
POSTGRES_USER=app_user
POSTGRES_PASSWORD=strong-password
POSTGRES_DB=expense_tracker
SITE_ADDRESS=api.example.com
```

Then protect the file:

```bash
chmod 600 .env
```

Notes:

- `SITE_ADDRESS` is the Caddy site address. With a real domain, Caddy obtains and renews TLS certificates automatically. It requires ports 80 and 443 to be reachable.
- The API container reads `DATABASE_URL` from `compose.prod.yml`, which rewrites it to the `postgres` service host inside the Compose network.
- Only Caddy publishes ports. PostgreSQL and the API are internal.

### 4. First deploy

```bash
docker compose -f compose.yml -f compose.prod.yml up -d --build
```

The `migrate` service runs before the API. Verify:

```bash
docker compose -f compose.yml -f compose.prod.yml ps
curl https://api.example.com/health/ready
```

You should get `{"status":"ok","database":"ok"}`.

### 5. Backups

Create a backup:

```bash
./scripts/backup.sh
```

The script writes a timestamped custom-format dump to `backups/` with `umask 077`.

Restore into the configured database (destructive, asks for confirmation):

```bash
./scripts/restore.sh backups/expense_tracker_YYYYMMDDTHHMMSSZ.dump
```

Test a restore without touching production by targeting a scratch database:

```bash
docker compose exec -T postgres psql -U app_user -d postgres -c 'CREATE DATABASE restore_test;'
TARGET_DB=restore_test ./scripts/restore.sh backups/<file>.dump --yes
docker compose exec -T postgres psql -U app_user -d restore_test -c 'SELECT count(*) FROM users;'
docker compose exec -T postgres psql -U app_user -d postgres -c 'DROP DATABASE restore_test;'
```

Automate it with cron:

```cron
# Daily at 03:15 UTC
15 3 * * * cd /home/deploy/expense-tracker-api && ./scripts/backup.sh >> /var/log/expense-backup.log 2>&1
```

Copy backups off the server regularly (`scp`, `rclone`, or object storage). A backup that only exists on the same disk is not a backup.

### 6. Updates

```bash
git pull
docker compose -f compose.yml -f compose.prod.yml up -d --build
```

The `migrate` service applies any new migrations before the API is recreated.

### 7. Rollback

```bash
git checkout <previous-tag>
docker compose -f compose.yml -f compose.prod.yml up -d --build
```

If the release included a migration, roll the database back deliberately:

```bash
docker compose exec -T migrate alembic downgrade -1
```

Review the migration's `downgrade()` first. Data-changing migrations may not be safely reversible.

### 8. Logs and health

```bash
docker compose -f compose.yml -f compose.prod.yml logs -f api
docker compose -f compose.yml -f compose.prod.yml logs -f caddy
```

The API emits JSON logs with request IDs when `LOG_JSON=true` (set by the production overlay). Health endpoints:

- `/health` — liveness.
- `/health/ready` — readiness, checks the database.

## Security checklist

- [ ] Only ports 22, 80 and 443 are open.
- [ ] `.env` is `chmod 600` and never committed.
- [ ] PostgreSQL is not published to the host.
- [ ] `SECRET_KEY` is a long random value and differs from development.
- [ ] CORS is configured only if a browser frontend needs it.
- [ ] Rate limiting is active on `/auth/login` and `/auth/register`.
- [ ] Backups run on a schedule and are copied off the server.
- [ ] A restore has been tested at least once.
- [ ] Log rotation is configured (the production overlay does this).

## Scaling note

Rate limiting currently uses in-process memory, which is correct for a single API container. If you run multiple API replicas or workers, point the limiter at Redis and run migrations as a dedicated job rather than per replica.
