# Changelog

## 2.1.0 — 2026-10-25

- Restored the original desktop-widget workflow: independent frameless calendar, quote, notes, and RSS windows.
- Added per-widget dragging, resizing, persisted positions/visibility, tray recovery, transparent backgrounds, opacity, and optional always-on-top.
- Kept the daily calendar small; the month grid is an optional separate widget and settings is a separate dialog.
- Preserved existing 2.0 notes/feeds/backups and added an explicit v1 widget-layout importer.
- Retained the network, API-key, storage, dependency, and privacy safeguards from 2.0.
- Added regression coverage for independent desktop behavior and replaced screenshots/documentation accordingly.

## 2.0.0 — 2026-10-22

- Rebuilt the desktop UI with a Saturday-first Jalali month grid, Gregorian day labels, selected-day details, visible date navigation, and compact view.
- Added bilingual Persian/English layouts, ocean/daylight blue themes, bundled Vazirmatn, and Phosphor icons through QtAwesome.
- Reworked notes with confirmed deletion, checklists, debounce autosave, atomic JSON persistence, previous-save backups, import/export, and a v1 note importer.
- Moved online work off the UI thread; prevented stale feed results and invalid event-error caching.
- Constrained network traffic to bounded, certificate-verified public HTTPS requests with address pinning and redirect checks.
- Removed plaintext API-key persistence; retained optional Persian AI summaries through environment configuration and explicit per-request consent.
- Removed legacy article scraping and deprecated/broad dependencies; added pinned runtime hashes, regression tests, CI, security policy, privacy documentation, and portable Windows builds.
- Version 2 consolidates independent v1 widgets into tabs. Legacy widget positions, arbitrary theme palettes, and per-widget size settings are not migrated; notes can be imported explicitly.

## 1.0.0 — 2025-06-29

Original floating calendar, notes, RSS, and quote widgets. This version is no longer maintained.
