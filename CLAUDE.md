# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains **gherkins**, a Python library under active development for deployment automation. The library provides a framework to manage deployment stages and execute commands both locally and on remote servers via SSH.

**Important**: The `gherkins/` package is the core library being developed. The `example.py` file serves as an annotated demo/example script illustrating how to use the library, not as production deployment code.

## Architecture

### Core Components

**StageManager** (`gherkins/StageManager.py`):
- Provides a decorator-based pipeline for defining and executing deployment stages sequentially
- Stages are registered using `@sm.stage()` decorator and executed in order via `sm.run()`
- Stage names can be customized or default to the function name

**Serloc** (`gherkins/Serloc.py`):
- `local_exec(exec_str)`: Executes shell commands locally via subprocess
- `ServerConnection`: SSH client wrapper using paramiko for remote server operations
  - `exec(exec_str)`: Runs commands on remote server and displays output/errors
  - `scp(local_path, remote_path)`: Copies files/directories to remote server
- Uses colorama for colored terminal output

### Typical Usage Pattern

1. Instantiate `StageManager` at the top of the deployment script
2. Define deployment stages as functions decorated with `@sm.stage()`
3. Within each stage, use `Serloc.local_exec()` for local commands or `ServerConnection` methods for remote operations
4. Call `sm.run()` to execute all stages in sequence

## Development Context

The **gherkins** library is under active development by the repository owner. Key points:

- **Library Code**: The `gherkins/` directory contains the reusable library components (`StageManager.py`, `Serloc.py`, etc.)
- **Example File**: `example.py` is an annotated demo script illustrating a full deployment pipeline using the library
- **Design Goal**: The library is designed to be importable and used in other projects for deployment automation
- **Development Workflow**: When modifying library code in `gherkins/`, test changes by running `python example.py` (with valid credentials) or `pytest tests/`

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix

# Install dependencies
pip install -r gherkins/requirements.txt
```

### Testing Library Changes
```bash
# Run unit tests
pytest tests/

# Run the example script (requires valid server credentials substituted in example.py)
python example.py
```

## Key Dependencies

- **paramiko**: SSH client for remote server connections
- **scp**: File transfer over SSH
- **colorama**: Terminal color output (cross-platform)
- **invoke**: Task execution library (installed but not currently used in the codebase)
