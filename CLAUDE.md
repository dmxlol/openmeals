# Openmeals API

@README.md

## Import rules
- `core` must not import from `modules` or `services`
- `libs` must not import from `modules` or `services`
- `services` can import from `core`, `libs`, and `modules`
- Within a package:
  - `schemes` → only `core`
  - `models` → only `schemes`
  - `projections` → nothing (or only `schemes`)
  - `dto` → `models`, `schemes`
  - `dependencies` → `models`, `schemes`, `dto`, other `dependencies`; never `handlers`
  - `handlers` → anything


## Conventions
- Python 3.11+ modern typing: `list[str]`, `int | None`, `X | Y`
- `import typing as t` — use `t.Annotated`, `t.TYPE_CHECKING`, etc.
- Use type hints on all function signatures
- Prefer composition to inheritance
- Raise exceptions from `lib.exceptions` (`NotFoundException`, `ValidationException`, etc.)
- Run `make format` and `make lint` (ruff) before committing
- Run `make test` to execute unit tests

## Git flow
- Use github flow (feature-branch → master)
- Semantic commit messages: `tag(context): summary`
  - `fix`/`feat` for changes that require a new version; other tags for the rest
- No `Co-authored-by` headers
- Summary only; add a description body only for breaking changes

## FastAPI-specific rules
- Always use `Depends(some_function)`, never bare `Depends()` with a Pydantic model — that treats the model as a request body
- On GET endpoints, annotate non-path parameters explicitly with `Query(...)` — do not rely on implicit resolution
- Route handlers should be thin: resolve dependencies, call a service/manager, return response
- Use `BackgroundTasks` for fire-and-forget DB updates after the response is built

## Forbidden patterns
- `print()` for logging — use the injected `request.logger`
- private variables/functions in module (.e.g _var = foo  then def foo(): print(_var))
- `@property` for heavy computation or I/O — use `@cached_property` or an explicit async method
- Bare `except:` or `except Exception:` without re-raising
- Mutable default arguments
- Hardcoded secrets or magic values — use `core/config.py` settings
- `import *` except in `__init__.py` re-exports
- imports anywhere but at the beginning of file
- Passing `doc.id` (ObjectId) to a Beanie `Link` field — pass the full document object so the link resolves correctly
