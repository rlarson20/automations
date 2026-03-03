**Summary**

Built an `automations` repo for zero-friction project scaffolding, modeled on Simon Willison's uv + PEP 723 philosophy. All scripts are `uv run`-able with inline metadata; shared logic lives in a proper local package (`automations-parts`) referenced via `[tool.uv.sources]`.

**Structure**

```
automations/
  init/
    hugo.py          # interactive Hugo site scaffolder
    python_lib.py    # uv --lib + PEP 735 dep groups + ruff/mypy/pytest
    python_script.py # standalone PEP 723 script scaffold
    notebook.py      # jupyter or marimo, --flavor flag, venv-scoped kernel
    generic.py       # language-agnostic base for exotic stacks
    js.py            # vite/next/astro/vanilla-ts, bun default, --serious flag
  parts/
    src/automations_parts/
      git.py         # git_init, write_gitignore, initial_commit
      github.py      # create_repo via gh CLI
      precommit.py   # write_config (generic + stack hooks), install via uvx
      run.py         # subprocess wrapper
      toml_utils.py  # read/patch/write pyproject.toml, set_dependency_groups
    pyproject.toml   # automations-parts, deps: rich, tomli-w
    uv.lock
  README.md
```

**Key design decisions**

- PEP 723 inline metadata on all `init/` scripts — `uv run init/python_lib.py my-project` with no setup
- `automations-parts` as a path dep, src layout, no workspace — clean imports via `from automations_parts import git, ...`
- pre-commit via `uvx` — no install required beyond uv
- `--no-github`, `--no-commit`, `--no-launch` escape hatches throughout
- `--flavor` pattern for multi-mode scripts (notebook: jupyter/marimo, js: vite/next/astro/vanilla-ts)
- `--serious` on js.py layers ESLint + Prettier + strict tsconfig

---

**Next steps**

1. Build `readme.py` in `parts/src/automations_parts/` — shared README renderer to stop drift across scripts
2. Build `init/rust.py` — `cargo init` + clippy/fmt pre-commit + gh
3. Refactor all init scripts to use `readme.py` instead of hand-rolled README stubs
4. Add pre-commit + a `pyproject.toml` with ruff/mypy to the `automations` repo itself (ironic it lacks what it provisions)
5. `cleanup/remove_kernel.py` — prune stale Jupyter kernels from `~/.local/share/jupyter/kernels/`
6. `update.py` — bump pre-commit hook revs across all configs (lower priority, useful at 10+ projects)
