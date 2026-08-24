# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

`arxiv-browse` is the Flask app behind arxiv.org's public reading paths: `/abs`, `/list`,
`/pdf`, `/src`, `/html`, `/format`, `/year`, `/tb`, `/stats`, plus a pile of legacy redirects.
It is read-only with respect to the arXiv corpus. The workspace-level `CLAUDE.md` (one
directory up, via `arxiv-developer/workspace/`) covers cross-repo conventions; this file
covers browse.

## Commands

Toolchain is **`uv`** with Python 3.11 (`~=3.11.0`). There is no `pipenv`/`poetry` here
despite the stale `poetry.lock.bak`.

```bash
uv sync                                  # create/refresh .venv from uv.lock
uv run python main.py                    # dev server on :8080, debug + template autoreload
uv run pytest tests                      # full suite
uv run pytest tests/test_abs.py -q       # one file
uv run pytest tests/test_abs.py::test_encrypted_source_db  # one test
uv run pytest tests --cov=browse --cov-fail-under=80      # what CI runs
uv run pytest tests --runintegration     # also run @pytest.mark.integration (needs GCP creds)
uv run ruff check browse                 # the lint gate CI enforces
uv run mypy browse                       # config in mypy.ini; not enforced by CI
```

`make run` / `make test` wrap the above. `make docker` + `make docker.run` build and run the
production image; `make proxy` / `make dev-proxy` start cloud-sql-proxy against
prod/dev Cloud SQL.

CI (`.github/workflows/python-app.yml`, on PRs to `develop`) gates on exactly two things:
`pytest --cov=browse --cov-fail-under=80 tests` and `ruff check browse`. Coverage is a
real gate — dropping below 80% fails the PR.

Flask CLI commands (registered as blueprints in the factory):

```bash
uv run flask --app app:app invalidate invalidate-mailings 250130 --dry-run  # purge a mailing's PDFs
uv run flask --app app:app check paper_formats 2501
```

### Dev data modes

`uv run python main.py` with no `.env` uses the checked-in filesystem test data under
`tests/data/` — enough for `/abs/0906.5132` and PDFs, but **listings do not work**. For real
data you need a `.env` with `CLASSIC_DB_URI`/`LATEXML_DB_URI` pointing at cloud-sql-proxy
ports and `gs://` storage prefixes; the README has the full `gcloud secrets` recipe. The
practical tell that you are still on test data is a 404 on a paper you know exists.

## Architecture

### Request path

`browse/routes/` → `browse/controllers/` → `browse/services/` → arxiv-base.

- **routes** are thin Flask blueprints. They own URL shapes, surrogate keys, and picking the
  template; they should not contain business logic. Five blueprints:
  `ui` (all the HTML pages), `dissemination` (`/pdf`, `/ps`, `/html`, `/format`),
  `src` (`/src`, `/e-print`, ancillary files), `redirects`, `unimplemented`.
- **controllers** return the `Response` triple `(data_dict, status, headers)` — see
  `browse/controllers/__init__.py`. The route renders the template with `**data`. This is why
  controllers are testable without a request context and why headers are assembled in the
  controller, not the template.
- **services** talk to the DB, GCS buckets, and the legacy filesystem.

### Pluggable abs/listing backends

The two big data sources are swappable via config, because browse runs against both the
legacy filesystem and the database:

- `DOCUMENT_ABSTRACT_SERVICE` — `browse.services.documents.fs_docs` (parses `.abs` files) or
  `db_docs` (queries `arXiv_metadata`).
- `DOCUMENT_LISTING_SERVICE` — `browse.services.listing.fs_listing`, `db_listing`, or `fake`.

Both are pydantic `PyObject` fields: the config value is a dotted path to a **factory
function**, resolved at import and called per app context. `get_doc_service()` /
`get_listing_service()` memoize the result on Flask `g`. When you add a method, add it to the
`ListingService` ABC (`browse/services/listing/__init__.py`) and to *all* implementations —
including `fake_listings.py`, which is 1200 lines of hand-built fixtures and is easy to forget.

`get_article_store()` is different and deliberately so: `ArticleStore` is a **module-level
global**, not app-context bound, so the GCS `storage.Client` is reused across requests. Tests
that change storage config must reset it — that is what the `reset_packages` fixture does.

### Domain model lives in arxiv-base, not here

`DocMetadata`, `VersionEntry`, `Identifier`, `FileObj`/`ObjectStore`, `fileformat`,
`key_patterns`, the taxonomy (`ARCHIVES`, `CATEGORIES`, `GROUPS`), the SQLAlchemy models
(`arxiv.db.models`), and the header/footer templates (`base/header.html`, `base/footer.html`)
all come from **arxiv-base**. Before writing a helper here, check whether `arxiv.*` already
has it. Several empty directories (`browse/domain/`, `browse/services/object_store/`,
`browse/services/util/`, `browse/services/search/`, `browse/services/prevnext/`,
`browse/services/document/`) are untracked `__pycache__` leftovers from that migration —
ignore them, don't add to them.

arxiv-base is pinned in `pyproject.toml` as a **git dependency on `master`**, with
`exclude-newer-package = { arxiv-base = "1 minute" }`. So `uv lock` re-pins to whatever
master is at that moment. A browse change that depends on a new arxiv-base commit needs the
lock bump committed alongside it, as its own step (see commit `02b75d13` for the pattern).

### Dissemination (PDF/source serving)

`ArticleStore.dissemination()` resolves a `(format, id, version)` request to a `FileObj`, or
to a typed **condition** rather than an exception — `"WITHDRAWN"`, `"NO_SOURCE"`,
`"UNAVAILABLE"`, `"NOT_PDF"`, `Deleted(msg)`, `KnownReason(msg, fmt)`. The `Union` is
intentional (`browse/services/dissemination/article_store.py`): these are type-checked
outcomes, and each maps to a specific user-facing page in `browse/controllers/files/`.
`KnownReason` comes from `reasons.json` in the storage bucket, read once when the store is
first built.

Responses honor `Range` requests and force `Transfer-Encoding: chunked` — both are hard
requirements of the Fastly/Cloud Run pair for objects over 20MB, not stylistic choices.

### Caching and Fastly surrogate keys — read before touching a route

Browse is fronted by Fastly, and correctness of the cache headers is a production concern with
outage history. Response-producing routes tag themselves with surrogate keys via
`b_add_surrogate_key(headers, [...])` (`browse/__init__.py`, wrapping
`arxiv.integration.fastly.headers`). Keys follow established shapes — `abs-{id}`,
`paper-id-{id}`, `paper-id-{id}-current`, `src-{idv}`, `list-new-{ctx}`, `announce` — and the
announce/publish pipeline purges by those exact strings. **A new route without the right keys
is unpurgeable; a wrong key gets purged by the wrong event.** Match the neighbors.

Two comments in `browse/config.py` (`LISTING_EMPTY_MAX_AGE`, `LISTING_STALE_IF_ERROR`) and the
tail of `browse/controllers/list_page/__init__.py` document why listings return **503** on a
count/items contradiction instead of an empty page: read-replica lag during announcement once
froze a 2-minute blip into a 10-hour outage via a long-cached empty listing. `stale-if-error`
is what makes the 503 safe. Preserve that logic.

### Config

`browse/config.py` `Settings` extends `arxiv.config.Settings` (pydantic). Every field is
overridable by environment variable, and `create_web_app(**kwargs)` overrides take precedence
— that is how the test fixtures build differently-wired apps. Note `TESTING: bool = True` is
the *default*; deployments set it false. `Settings.check()` fixes up sqlite pooling and flips
`FS_TZ` to UTC when `ABS_PATH_ROOT` is a `gs://` path (filesystem timestamps are US/Eastern on
the Cornell VMs, UTC in the buckets — a source of off-by-hours bugs).

## Tests

Fixtures in `tests/conftest.py` build one app per wiring; pick by which backend you are
exercising:

| Fixture | abs from | listings from |
| --- | --- | --- |
| `dbclient` / `client_with_db_listings` | DB | DB |
| `client_with_test_fs` | `.abs` files | listing files |
| `client_with_fake_listings` | `.abs` files | `fake_listings.py` |

Each is a Flask test client already inside an app context. The DB is sqlite, built fresh per
session from `tests/data/db/sql/*.sql` and copied per test function, so tests may mutate it.
`populate_test_database` refuses to run if `arXiv_metadata` has >1M rows — a guardrail against
pointing the fixtures at a real database.

Test data layout under `tests/data/abs_files/` mirrors production storage: `ftp/` (current
version), `orig/` (superseded versions), `ps_cache/` (built PDFs). To add a paper, pull its
real objects with `uv run python script/get_test_article.py <id> ./tests/data/abs_files <bucket>`
rather than hand-crafting `.abs` files.

`tests/legacy_comparison/` diffs rendered pages against the legacy Perl site; it is a manual
tool, not part of the suite.

## Conventions

- PRs target **`develop`**. Commit subjects are prefixed with the Jira key —
  `ARXIVCE-4313: dual arXiv/Cornell copyright attribution`.
- Static assets are cache-busted with a manual `?v=YYYYMMDD` query in `templates/base.html`.
  Changing a CSS/JS file without bumping its `v` means users keep the old one.
- `DECISIONS.md` records user-visible display decisions (e.g. proxy-name formatting) and their
  rationale. Add to it when a change encodes a judgment call about what readers see.
- `.pylintrc` and `tests/lint.sh`/`docstyle.sh` are Travis-era leftovers; ruff is the live
  linter.

## Note

`~/.codex/config.toml` and `~/.gemini/settings.json` exist on this machine. Reply `/import`
to see what is importable from them (MCP servers, slash commands, subagents, skills,
instructions), then `/import --yes=<digest>` to apply.
