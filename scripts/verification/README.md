# Verification & Diagnostic Scripts

This directory contains standalone end-to-end (E2E), integration, and diagnostic scripts used during development, acceptance testing, and pilot verification runs.

## Overview

- **`diagnose-login-route.cjs`**: Playwright headless browser check verifying authentication flows and network responses against the local/test frontend.
- **`verify-app-reopen.cjs`**: Verifies local caching, persistence across application reopen, and offline state preservation.
- **`verify-alert-roundtrip.cjs` / `verify-alert-roundtrip-real.cjs` / `verify-alert-roundtrip-review.cjs`**: End-to-end verification of user alert subscriptions, notifications dispatch, and roundtrip delivery.
- **`verify-favorite-roundtrip.cjs` / `verify-favorite-roundtrip-real.cjs`**: E2E test verifying contest favoriting, local offline sync, and server reconciliation.
- **`verify-t007-postgres.py`**: PostgreSQL isolated review runner for migration and schema testing against review containers.

## Running

Most `.cjs` scripts require Playwright installed:

```bash
npm install playwright
node scripts/verification/verify-favorite-roundtrip.cjs
```
