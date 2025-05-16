Here's a straight-to-the-point guide for ditching requirements.txt and fully embracing uv plus pyproject.toml for Python dependency and project management.

⸻

1. Why switch?
	•	Unified toolset: uv replaces pip, pip-tools, poetry, virtualenv, and more — all in one fast Rust binary (10–100× faster than plain pip).
	•	Standardized metadata: All your project's metadata (name, version, dependencies, optional/dev groups) lives in pyproject.toml, following PEP 621, instead of scattered files.
	•	Reproducible lockfile: uv.lock captures complete dependency graphs and sources for auditability and speed.

⸻

2. Install uv

# Via pip
pip install uv

# Or platform installer (macOS/Linux):
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or Windows PowerShell:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

⸻

3. Initialize your project

From an empty directory, run:

uv init

This will:
	1.	Create pyproject.toml with a [project] table (name, version, empty dependencies).
	2.	Generate default settings under [tool.uv].
	3.	(Optionally) Pin your Python via uv python pin 3.x.

⸻

4. Declaring dependencies

Here's a comprehensive example of a modern pyproject.toml:

[project]
name = "my-app"
version = "0.1.0"
description = " Python API for the your app"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "docling>=2.30.0",
    "fastapi>=0.115.12",
    "httpx>=0.28.1",
    "langchain>=0.3.23",
    "langchain-community>=0.3.21",
    "langchain-openai>=0.3.13",
    "pydantic>=2.11.3",
    "pydantic-settings>=2.8.1",
    "python-multipart>=0.0.20",
    "uvicorn>=0.34.1",
]

[dependency-groups]
dev = [
    "mypy>=1.15.0",
    "pytest>=8.3.5",
    "pytest-asyncio",
    "ruff>=0.11.5",
    "types-pyyaml>=6.0.12.20250402",
]

# Tool configurations can also be included
[tool.ruff]
line-length = 88
target-version = "py312"

exclude = [
    "src/openapi_server/**",
]

[tool.ruff.lint]
select = [
    # pycodestyle
    "E",
    # Pyflakes
    "F",
    # pyupgrade
    "UP",
    # flake8-bugbear
    "B",
    # flake8-simplify
    "SIM",
    # isort
    "I",
]

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"

[tool.pytest.ini_options]
testpaths = ["tests",]
asyncio_mode = "auto"
pythonpath = ["."]
asyncio_default_fixture_loop_scope = "function"

[tool.mypy]
strict = true
pretty = true
warn_unreachable = true

⸻

5. Adding or removing deps

Use the CLI so your TOML stays in sync:
	•	Add:

uv add fastapi

→ appends "fastapi>=x.y.z" to [project].dependencies.

	•	Remove:

uv remove fastapi

→ drops it (and any [tool.uv.sources] entry if unused).

⸻

6. Development & optional dependencies

There are two ways to manage development dependencies:

1. Using project.optional-dependencies (recommended):

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0"
]

Install with:
uv sync --extra dev

2. Using dependency-groups (experimental):

[dependency-groups.dev]
dependencies = [
    "pytest>=7.0.0",
    "black>=23.0.0"
]

Install with:
uv sync --group dev

Choose the first approach for better tool compatibility.

⸻

7. Importing existing requirements.txt

To pull in an old requirements.txt without hand-copying:

# adds each req into pyproject.toml
uv add -r requirements.txt

Or to just install into the virtualenv without modifying TOML:

uv pip install -r requirements.txt

⸻

8. Locking & installing
	1.	Lock your graph:

uv lock

→ produces uv.lock, capturing exact versions & sources.

	2.	Sync environment from lockfile:

uv sync

→ creates/updates .venv, installs locked packages.

⸻

9. Virtual environments & Python versions

	•	Create a venv:
uv venv

	•	Activate it:
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows

	•	Pin interpreter:
uv python pin 3.11

creates .python-version for consistent teamwide versions.

⸻

10. CI/CD integration

Replace your old steps:

steps:
  - run: pip install uv          # or install via script
  - run: uv sync --ci           # install deps non-interactively
  - run: uv run pytest          # run tests in the venv

You can also export back to a requirements.txt for legacy tooling:

uv pip compile pyproject.toml -o requirements.txt

⸻

11. Migrating workflow
	1.	Audit your requirements*.txt.
	2.	Run uv init in each project root.
	3.	Import old deps via uv add -r.
	4.	Remove requirements*.txt, switch all CI/dev scripts to uv sync and uv run.
	5.	Commit pyproject.toml + uv.lock.

⸻

That's it—no more manual requirements.txt drudgery. You get a unified, blazing-fast workflow, standardized metadata, and bullet-proof reproducibility.
