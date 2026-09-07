# Security Tracker

This tracker covers application and operational security for the automation manager.

Status values: `[ ]` not started, `[-]` in progress, `[x]` complete, `[!]` blocked or needs a decision.

## Phase 0: Inventory and Boundaries

- [x] Identify every sensitive value: API tokens, website credentials, browser session files, cookies, logs, and state files.
- [x] Document which endpoints are local-only and which clients need remote access.
- [x] Confirm the website's automation and session policies.
- [x] Define an incident response step for a leaked API token or browser session.
- [x] Identify which processes/components are trusted and which inputs are considered untrusted.

### Phase 0 Findings

#### Sensitive Values

- `forsaken_session.json`: browser session cookie and website authentication state. Treat as a password-equivalent secret.
- Website username, password, and CAPTCHA values: used only by the manual session manager and not currently stored by the project.
- Future API token: not implemented yet; must be stored outside source control.
- `state/*.json`: operational details such as credits, provider identifiers, cooldowns, and timestamps.
- `logs/*.log`: potentially sensitive operational and browser error information.
- `automations.json`: deployment configuration, URLs, strategy settings, and local file paths. It is already ignored by Git.

The existing `.gitignore` covers `*_session.json`, `*.log`, `automations.json`, `available_votes.json`, and `/state/`. This protects new files from ordinary Git tracking, but it does not remove files already committed or protect them from local users and backups.

#### Endpoint Boundaries

- `/api/hello`: health/basic connectivity endpoint.
- `/api/automations`: lists configured automation metadata and process status.
- `/api/automations/{id}/status`: reads process status.
- `/api/automations/{id}/pids`: exposes worker PIDs.
- `/api/automations/{id}/start`, `/stop`, `/stop-all`: process-control endpoints and should be administrator/operator-only.
- `/api/automations/{id}/state`: exposes persisted automation details and should be protected.
- `/api/events`: live event stream and should be protected.
- `/api/events/test`: test event injection and should be removed or restricted outside development.
- `/api/internal/automation/state`: worker-to-API callback. It should be local-only or authenticated separately.

No endpoint authentication is currently implemented. Until Phase 1 is complete, the API should be treated as local-only and should not be exposed directly to the network.

#### Trust Boundaries

- Trusted: the local service account, the API process, worker processes, and reviewed local configuration.
- Untrusted: API callers, frontend clients, automation configuration if modified by an untrusted user, external vote-provider pages, redirects, and browser content returned by the remote website.
- Sensitive boundary: the worker sends state over HTTP to the API and the browser loads external provider pages in the same automation context.

#### Incident Response

If an API token is exposed, revoke or replace it and review API logs. If `forsaken_session.json` or website credentials are exposed, log out or revoke the website session, regenerate the session, rotate the website password if appropriate, replace the file on every host, and review recent worker activity.

## Phase 1: Single-User Local Hardening

Priority: complete before remote access is introduced.

- [x] Add `forsaken_session.json` and other browser storage files to `.gitignore`.
- [x] Verify the session file is readable only by the service account (`chmod 600` on Linux).
- [x] Keep website credentials outside the repository and outside `automations.json`.
- [x] Add a long random API token through an environment variable or secret manager.
- [x] Require the API token for start, stop, state, PID, and event endpoints.
- [x] Restrict CORS to the configured local frontend origin.
- [x] Bind the API to localhost or a private interface unless remote access is required.
- [x] Restrict the internal state-update endpoint by requiring the API token.
- [x] Remove cookies, credentials, CAPTCHA values, and session contents from logs.
- [x] Do not run the API or workers with unnecessary administrative/root privileges during development.

### Phase 1 Configuration

Set the same high-entropy token in the API and worker environment before starting either process:

```text
AUTOMATION_API_TOKEN=<long-random-secret>
```

Requests to protected endpoints must send the token in the `X-API-Token` header. The worker uses the same header when publishing state to the internal API endpoint. If the environment variable is missing, protected API requests return `503` and worker state publishing is refused.

The development API is currently localhost-only.

## Phase 2: Authentication and Authorization Growth

Priority: required when more users or remote clients are introduced.

This phase stays focused on application security and access control. It does not include infrastructure deployment, reverse proxies, networking hardening, or hosting concerns.

- [x] Define the target identity model for local operators, remote users, and service accounts.
- [ ] Replace the shared token with per-user or per-client identities.
- [x] Add roles such as administrator, operator, and read-only viewer.
- [x] Add per-automation permissions and ownership boundaries.
- [ ] Add token expiration, rotation, revocation, and audit history.
- [ ] Use an established identity provider or OAuth2/OIDC instead of building password authentication.
- [ ] Add rate limits and failed-authentication monitoring.
- [ ] Add CSRF protection if browser cookie authentication is introduced.
- [x] Add explicit authorization checks for automation start/stop, state access, and event-stream read access.
- [x] Record a decision on whether the service remains local-only or moves behind a real identity-provider-backed access layer.

### Phase 2 Practical Milestones

- [x] Confirm whether the project should support only trusted local operators or a multi-user remote access model.
- [x] Separate authentication from authorization so end users and automation workers are not treated as the same principal.
- [x] Define the minimum permissions needed for start/stop actions versus read-only monitoring.
- [x] Decide how tokens or sessions are managed for browser automation actions that call into internal endpoints.
- [x] Treat any future web UI as a separate trust boundary from the API and automation workers.

These milestones are satisfied for the current local-only design. The remaining unchecked items above are for the future multi-user or remote-identity model, not for the current trusted-local deployment.

## Phase 3: Operational Assurance

- [ ] Add security-focused tests for authentication, authorization, CORS, and internal endpoints.
- [ ] Add tests proving sensitive values never appear in logs or API responses.
- [ ] Run dependency vulnerability scanning in CI.
- [ ] Run static analysis and secret scanning in CI.
- [ ] Review subprocess, file-path, and URL inputs for injection or traversal risks.
- [ ] Review external provider pages as untrusted content and isolate browser permissions.
- [ ] Document session re-authentication and recovery procedures.

## Current Known Gaps

- API authentication currently uses one shared single-user token.
- Token rotation and revocation are manual until multi-user authentication is introduced.
- The browser session file is sensitive and must remain outside version control.
- CAPTCHA-based re-authentication requires human intervention or a remote browser display.
- The state and log files may reveal operational details and need permission controls.

## Decisions To Record

- Secret storage: environment variables, systemd credentials, or a secret manager.
- Authentication model after multi-user support is needed: OIDC provider or another established identity system.