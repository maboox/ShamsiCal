# ShamsiCal user guide

[فارسی](../README.fa.md) · [Home](../README.md)

## Desktop widgets

The app starts as independent frameless desktop widgets, with calendar and quotes visible by default. Notes and RSS can be shown from the calendar shortcuts, any widget menu, or the tray icon. Drag the header to move one widget; its lower-corner grip resizes it. Position, size, and visibility are saved separately. Hiding the calendar does not hide other widgets. Settings is a separate dialog, not the main app. The tray icon can restore a hidden calendar; without a tray the app keeps a recoverable widget visible. Quit closes the suite after saving.

Settings offers blue themes, optional transparent backgrounds, opacity, and always-on-top. On a disconnected monitor, saved positions are clamped back into the available desktop. Reset widget positions recovers the default arrangement.

## Calendar

Choose a day in the Saturday-first month grid. The larger number is Jalali; the smaller number is Gregorian. Friday is colored distinctly, but this is **not** an authoritative holiday calendar. Month arrows clamp the selected day to the destination month's length. Day buttons, Today, and Go to date support daily navigation. Date entry accepts Persian, Arabic, and Western decimal digits, with `/` or `-` separators.

Dates from Jalali 1200 to 1600 are browsable. Hijri conversion has a smaller library-defined range; outside it the UI shows an unavailable message instead of crashing. Hijri uses Umm al-Qura and can differ from local observations. At midnight the view follows today only when you were already viewing today; browsing another day is preserved.

The small daily widget is the default. Its month button opens a separate optional month widget. Compact view hides secondary daily details without affecting the other widgets. Use the header to drag, the corner grip to resize, and the widget menu to show/hide, configure, or quit. No dashboard or tabbed main window is created.

## Notes

Create and rename notes in the independent Notes widget. Use Bold, Italic, and Checklist on the current cursor/selection. Checklist toggles the current line between unchecked and checked; Enter continues a list, and Enter on an empty item exits it. External paste is plain text. Images and external rich-text resources are blocked.

Edits autosave after 500 ms of inactivity, when switching notes, and at orderly close. Deletion asks for confirmation and always leaves one usable note. Watch the bottom status bar: if saving fails, keep the app open and export a backup from Settings. Autosave cannot preserve keystrokes lost to abrupt power failure before the timer fires.

## Reader

Add a public HTTPS RSS/Atom feed and click Refresh. Feeds are not fetched automatically at startup, on selection, or on a timer. Article lists are kept in memory rather than persisted to disk. Switching feeds invalidates any late response from the previous feed.

Only standard HTTPS port 443 is accepted. Local/private destinations, URL credentials, alternate schemes, and oversized responses are rejected. Each fetch validates resolved addresses and each redirect before connecting. The app intentionally ignores proxy environment variables and does not pass browser cookies or OS credentials. Networks that require a proxy may not support optional online features.

Read in browser opens an explicitly selected public HTTPS link. Once opened, your browser's cookies, network behavior, and the destination's privacy policy apply. Arbitrary sites and full article text are not fetched by the AI feature.

## Optional AI summaries

Create a Together API key and choose an available chat model through the provider's official dashboard. Set `TOGETHER_API_KEY` and `SHAMSICAL_AI_MODEL` in your process environment **before launching ShamsiCal**. The app has no saved-key field or fixed free-model assumption. Environment secrets are visible to sufficiently privileged local processes; protect your account.

Every AI request asks for confirmation. Only the selected title and the RSS-provided excerpt are sent to Together's HTTPS API, limited to 8,000 characters and a bounded output. Notes, backups, and other articles are never included. Charges and provider retention policies may apply. The result is plain text and may be inaccurate. Missing configuration and service failures have visible UI states. Live paid AI requests are not part of the automated test suite.

## Settings and shortcuts

Settings offers Persian/English, ocean/daylight blue, 9–16 pt text, opt-in online events, editable quotes, and hourly/daily/weekly quote rotation. Save settings applies these preferences. Quote rotation uses fixed time intervals, not a particular local midnight. Online events may run automatically for the selected day **after** you enable the feature; cached days do not trigger another request until Refresh.

| Shortcut | Action |
| --- | --- |
| Ctrl+T | Today |
| Alt+Left / Alt+Right | Previous / next day |
| Ctrl+J | Go to Jalali date |
| Ctrl+N | New note |
| Ctrl+S | Save now |

## Data, backups, and migration

The default directory is chosen by Qt's `AppLocalDataLocation`. On Windows it is normally `%LOCALAPPDATA%\ShamsiCal\ShamsiCal`. Use `python -m shamsical --data-dir PATH` (or the same option on the executable) for an isolated workspace. Only one process can open the same workspace at a time.

- `workspace.json`: local notes, preferences, feed URLs, bounded cached event data, and per-widget layout/visibility. **Not encrypted.**
- `workspace.json.bak`: the previous valid save, replaced after each successful subsequent save.
- `workspace.lock`: prevents concurrent writers; never delete a live lock while another instance is using the data.

Export backup creates a portable JSON copy. Treat it as private. Restore validates the schema and asks before replacing the current workspace. It always resets online-event consent to off. Export your current data before restoring; do not rely only on the rolling `.bak` file.

If a workspace is corrupt, the app refuses to overwrite it. Close all instances, preserve both files, then copy the valid `.bak` file to `workspace.json`, or start with a fresh `--data-dir` and restore an exported backup. The workspace size limit is 16 MiB; export and split large notes if you reach it.

For v1, open Settings → Import v1 notes. The importer reads only the old `MyCompany/ShamsiCalendar` note array and appends distinct notes; it never imports API keys or cached articles. A separate Import v1 widget layout action imports only known position/geometry and visibility fields for the calendar, quotes, reader, and notes. All recovered windows are kept on an available screen. Existing v1 settings remain untouched unless you explicitly use Remove v1 saved API key. Rotate a previously saved key at Together; deleting its local setting does not scrub old OS backups.

## Check a Windows download

Download the ZIP and its `.sha256` companion from the same release. In PowerShell run:

```powershell
Get-FileHash .\ShamsiCal-2.1.0-windows-x64.zip -Algorithm SHA256
```

Compare the value with the checksum file. Extract the whole directory; do not move the EXE away from `_internal`. The executable is unsigned. Download only from the project's release page.
