# Changelog

## 1.1.0 — 2026-11-11

### Added
- English language. The whole interface, rank titles, credits and all 197 country names are
  translated. Switch language from the title screen or from Settings. On first launch the game
  follows the system language (Italian on Italian systems, English otherwise).
- Y (Yes) works like S (Sì) to confirm, in both languages.
- If the game crashes, the Windows exe shows a readable message pointing to `errore.log`, and
  the log now includes version, date and system details.
- Tests for translations, for damaged save files, and a headless test that plays complete
  games and draws every screen in both languages.
- GitHub Actions: tests on Windows and Linux, and a release workflow that builds the exe.
- English README (`README.md`) and Italian README (`README.it.md`), with screenshots.
- MIT license for the code (`LICENSE`).

### Fixed
- Crash after returning to the title screen many times: the image cache emptied itself while
  adding an image and then failed to find it.
- Long border lists (Russia, China…) overflowed the bottom of the reveal panel.
- A damaged `classifica.json` or `impostazioni.json` could stop the game at startup. Damaged
  entries are now skipped, and both files are written atomically.
- A leaderboard file with more than 10 entries kept the first 10 instead of the 10 best.

### Changed
- Dependencies are pinned (`requirements.txt` for running, `requirements-build.txt` for the
  exe), and `build.bat` runs the tests before building.

## 1.0 — 2026-11-09

- First version (Italian only).
