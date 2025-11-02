# meteo

> Project generated with Sicarator

## Project requirements

### Astral/uv

- Install [uv](https://github.com/astral-sh/uv) to manage your Python version, virtual environments, dependencies and
tooling configs: see [installation docs](https://github.com/astral-sh/uv?tab=readme-ov-file#installation).


## Installation

### Python virtual environment and dependencies

Run the following command:

```bash
uv sync
```

or else:

```bash
make install
```


### Install git hooks (running before commit and push commands)

```bash
uv run pre-commit install
```


## Testing

To run unit tests, run `pytest` with:

```bash
uv run pytest tests --cov src
```

or

```bash
make test
```

## Formatting and static analysis

### Code formatting with `ruff`

To check code formatting, run `ruff format` with:

```bash
uv run ruff format --check .
```

or

```bash
make format-check
```

You can also [integrate it to your IDE](https://docs.astral.sh/ruff/integrations/) to reformat
your code each time you save a file.

### Static analysis with `ruff`

To run static analysis, run `ruff` with:

```bash
uv run ruff check src tests
```

or

```bash
make lint-check
```

To run static analysis and to apply auto-fixes, run `ruff` with:

```bash
make lint-fix
```

### Type checking with `mypy`

To type check your code, run `mypy` with:

```bash
uv run mypy src --explicit-package-bases --namespace-packages
```

or

```bash
make type-check
```

