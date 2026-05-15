.DEFAULT_GOAL := help

##@ Dev Tools

.PHONY: help
help: ## Print available commands
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Lint / Format

.PHONY: lint
lint: ## Run ruff format and lint
	uv run ruff format
	uv run ruff check --fix

##@ Git Hooks

.PHONY: hooks-install
hooks-install: ## Install pre-commit hooks
	uv run pre-commit install

.PHONY: hooks-run
hooks-run: ## Run pre-commit hooks against all files
	uv run pre-commit run --all-files
