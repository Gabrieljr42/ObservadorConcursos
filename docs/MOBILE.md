# App mobile (Expo / React Native)

Stack (versões em `mobile/package.json`): Expo SDK 54, React Native 0.81.5, React 19.1, expo-router 6 (navegação por arquivos em `mobile/app/`), axios, `expo-sqlite`, `expo-secure-store`, `expo-background-task` + `expo-task-manager`. Sem testes configurados (`package.json` só tem `start/dev/build/android/ios/web`).

## Telas e navegação

`mobile/app/_layout.tsx` monta `SafeAreaProvider → ThemeProvider → AuthProvider` e protege rotas: não autenticado em `(tabs)`, `concurso/*` ou `preferencias-iniciais` → `/onboarding`; autenticado em `index/onboarding/login/cadastro` → `/(tabs)/inicio`.

| Rota | Papel |
|---|---|
| `/` (`index.tsx`) | redirect → `/onboarding` |
| `/onboarding`, `/login`, `/cadastro` | entrada e criação de conta (online; login cai p/ offline se servidor falhar com 5xx/rede e a conta já foi validada no aparelho) |
| `/preferencias-iniciais`, `/privacidade-seguranca` | pós-cadastro |
| `/(tabs)/inicio` | lista principal (lê SQLite local) |
| `/(tabs)/busca` | busca local |
| `/(tabs)/atualizacoes` | `recent_updates` + `my_updates` locais |
| `/(tabs)/alertas` | CRUD de alertas (locais, com outbox) |
| `/(tabs)/salvos` | favoritos locais |
| `/(tabs)/perfil` | conta, preferências, sync |
| `/concurso/[id]` | detalhe + publicações + versões (locais) |
| `/notificacoes` | notificações locais |

Componentes em `mobile/src/components/` (`ConcursoCard`, `UpdateCard`, `TimelineItem`, `PublicationCard`, `StatusBadge`…); listas de apoio em `src/constants/` (`areas.ts`, `bancas.ts`); tema em `src/theme/`; formatação em `src/utils/formatters.ts`.

## Offline-first: ler local, sincronizar depois

Regra de ouro: **telas nunca consultam a API para listagens**. `mobile/src/api/*.ts` são fachadas sobre `mobile/src/db/repositories.ts` (SQLite `observador.db`):

- `client.ts` — axios com `baseURL = EXPO_PUBLIC_API_BASE_URL` (fallback `https://api.observador.tech`) + interceptor que injeta o Bearer. `fetchConcursos/byId` leem o SQLite; `getDemo*` estão desativados.
- `auth.ts` — login/cadastro/refresh (único uso direto de rede fora do sync).
- `alerts/favorites/preferences/notifications/updates/publications.ts` — delegam a `localAlerts`, `localFavorites`, etc.

### Banco local (`src/db/database.ts`)

Tabelas-espelho do checkpoint + controle: `metadata`, `user_cache`, `concursos`, `publications`, `versions`, `recent_updates`, `my_updates`, `favorites`, `alerts` (`local_id` negativo p/ pendentes, `remote_id` após sync), `notifications`, `preferences`, `outbox` (`op`, `entity_key`, `payload`). `applyCheckpoint()` **substitui** o conteúdo local em transação exclusiva (wipes + inserts) e grava `last_sync_at`.

### Ciclo de sync (`src/sync/syncService.ts`)

1. `ensureServerSession()`: testa `GET /auth/me`; se `401` e houver refresh token, renova.
2. `syncOutbox()`: envia operações na ordem (`favorite_add/remove`, `preferences_put`, `notification_read`, `notifications_read_all`, `alert_create/update/delete`); `404` em operações de remoção/leitura descarta o item; `alert_create` reconcilia `remote_id`.
3. `GET /sync/checkpoint` (timeout 45s) → `applyCheckpoint()` → atualiza usuário lembrado.

Agendamento: `syncIfDue()` pula se a última tentativa tem < 1h (`SYNC_INTERVAL_MS`); `AuthProvider` chama no login, a cada 5 min com app aberto e ao voltar ao foreground (`AppState`); `background.ts` registra `observador-hourly-checkpoint-sync` (só roda com sessão ativa).

### Sessão e conta offline (`src/storage/auth.ts`, `AuthProvider.tsx`)

- Tokens no SecureStore (nativo) ou AsyncStorage (web). `logout` só fecha a sessão local (`closeLocalSession` + apaga access token) — **não** apaga a conta lembrada nem revoga no servidor, então o mesmo aparelho pode relogar offline.
- `rememberOfflineAccount` guarda `{email, salt, verifier SHA-256(salt, email, senha)}`; `verifyOfflineAccount` permite login sem rede após falha 5xx/rede. `401/403` reais nunca caem para offline.
- `forgetOfflineAccount` (esquecer tudo) apaga tokens + conta + sessão — único caminho de “logout total”.

## Configuração e comandos

```powershell
cd mobile
npm install
npx expo start --tunnel        # Expo Go (recomendado p/ aparelho físico)
```

Variáveis (`mobile/.env`, ver [CONFIGURATION.md](CONFIGURATION.md)):

```text
EXPO_PUBLIC_API_BASE_URL=http://SEU_IP_LOCAL:8000
```

| Alvo | URL da API |
|---|---|
| Navegador (`--web`) | `http://localhost:8000` |
| Celular físico (mesma rede) | `http://SEU_IP_LAN:8000` (ex.: `192.168.0.105`) |
| Emulador Android | `http://10.0.2.2:8000` |

Outros comandos: `npm run dev` (web :3000), `npm run build` (`expo export -p web`), `npx expo start --android|--ios|--web`. Builds nativos via EAS: `eas.json` tem `preview` (APK interno) e `production` (AAB), ambos com `EXPO_PUBLIC_API_BASE_URL=https://api.observador.tech`.

## Limitações conhecidas

- `npx tsc --noEmit` falha hoje em `components/ExternalLink.tsx` (prop `href: string` incompatível com rotas tipadas do expo-router; `typedRoutes: true` em `app.json`). Não bloqueia o Expo, mas deve ser corrigido (ver troubleshooting).
- `src/types/concurso.ts` está desatualizado frente ao backend (`ConcursoOut`): faltam `vagas`, `salario_min/max`, `escolaridade`, `taxa`, `prova_data`, campos `edital_pdf_*`. Telas que precisarem desses campos devem estender o tipo.
- `runAlertsSync` no app é stub offline (`{processed_alerts: 0, ...}`) — alertas são avaliados no servidor.
- `applyCheckpoint` faz replace total: alterações locais ainda na outbox **não** drenada seriam sobrescritas em caso de sync parcial — na prática o sync drena a outbox antes, mas não usar o banco local como “fonte de verdade” permanente.
- `origin` padrão em `app.config.js` aponta para uma URL `*.run.app` (herança de protótipo); builds EAS usam `https://api.observador.tech`. Confirmar com o mantenedor qual deve prevalecer.
