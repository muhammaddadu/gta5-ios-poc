# GTA V local proof of concept

Only original scripts, documentation and synthetic test fixtures belong in this Git repository.
Keep all upstream checkouts, game inputs, translated engine code, shader files, builds,
IPAs, logs, screenshots, save games and signing configuration under ignored `.local/`.
The owner authorised local acquisition for this POC. Keep third-party game archives
and all derivatives private under `.local/`; never commit or redistribute them.
Never claim gameplay from a server test, support page, successful compile or
community demonstration.

Run `python3 -m unittest discover -s tests -v` and `python3 scripts/audit_git.py`
before committing. Stage explicit paths, never force-add ignored files. Do not push.
Use CodeGraph first if a `.codegraph/` directory exists; do not create an index.
