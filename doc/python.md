# Production-Worthy Python Code Playbook

Your no-BS checklist for writing maintainable, scalable, secure Python services.

---

## 1. Project Structure & Organization

```
myapp/
├── myapp/
│   ├── __init__.py
│   ├── core/           # configs, constants
│   ├── api/            # routers, controllers
│   ├── services/       # business logic
│   ├── models/         # Pydantic/DB schemas
│   ├── utils/          # pure helpers
│   └── main.py         # entrypoint
├── tests/              # unit & integration tests
├── scripts/            # ops scripts (migrations, tasks)
├── .env.example
├── pyproject.toml
└── README.md
```

- **One responsibility per module**—no Frankenfiles.

---

## 2. Configuration Management

```python
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DEBUG: bool = Field(False, env="DEBUG")

    class Config:
        env_file = ".env"

settings = Settings()
```

- **Use Pydantic BaseSettings** to load & validate ALL env vars.
- **Fail fast** if a required var is missing/malformed.
- **No magic strings**—pull defaults from `settings`.

---

## 3. Dependencies & Injection

- **Don’t import clients at top-level.**
- Expose constructors via dependency injection (`Depends` in FastAPI).
- **Swappable implementations** = effortless testing & upgrades.

---

## 4. Logging & Observability

```python
import logging, sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout
)
log = logging.getLogger(__name__)
```

- **Structured JSON logs** with timestamp, level, module, request_id.
- **Correlation IDs** across HTTP/async boundaries.
- **Log at boundaries**: INFO on entry/exit, DEBUG on payloads, WARN/ERROR on failures.

---

## 5. Error Handling & Exceptions

```python
class IngestionError(Exception):
    pass

try:
    ...
except IngestionError as e:
    raise HTTPException(status_code=422, detail=str(e))
```

- **Define domain errors** (`IngestionError`, `QueryError`, etc.).
- **Map exceptions** to proper HTTP codes.
- **Never catch** broad `Exception` in business logic—let unexpected errors bubble.

---

## 6. Testing Strategy

```
tests/
├── unit/
├── integration/
└── conftest.py   # fixtures & test factories
```

- **Unit tests** for pure functions & edge cases.
- **Integration tests** against real or in-memory datastore.
- **Contract tests** for external APIs (use VCR or mocks).
- **Coverage gates**: aim ≥ 90 % on critical modules.

---

## 7. Security Hygiene

- **Secrets only in vault/env**, never in code or logs.
- **Validate all inputs** via Pydantic schemas.
- **Rate-limit** public endpoints.
- **Dependency scanning** (`pip-audit`, `safety`) in CI.

---

## 8. Performance & Scalability

- Profile hot paths (e.g. `cProfile`, `pyinstrument`).
- Use **async** I/O or worker pools for blocking operations.
- **Cache** expensive calls (Redis, in-process TTL).
- **Batch** operations (bulk writes, vectorized NumPy).

---

## 9. CI/CD & Deployment

- **Lint** (flake8/isort) + **format** (black) in pre-commit hooks.
- **Automate tests** + security checks on every PR.
- **Reproducible container builds** (pin base-image hash).
- **Canary/blue-green** vs. direct deploy—roll back faster than push forward.

---

## 10. Documentation & Onboarding

- **Auto-generate API docs** (OpenAPI/Swagger).
- **README**: setup, run, test, deploy in ≤ 5 steps.
- **CHANGELOG** (Keep a Changelog style).
- **Docstrings** on public APIs with “what/why,” not “how.”

---

## 11. Maintenance & Code Reviews

- **PR size < 200 LOC**—small diffs merge faster.
- **Enforce review checklists**: security, performance, tests, docs.
- **Refactor ruthlessly**—carry tech debt as a conscious ledger, not hidden backlog.

---

## 12. Developer Tooling: uv & mise

### uv

- Project-scoped venv + interpreter manager.
- Reads `.python-version`, emits `uv.lock` for reproducibility.

```bash
# pin your Python version
echo "3.12" > .python-version

# run any script inside a per-project venv (auto-created)
uv run hello.py

# install interpreters
uv python install 3.11.4
```

### mise

- Universal tool installer + task runner + env-var injector.
- Manages multiple runtimes and per-dir env files.

```bash
# install mise
curl -sL https://github.com/jdx/mise/releases/latest/download/install.sh | bash

# install Python via mise
mise install python@3.11.12

# define tasks in mise.toml
[tools.tasks]
test = "pytest --maxfail=1 --disable-warnings"
```

### Sync uv ↔ mise

```bash
uv python install 3.11.12
mise install python@3.11.12

# sync installs both ways
mise sync python --uv
mise sync python --pyenv
```

**Pro Tip**: In `mise.toml`, enable uv venv auto-pickup:

```toml
[settings]
python.uv_venv_auto = true
```

---

> **TL;DR**
> Treat every line of code as tomorrow’s emergency. Invest in config, structure, tests, and observability up-front—so you don’t drown in incidents later.
