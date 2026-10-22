# Release audit — 2.0.0

This is a maintenance review and regression record, not an independent penetration test or a promise that the software is vulnerability-free.

## Findings addressed

| Finding in v1 | Change in v2 |
| --- | --- |
| Synchronous event, RSS, article, and AI calls froze the UI | Qt background jobs; explicit busy/error states and obsolete-result protection |
| Network failures could be cached as a day with no events | Only a validated successful provider response is cached |
| Together API token was persisted in plaintext settings | Environment-only configuration, per-request consent, explicit v1-key removal action |
| Article retrieval and broad legacy dependencies increased network/parser surface | Removed newspaper3k, lxml, BeautifulSoup, requests, OpenAI SDK, deprecated hijri-converter; narrow runtime dependencies |
| Feed URLs and article links lacked a clear trust boundary | HTTPS-only validation, public-IP pinning, redirect validation, no authenticated redirects, bounded bodies |
| Untrusted parser input could be interpreted as a file path | Feedparser receives only an in-memory byte stream |
| Rich text could load external or local image resources | Private document resource loader and plain-text news/AI display |
| Closing/deleting the last note could discard text without warning | Explicit delete confirmation, persistent note list, final save, visible save failure |
| Cache paths were tied to source/frozen application directories | OS app-data directory and an explicit isolated-workspace option |
| Duplicate UI functions, missing icon resources, obscure context-menu-only navigation | Modular tabs, visible controls, packaged fonts/icons, two blue themes and bilingual layout |
| No automated checks or clear release/dependency policy | Regression suite, lint/format checks, pinned runtime hashes, vulnerability audit, secret scanning, portable release build |

## Review coverage

- All original reachable branches and the v1 tag were inspected. The repository had only `main`; no redundant remote branch was present.
- Gitleaks 8.30.1 was run against reachable Git history with redacted output. It found no credential matches in the original history. This does not prove no unknown or non-pattern secret ever existed.
- Personal author/committer email metadata is replaced with the project's GitHub noreply identity during release preparation. Development commits and the old version tag are retained. Historical generated event-cache files are removed; user notes and settings are excluded from tracking.
- Automated tests cover known date conversions, leap boundaries, month grid weekdays, schema rejection, atomic-save failure, backups, URL schemes, private/mixed DNS, pinned TLS hostnames, redirect leakage, body limits, parser local-path isolation, UI note retention, language/theme changes, stale feed responses, event failures, and midnight rollover.
- Real Qt screenshots use a synthetic, isolated workspace. Live optional event lookup and a public NASA RSS feed were exercised successfully. AI transport is tested with fakes; no paid or user-key request is performed.
- Runtime advisory scanning uses the exact dependency lock. Scanner results are a point-in-time check and can change as new advisories are published.
- Local verification passed 54 regression tests, lint and format checks, workflow validation, source/wheel builds, and the frozen-app smoke test. The 13 pinned runtime packages had no known advisory matches at review time.
- A frozen-build failure was traced to an incompatible host ICU DLL accidentally discovered through PATH. Release builds now restrict PATH to the interpreter and Windows system directories; the disposable console build passed both version and GUI smoke checks with the conflict removed.

## Remaining limits

Notes and backups are plaintext, release executables are unsigned, and third-party event/Hijri results may differ from authoritative local calendars. Public HTTPS feed servers may still serve misleading content. The external browser has its own URL/network and privacy behavior. DNS/OS waits can exceed the app's body-loop deadline. Windows binaries are built and smoke-tested; Linux source behavior is covered in CI, and macOS packaging is not provided.

History rewriting changes commit IDs. Existing clones should be replaced with a fresh clone to avoid reintroducing old metadata. A force-push cannot erase copies already cloned, cached old commit views, or old operating-system backups; GitHub Support controls server-side cache removal when needed.
