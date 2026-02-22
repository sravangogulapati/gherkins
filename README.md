# gherkins

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)

A lightweight Python library for defining and running sequential deployment pipelines — locally and over SSH.

---

## Overview

**gherkins** lets you describe your deployment as a series of named stages using a simple decorator API. Each stage is a plain Python function; the library handles ordering, display, and selective execution.

```python
from gherkins.StageManager import StageManager
from gherkins.Serloc import local_exec, ServerConnection

sm     = StageManager()
server = ServerConnection("your.server.ip", "your_username", "./credentials/ssh_key.pem")

@sm.stage("Build")
def build():
    local_exec("docker build -t myapp .")

@sm.stage("Deploy")
def deploy():
    server.scp("./dist", "/opt/app")
    server.exec("systemctl restart myapp")

sm.run()
```

---

## Features

- **Stage pipeline** — define stages as decorated functions; run them all or select a subset by name
- **Local execution** — run shell commands locally with per-command output, preserving shell state across commands
- **Remote SSH execution** — run commands on a remote server via a persistent interactive SSH session (powered by [paramiko](https://www.paramiko.org/))
- **SCP file transfer** — copy files or entire directories to a remote server with a single call
- **Context manager support** — use `ServerConnection` as a context manager for automatic cleanup
- **Rich terminal output** — stage headers and coloured output via [rich](https://github.com/Textualize/rich) and [colorama](https://github.com/tartley/colorama)

---

## Installation

> **Note:** gherkins is not yet published to PyPI. Install by cloning the repo directly.

```bash
git clone https://github.com/<your-username>/gherkins.git
cd gherkins
pip install -r gherkins/requirements.txt
```

Or install as an editable package (requires pip ≥ 21):

```bash
pip install -e .
```

---

## Quick Start

See [`example.py`](example.py) for a complete, annotated deployment script. The example covers:

1. Cloning a git repo locally
2. Clearing old files on the remote server
3. Copying the codebase over SCP
4. Installing Python dependencies in a virtualenv
5. Configuring and restarting NGINX
6. Launching a uvicorn backend process

To try it, copy `example.py`, fill in your server details, and run:

```bash
python example.py                        # run all stages
python example.py "Build" "Deploy"       # run specific stages by name
```

---

## API Reference

### `StageManager`

```python
from gherkins.StageManager import StageManager

sm = StageManager()
```

#### `@sm.stage(stage_name: str)`

Decorator that registers a function as a named deployment stage.

```python
@sm.stage("My Stage")
def my_stage():
    ...
```

#### `sm.run(stages: list[str] | None = None) -> None`

Execute registered stages in order. Pass a list of stage names to run only those stages.
Raises `ValueError` for unknown stage names.

---

### `local_exec(exec_str: str) -> None`

Execute one or more shell commands locally. Commands are split by newline; each is run in a persistent shell session so state (e.g., `cd`, environment variables) is preserved across lines.

```python
from gherkins.Serloc import local_exec

local_exec("""
    cd ./my-project
    git pull
    docker build -t myapp .
""")
```

---

### `ServerConnection`

SSH wrapper around paramiko providing interactive command execution and SCP transfers.

```python
from gherkins.Serloc import ServerConnection

# As a regular object
server = ServerConnection("host", "user", "/path/to/key.pem")
server.exec("sudo systemctl restart myapp")
server.scp("./dist", "/opt/app")
server.close_shell()

# As a context manager (recommended)
with ServerConnection("host", "user", "/path/to/key.pem") as server:
    server.exec("sudo systemctl restart myapp")
```

#### `server.exec(exec_str: str) -> None`

Run one or more commands on the remote server. Output is printed to the console after each command.

#### `server.scp(local_path: str, remote_path: str) -> None`

Copy a file or directory from `local_path` to `remote_path` on the remote server (recursive).

#### `server.close_shell() -> None`

Close the interactive SSH shell session. Called automatically when used as a context manager.

---

## Project Structure

```
gherkins/
├── __init__.py        # Public API exports and version
├── StageManager.py    # Decorator-based pipeline manager
├── Serloc.py          # Local exec + SSH/SCP client
└── requirements.txt   # Library dependencies

example.py             # Annotated demo deployment script
pyproject.toml         # Packaging metadata
```

---

## Development

```bash
# Clone and set up
git clone https://github.com/<your-username>/gherkins.git
cd gherkins
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r gherkins/requirements.txt

# Run tests
pip install pytest
pytest tests/

# Validate the example script (requires valid server credentials)
python example.py
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
