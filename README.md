# automations

Personal project scaffolding and automation scripts.

## Structure

```
init/          # uv run-able PEP 723 init scripts
parts/         # shared library (automations-parts local package)
templates/     # static config templates (if needed)
```

## Usage

```bash
uv run init/python_lib.py my-project
uv run init/python_lib.py my-project --no-github
uv run init/hugo.py
```

## Requirements

- [uv](https://docs.astral.sh/uv/)
- [gh](https://cli.github.com/) (for GitHub integration)
- [hugo](https://gohugo.io/) (for Hugo scaffolding)
