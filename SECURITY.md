# Security policy

The latest 2.x release is the maintained line. Version 1 is unsupported; it stored optional AI keys in plaintext local settings. Upgrade, remove the old setting through v2 Settings, and rotate any previously used key.

Report suspected vulnerabilities through [GitHub's private vulnerability reporting](https://github.com/maboox/ShamsiCal/security/advisories/new). If that entry point is unavailable, open an issue requesting a private reporting channel **without publishing exploit details, credentials, private notes, or backups**. Maintainers will assess reports as availability permits; no response-time SLA is promised.

Include the app version, OS, minimal synthetic reproduction, expected behavior, and impact. Do not attach your real `workspace.json`, settings, API key, or a token-bearing URL. A placeholder feed or fake data is preferred.

For credential exposure, revoke/rotate the credential first. Removing a file or rewriting Git history cannot invalidate an already copied secret. See [privacy behavior](docs/PRIVACY.md) and [release audit](docs/AUDIT.md) for the intended boundaries and known limits.

Runtime dependencies are pinned with hashes in `requirements.lock`; CI checks advisory data and scans history for common secret patterns. Updates must refresh the lock, pass regression tests, and be reviewed before release.
