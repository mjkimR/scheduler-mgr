# Print available commands
default:
    @just --list

# Run ruff format and lint
lint:
    uv run ruff format
    uv run ruff check --fix

# Install pre-commit hooks
hooks-install:
    uv run pre-commit install

# Run pre-commit hooks against all files
hooks-run:
    uv run pre-commit run --all-files