# Web Automation Manager

A local automation manager for browser-based workflows. The project uses a generic automation and strategy architecture so additional automation types and strategies can be added without changing the manager lifecycle.

## Requirements

- Python 3.14.7
- Playwright and a locally installed Chromium browser
- A valid browser session for the configured provider

The supported Python version is declared in `.python-version`.

## Setup

Create and activate a virtual environment, then install the runtime dependencies:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
playwright install chromium
```

The repository intentionally does not include local automation configuration, browser sessions, logs, or state files. Create `automations.json` locally from the configuration format shown below.

## Configuration

`automations.json` is a local-only file and is ignored by Git. A minimal configuration looks like this:

```json
{
	"automations": [
		{
			"id": "example",
			"name": "Example Automation",
			"type": "web",
			"strategy": "voting",
			"config": {
				"web": {
					"url": "https://example.com",
					"session_file": "example_session.json"
				},
				"strategy": {
					"action_delay_seconds": 0
				}
			},
			"state_file": "state/example.json",
			"log_file": "logs/example.log",
			"check_interval_seconds": 60,
			"enabled": true
		}
	]
}
```

Configuration loading accepts only HTTP(S) web URLs and project-relative session, state, and log paths. Parent traversal and absolute paths are rejected.

## API

Start the FastAPI application with an ASGI server:

```powershell
$env:AUTOMATION_API_TOKEN = "replace-with-a-long-random-token"
uvicorn api:app --reload
```

Protected requests must send the configured token in the `X-API-Token` header:

```powershell
Invoke-RestMethod `
	-Uri "http://127.0.0.1:8000/api/automations" `
	-Headers @{ "X-API-Token" = $env:AUTOMATION_API_TOKEN }
```

The API uses role-based access for the local trusted-operator model:

- `admin`: full administrative access
- `operator`: start and stop permitted automations
- `viewer`: read-only monitoring access
- `service`: worker-to-API state publication

Token metadata can be supplied with `AUTOMATION_API_TOKENS` when multiple local principals, roles, scopes, expiration, or revocation state are needed. Keep all token values outside the repository.

## Running Workers

The API starts workers from the configured automation definitions. A worker can also be started directly:

```powershell
python run_automation.py <automation-id>
```

Workers publish state to the API using the configured API token and the `service` role. They also persist state under the configured `state_file` path.

## Architecture

- `api.py`: FastAPI routes, event streaming, and process-control endpoints
- `automation/core/`: manager, process lifecycle, state, events, security, and shared abstractions
- `automation/types/web/`: Playwright browser automation and web strategies
- `run_automation.py`: worker process entry point
- `tests/`: unit and API regression tests

The manager is automation-type agnostic. Each automation type supplies its implementation, and each strategy supplies the workflow-specific behavior.

## Tests and Checks

Run the local test suite:

```powershell
python -m pytest -q
```

The GitHub Actions workflow runs on Python 3.14.7 and currently includes:

- Full tests with a 90% application coverage threshold
- Dependency vulnerability scanning with `pip-audit`
- Dependency consistency checks with `pip check`
- Bandit static analysis
- Gitleaks secret scanning
- Ruff linting
- Pyright type checking
- Python compilation and application import smoke checks

## Sensitive Files

Never commit:

- Browser session files such as `*_session.json`
- `automations.json`
- API tokens or website credentials
- Runtime state and logs

The project is intended for local trusted operators. Multi-user identity providers, remote access, and cookie-based browser authentication are intentionally deferred until they are needed.