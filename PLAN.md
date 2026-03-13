# Plan

This project implements the Interactive Brokers Web API interface.

## Features

It allows the user to authenticate, retrieve account information, market data and manage orders, positions, and more.

## Tech stack

- Python 3.13
- `Pydantic` for all the data models, prefer to use Pydantic models and avoid plain dictionaries or Python's data classes.
- `pydantic-settings` - for managing configuration and environment variables in a structured way, and reading .env files or system environment variables.
- Typer - for building the command-line interface (CLI) of the application.
- `uv` - for managing the Python project, and `uv` workspaces for structing the repository.
- `typing` - The project is completely type-annotated for better code quality and maintainability.
- `ruff` - for linting and code formatting. (with ruff check --fix and ruff format)
- `ty` - LSP and type checking.
- mise: used for task management and orchestration.
- use `pytest` for testing - unit tests for code that doesn't require mocking and integration tests for code that interracts with my IB account (note to keep the scope of integrationtests limited to smoke tests to check everything wroks, dont assert on actual values like balance or number of positions, that might be changing between runs since it hits the real account)
- for logging, use `structlog` - create a `logger.py` module and include all logging configurations there, allow logging in plaintext and JSON, allow coloring in plaintext mode (tho can be configurable if CI=true), include timestamp, log level, message, check if CI=true when configuring the logger to disable coloring.

Note about `uv`:

Use `uv` workspaces, make the top package a CLI with Typer and the inner package the actual API client.
This way, we can keep the the applicative part (the CLI) separate from the core logic (the API client), which promotes better organization and maintainability.

## Scaffolding

When scaffolding the project, use CLI commands to create the project structure, proper use of `uv init` is needed - see references below for docs.

## Agents

Opencode and AI agents are first-class citizens in this project.

Implement `AGENTS.md` and keep it maintained with the project's details, keep it concise, useful and up-to-date.

## Auth

The auth part is the hardest. IB requires downloading and installing a local gateway application, and to authenticate with username and password, it involves 2FA, we need to see how we automate much of the process as possible, and how to handle the 2FA part.

I don't mind stepping in and having some human intervention, but we should strive to keep it to a minimum, and to automate as much of the process as possible.

First, let's make it work because we've had issues before with this type of authentication IB uses.

Read the IB Web API docs carefully and download the gateway, configure it, and use Playwright to automate the login process, credentials will be provided in the configuration through environment varibales.

## Project Docs

We will write a proper README.md with pre-requisites, installation instructions, usage examples.

## References

- <https://ibkrcampus.com/campus/ibkr-api-page/cpapi-v1/#api-req>
- <https://docs.astral.sh/uv/concepts/projects/workspaces/#getting-started>
- <https://github.com/mjpieters/aiolimiter>
- <https://github.com/hynek/stamina>
- <https://github.com/orshemtov/ib/tree/main/packages/ib-client>
- <https://docs.github.com/en/copilot/how-tos/copilot-cli/automate-copilot-cli/automate-with-actions>
