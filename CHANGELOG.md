# Changelog

All notable changes to gherkins will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2026-02-21

### Added

- **StageManager**: decorator-based pipeline for defining and executing named deployment stages sequentially; supports running all stages or a named subset
- **local_exec**: execute multi-line shell commands in a persistent local shell session (cmd.exe / bash), preserving state (cd, env vars) across commands
- **ServerConnection**: SSH client wrapper using paramiko and paramiko-expect for interactive remote command execution with persistent shell state
- **ServerConnection.scp**: recursive SCP file/directory transfer to remote server
- **ServerConnection context manager**: `with ServerConnection(...) as s:` syntax for automatic session cleanup
- `pyproject.toml` packaging metadata (setuptools, Python ≥ 3.9)
- MIT license
- README with quick-start, API reference, and project structure overview
- Unit tests for StageManager (`tests/test_stage_manager.py`)
- GitHub Actions CI workflow (Python 3.9, 3.11, 3.12; pytest + ruff)
