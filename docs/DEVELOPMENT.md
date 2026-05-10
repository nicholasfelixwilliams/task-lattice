# Development Guidelines

## Dev Environment

To develop locally, you have 2 choices:
 - Dev Container (recommended)
 - Local uv virtual environment

Dev container setup is included for VSCode. 

To configure local environment:

```sh
uv sync --dev
```

## Code Linting

Linting Framework: ruff

To run code linting:

```sh
uv run ruff format .
uv run ruff check .
```

Formating is required and enforced via CI. 

## Testing 

Testing Framework: pytest

To run unit tests:

```sh
uv run pytest tests --cov=src --cov-report=term-missing
```

100% code coverage is required (enforced via CI). 