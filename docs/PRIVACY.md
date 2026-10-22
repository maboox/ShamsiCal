# Privacy and network behavior

ShamsiCal does not collect telemetry, display ads, require an account, run an updater, or expose a local server. Calendar conversion, notes, themes, and quotes work offline.

| Operation | Destination | Data sent | Trigger |
| --- | --- | --- | --- |
| Event lookup | `pnldev.com` | Selected Jalali date, IP, generic app User-Agent | Opt-in in Settings; uncached selected dates or explicit refresh |
| RSS/Atom refresh | The feed host you entered and its validated redirects | IP, feed URL path/query, generic app User-Agent | Explicit Refresh only |
| AI summary | `api.together.xyz` | Configured model, API authorization, selected title and excerpt, fixed prompt | Explicit confirmation for each request |
| Open article | Your default browser | Subject to browser and destination policies | Explicit Read in browser |

No notes or backups are included in these requests. RSS queries can contain private identifiers; avoid credential-bearing URLs. The app rejects username/password URL syntax but cannot infer whether a query parameter is a secret. URLs are stored locally and included in your own exported backups.

## Local data

`workspace.json` contains your notes, feed addresses, preferences, and up to 400 cached event days. Previous-save and exported backups contain the same kinds of data. These files are **not encrypted**. Use OS account protection, disk encryption, and a safe backup location. Deleting a note does not promise secure erasure from disk, the rolling backup, or OS snapshots.

News articles are kept in memory only. AI keys are read from `TOGETHER_API_KEY` at request time and are never intentionally written to settings, logs, exports, or cache. The optional model is read from `SHAMSICAL_AI_MODEL`. The app does not print provider exceptions or token-bearing request details. OS crash dumps and sufficiently privileged local processes are outside this protection.

The v1 importer reads only note titles and HTML from the old settings. A separate explicit action removes `togetherai/api_token` from v1 settings; rotation at Together remains necessary for a previously exposed key. It does not scrub old device backups.

## Transport and rendering

Requests use certificate-verified HTTPS on port 443, reject local/private resolved addresses, pin the connection to the checked public IP while validating the original TLS hostname, and revalidate each redirect. Authenticated requests never follow redirects. Proxy environment variables, browser cookies, and OS credentials are not forwarded.

Responses are limited to 2 MiB, redirects to three hops, socket connect/read waits to five seconds each, and the body loop has a 25-second deadline. OS DNS resolution and blocking system calls can add delay. Work runs outside the GUI thread; close waits for active requests to complete.

Feed input is parsed from an in-memory stream, never interpreted as a filename or URL by the parser. News and AI output are rendered as plain text. Imported note HTML may retain formatting, but document resource loading is disabled for both local and remote images; external paste is plain text.

These controls reduce specific risks; they are not a guarantee that no vulnerability exists. Third-party servers control availability, accuracy, pricing, and their own retention policies. Opening an article hands control to your browser, which has different network and privacy behavior.
