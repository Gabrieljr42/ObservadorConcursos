# Observador de Concursos

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React Native](https://img.shields.io/badge/React%20Native-Expo-000020.svg?logo=expo)](https://expo.dev)
[![PostgreSQL 17](https://img.shields.io/badge/PostgreSQL-17-336791.svg?logo=postgresql)](https://www.postgresql.org/)
[![Celery & Redis](https://img.shields.io/badge/Celery-Redis-CC0000.svg?logo=redis)](https://docs.celeryq.dev)

> **A Brazilian public examination intelligence platform**: automated source monitoring, structured notices, document parsing, change tracking, and an offline-first mobile experience.

---

Observador de Concursos monitors and aggregates announcements, publications, and official notices from dozens of examination boards (*bancas examinadoras*) and public institutions throughout Brazil. 

Its FastAPI backend continuously crawls and parses announcements, tracks version changes, processes notice PDFs, and generates proactive notifications. Its companion React Native/Expo app keeps data cached in a local SQLite database, allowing candidates to search, save, and receive updates even with intermittent or absent internet connectivity.

---

## 🏛️ Architecture Overview

```text
  Examination Boards / Public Portals (99 sources cataloged)
                          │
                          ▼
            ┌───────────────────────────┐
            │   Crawlers & Connectors   │◄── Celery Beat (Scheduler)
            │  (HTTP / Playwright / PDF) │
            └─────────────┬─────────────┘
                          │
                          ▼
            ┌───────────────────────────┐
            │   Parsing & Validation    │◄── Redis (Queue & Broker)
            └─────────────┬─────────────┘
                          │
                          ▼
            ┌───────────────────────────┐
            │   PostgreSQL 17 Database  │
            │   (Announcements, Vers.)  │
            └─────────────▲─────────────┘
                          │
                          ▼
            ┌───────────────────────────┐
            │   FastAPI REST Engine     │
            │  (/sync/checkpoint & API) │
            └─────────────▲─────────────┘
                          │
             HTTPS / Offline Sync Checkpoint
                          │
                          ▼
            ┌───────────────────────────┐
            │   React Native (Expo)     │
            │   Local SQLite Outbox     │
            └───────────────────────────┘
```

| Component | Technology | Responsibility |
| :--- | :--- | :--- |
| **Backend API** | Python 3.12, FastAPI, Pydantic, SQLAlchemy 2 | REST endpoints, authentication (JWT), search, synchronization checkpoints. |
| **Collectors & Parsers** | HTTPX, BeautifulSoup4, Playwright, PyPDF | Crawling portals, extracting notice metadata, PDF text parsing. |
| **Worker & Queue** | Celery, Redis | Distributed task execution, scheduled crawls, retries. |
| **Primary Database** | PostgreSQL 17 | Stores tenders, notices, publication logs, user subscriptions, and audit logs. |
| **Mobile App** | React Native, Expo, TypeScript, SQLite | Offline-first candidate experience, optimistic favorites, local caching. |
| **Infrastructure** | Docker Compose | One-command orchestration for API, worker, scheduler, PostgreSQL, and Redis. |

---

## ✨ Features

- **Multi-Source Catalog:** 99 configured source definitions with dedicated and generic connectors.
- **Change Detection & Versioning:** Tracks document amendments, errata, date extensions, and changes across notices with SHA-256 fingerprinting.
- **Document Processing:** Automated extraction of vacancies, positions, salaries, and deadlines from published PDFs.
- **Offline-First Synchronization:** Candidates can save items and register alerts offline. Changes queue locally in SQLite and reconcile seamlessly when back online.
- **Operational Auditing:** Built-in audit suites and historical execution records to distinguish portal downtime from empty results.

---

## 📂 Repository Structure

```text
.
├── backend/                  # FastAPI backend, Celery tasks, connectors, test suite
│   ├── app/                  # Application code (API, connectors, models, schemas)
│   ├── tests/                # Unit and integration test fixtures
│   ├── Dockerfile            # Container definition for API and Celery workers
│   └── requirements.txt      # Python dependencies
├── docs/                     # Full technical documentation, runbooks, and audits
│   ├── ARCHITECTURE.md       # Detailed system design and data flows
│   ├── API.md                # REST API endpoint specifications
│   ├── DATABASE.md           # Database models and schema migrations
│   ├── CONFIGURATION.md      # Environment variable reference
│   └── SOURCES_STATUS.md     # Current status of the 99 monitored exam portals
├── mobile/                   # React Native (Expo) mobile application (Git submodule)
├── scripts/                  # Operational utilities and live audit tools
│   └── verification/         # Playwright E2E and offline roundtrip verification scripts
├── docker-compose.yml        # Root Docker Compose for orchestrating all backend services
├── .env.example              # Root environment template
└── LICENSE                   # MIT License
```

> ⚠️ **Note on Mobile Submodule:**  
> The `mobile/` directory is linked as a Git submodule to [mobileObservador](https://github.com/Gabrieljr42/mobileObservador). When cloning, use `--recurse-submodules`. If the mobile repository is private, ensure your GitHub account has collaborator access or initialize only the backend.

---

## 🚀 Quick Start

### Prerequisites
- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) & Docker Compose

### 1. Clone the Repository

```bash
git clone --recurse-submodules https://github.com/Gabrieljr42/ObservadorConcursos.git
cd ObservadorConcursos
```

*(If you already cloned without submodules, run `git submodule update --init --recursive`)*

### 2. Configure Environment

Copy the example configuration to `backend/.env`:

```bash
cp .env.example backend/.env
```

> **Important:** Open `backend/.env` and replace `SECRET_KEY=change-me-in-production` with a secure random key.

### 3. Start Backend Services

Run Docker Compose directly from the root directory:

```bash
docker compose up --build
```

The stack initializes:
- **FastAPI Backend:** http://localhost:8000
- **Interactive Swagger Docs:** http://localhost:8000/docs
- **PostgreSQL 17:** localhost:5432
- **Redis 7:** localhost:6379
- **Celery Worker & Beat Scheduler**

Verify API health:
```bash
curl http://localhost:8000/health
```

### 4. Seed Sources & Test Crawl

In a separate terminal, seed the catalog and trigger a sample crawl:

```bash
# Seed all 99 preset sources
curl -X POST http://localhost:8000/sources/presets/seed-all

# Trigger immediate synchronous crawl for source ID 1
curl -X POST http://localhost:8000/crawl/1/sync

# Check stored contests
curl http://localhost:8000/concursos
```

---

## 📱 Mobile Application (Expo)

To develop or run the mobile application locally:

```bash
cd mobile
npm install
cp .env.example .env
```

In `mobile/.env`, set the API URL:
- Physical device on Wi-Fi: `http://<YOUR_LOCAL_NETWORK_IP>:8000`
- Android Emulator: `http://10.0.2.2:8000`
- Web browser: `http://localhost:8000`

Start the Expo bundler:
```bash
npx expo start
```

Press `a` for Android, `i` for iOS simulator, or `w` for Web.

---

## 🧪 Testing & Verification

[Verificação local de 25/10/2026](docs/VERIFICACAO-REAL-2026-10-25.md): coleta oficial ACCESS/IPSEMG, publicação revisada sem duplicação, busca e detalhe no navegador, favoritos e alertas com a origem indisponível e sincronização após reconectar. O relatório distingue esse fluxo web dos testes ainda pendentes em dispositivos nativos.

### Backend Tests

Run pytest inside a virtual environment or Docker:

```bash
cd backend
python -m pytest tests/test_sanity_validation.py tests/test_idempotency.py tests/test_connectors_fixtures.py -v
```

### End-to-End & Sync Roundtrip Verification

Integration and offline-sync verification scripts are located in `scripts/verification/`:

```bash
# Requires Playwright: npm install playwright
node scripts/verification/verify-favorite-roundtrip.cjs
node scripts/verification/verify-app-reopen.cjs
```

---

## 📖 Technical Documentation

For deeper details, consult our documentation:

| Document | Description |
| :--- | :--- |
| [Architecture](docs/ARCHITECTURE.md) | Component interactions, data lifecycle, and sync protocol |
| [API Documentation](docs/API.md) | Endpoint specifications, payloads, and authentication |
| [Database Schema](docs/DATABASE.md) | PostgreSQL models, relations, and indices |
| [Configuration Guide](docs/CONFIGURATION.md) | Complete list of environment variables |
| [Mobile Details](docs/MOBILE.md) | SQLite schema, outbox pattern, and offline handling |
| [Development Guide](docs/DEVELOPMENT.md) | Contribution standards, test guidelines, and linting |
| [Source Status Audit](docs/SOURCES_STATUS.md) | Audit status across all 99 monitored institutions |

---

## 🔒 Security & Scope

- **Public Data Only:** Observador monitors publicly accessible exam portals. It never bypasses authentication walls or captures protected candidate records.
- **Credentials:** Never commit `.env` files, production keys, or database credentials.
- **Legal Notice:** Information is gathered from public domain institutional portals. Observador de Concursos is an independent aggregator and is not affiliated with or endorsed by any official examination authority.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the [LICENSE](LICENSE) file for details.

Maintained with ❤️ by [João Gabriel Alves Junior](https://github.com/Gabrieljr42).
