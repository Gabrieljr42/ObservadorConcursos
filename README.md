# Observador de Concursos

**A Brazilian public-exam intelligence platform: source monitoring, structured notices, change tracking and a mobile experience designed to work offline.**

Observador de Concursos brings together announcements from examination boards and public institutions. Its backend retrieves and processes notices, tracks meaningful changes and produces notifications. Its React Native app keeps locally synchronized data available even when the device loses connectivity.

> **Status:** active, evolving project. The catalog currently defines **99 sources**, but catalog inclusion does **not** mean every source is live, reliable or fully audited. Consult the [source status](docs/SOURCES_STATUS.md) and [operational documentation](docs/) before interpreting coverage.

## Why it exists

Public examination information is scattered across different portals, document formats and frequently changing pages. Observador aims to make that information easier to discover and follow, while preserving visibility into the origin and status of collected data.

## Architecture at a glance

| Component | Stack | Responsibility |
| --- | --- | --- |
| API | Python, FastAPI | REST endpoints, authentication, listings and synchronization |
| Collectors | HTTP clients, Playwright, PDF parsing | Retrieve and structure source information |
| Background processing | Celery and Redis | Schedule and distribute crawling tasks |
| Database | PostgreSQL 17 | Persist announcements, versions and collection diagnostics |
| Mobile | Expo, React Native, TypeScript, SQLite | Offline-first browsing, saved items and synchronization |
| Runtime | Docker Compose | API, worker, scheduler, PostgreSQL and Redis |

```text
Exam boards / institutions
            |
      crawler workers <---- Celery beat
            |                |
     parsing + validation    Redis
            |
       PostgreSQL <-------- FastAPI
                               |
                        /sync/checkpoint
                               |
                       React Native app
                       local SQLite cache
```

## Capabilities

- **Multi-source monitoring:** a catalog of 99 configured source definitions with dedicated and configurable connectors.
- **Change awareness:** deduplication, version history and significant-change notifications.
- **Document processing:** extraction of embedded text and structured fields from notices, with source-specific parsing and diagnostics.
- **Operational visibility:** collection runs and verification artifacts to help distinguish successful results, legitimate empty results and failures.
- **Offline-first mobile:** local SQLite storage, synchronization checkpoints and an outbox for changes made without connectivity.
- **REST API:** registration, login, source discovery, listings, publication/version history and sync endpoints.

Source quality varies. Scrapers may be blocked or break when institutional pages change, and scanned PDFs may require separate OCR processing. See the documented limitations.

## Repository map

```text
backend/               FastAPI, Celery tasks, connectors, tests
docs/                  Architecture, API, configuration and audits
mobile/                Git submodule for the Expo application
scripts/               Diagnostics and operational helpers
README.md              Project overview
```

**Note on the mobile code:** `mobile/` is a Git submodule. After cloning, initialize submodules; the companion repository is [mobileObservador](https://github.com/Gabrieljr42/mobileObservador). Public access to the backend repository alone does not grant access to a private submodule.

## Local quick start

**Requirements:** Git, Docker and Docker Compose.

```bash
git clone --recurse-submodules https://github.com/Gabrieljr42/ObservadorConcursos.git
cd ObservadorConcursos/backend
cp .env.example .env
```

Replace the example `SECRET_KEY` in `.env` with a secure, randomly generated value. Then start the services:

```bash
docker compose up --build
```

With the API running:

```bash
curl http://localhost:8000/health
# Interactive API documentation: http://localhost:8000/docs
```

Populate the catalog and run a sample collector:

```bash
curl -X POST http://localhost:8000/sources/presets/seed-all
curl -X POST http://localhost:8000/crawl/1/sync
curl http://localhost:8000/concursos
```

Real collection depends on network access and changing third-party websites. Results and success rates are not guaranteed by setup alone.

### Mobile development

After initializing the submodule:

```bash
cd ../mobile
npm install
```

Create a local `.env` with an API base URL reachable from your emulator or device:

```dotenv
EXPO_PUBLIC_API_BASE_URL=http://YOUR_LOCAL_NETWORK_IP:8000
```

Start Expo:

```bash
npx expo start --tunnel
```

Use the host's LAN address for a physical device, rather than `localhost`. See [mobile development](docs/MOBILE.md) for routing, storage and syncing details.

## Engineering notes

The codebase includes a backend test suite, source-specific regression fixtures, audit tooling and operational documentation. The [existing verification notes](docs/DEVELOPMENT.md) report earlier test results; these results are historical and are **not** a claim that the latest commit has been retested.

For a deeper look, start with:

| Document | What you'll find |
| --- | --- |
| [Architecture](docs/ARCHITECTURE.md) | Services, data flow and change detection |
| [Onboarding](docs/ONBOARDING.md) | A guided tour for new contributors |
| [API](docs/API.md) | Endpoints and example requests |
| [Database](docs/DATABASE.md) | Models and persistence |
| [Mobile](docs/MOBILE.md) | SQLite cache, navigation and sync |
| [Configuration](docs/CONFIGURATION.md) | Environment variables and integrations |
| [Development](docs/DEVELOPMENT.md) | Commands, tests and conventions |
| [Source audit](docs/SOURCES_STATUS.md) | Connector verification and limitations |

## Security and scope

- Never commit real API credentials, access tokens or user data.
- The provided development configuration is **not** a production security baseline.
- Review permissions and public information in operational artifacts before publishing repository history.
- Data from official portals should be verified against its original notice; Observador is not an official examination authority.

---

Built and maintained by [João Gabriel Alves Junior](https://github.com/Gabrieljr42).