## Install

Install the package and development dependencies:

```
uv sync
```

## Test

```
uv run pytest
```

pandas is optional. To run the tests without it:

```
uv run --isolated --no-dev --with pytest pytest
```

## Lint

```
uvx ruff check
uvx ruff format
```
