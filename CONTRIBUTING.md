# Contributing

Use synthetic data in issues, tests, and screenshots. Never commit notes, workspace files, API keys, local settings, binaries, or personal backup exports.

## Development

Use Python 3.11+ and a new virtual environment. Install the tested runtime and tooling, then the project without resolving dependencies again:

```console
python -m pip install --require-hashes -r requirements.lock
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps --no-build-isolation -e .
python -m shamsical --data-dir ./artifacts/dev-workspace
```

On Ubuntu, Qt may need `libegl1`, `libgl1`, `libxkbcommon0`, `libxcb-cursor0`, and `libdbus-1-3`. CI uses Qt's offscreen platform. Windows is the packaged release target; macOS can run source where compatible Qt wheels exist but has no packaged release or CI coverage.

```console
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m pip_audit --disable-pip --no-deps -r requirements.lock
python -m shamsical --smoke-test
```

For headless smoke tests set `QT_QPA_PLATFORM=offscreen`. Tests do not use live servers or paid AI. `tools/check_providers.py` is an explicit manual online check, outside the test suite.

## Changes

Keep date logic free of Qt and network side effects. Worker code returns values; the main thread owns widgets and persisted state. Translate new UI copy in `i18n.py`, use shared design tokens, and test both layout directions. Preserve note data on navigation, settings changes, import, and save failures.

Dependency changes belong in `pyproject.toml`. After installing the candidate versions in an isolated environment, run `tools/lock_dependencies.py` (requires curl), inspect the exact changes, audit, and test. Hashes come from the official PyPI release metadata. Do not turn off certificate checks or private-address protections to fix a feed.

## Windows release

Run `python build_exe.py` on Windows after all checks pass. It builds a directory-based portable app, collects licenses, and produces a versioned ZIP plus SHA-256 companion in `dist/`. It never bundles workspace data or automatically installs dependencies. Run `python tools/verify_release.py dist/ShamsiCal-2.0.0-windows-x64.zip` to verify the checksum, package contents, and extracted app startup using a temporary workspace. Keep the source archive for the exact tag available alongside the binary under GPL-3.0-or-later.

Update the package version, `tools/windows_version.txt`, changelog, README download filename, and release notes together. Build automation uploads artifacts for review; only a maintainer publishes a GitHub release. Do not claim the binaries are signed or bit-for-bit reproducible.
