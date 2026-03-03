# automations

Personal project scaffolding and automation scripts.

## Claude Convos

This was made almost entirely through conversing with Claude in the web UI or through Z.ai in the CLI.
Here are the links to the conversations I had:

https://claude.ai/share/643ab4cf-c18a-4d30-b11c-2b1857d633ee
https://claude.ai/share/5f739d49-c992-4323-9968-bfc4fc28203e

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
