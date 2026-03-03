# Manual checklist

## notebook test: kernel registration

```bash
# kernel registration
uv run init/notebook.py test-nb --no-github
jupyter kernelspec list  # should see test_nb
# open scratch.ipynb, confirm kernel selectable and imports work
```

### results

created the directory, had an error about `VIRTUAL_ENV=.venv` but that was probably because of running it inside the repo.

```
diff --git i/pyproject.toml w/pyproject.toml
index f95d64c..578140b 100644
--- i/pyproject.toml
+++ w/pyproject.toml
@@ -18,6 +18,11 @@ parts = ["rich>=13.0", "tomli-w>=1.0"]
 [tool.uv.sources]
 automations-parts = { path = "parts", editable = true }

+[tool.uv.workspace]
+members = [
+    "test-nb",
+]
+
 [tool.ruff]
 line-length = 100

diff --git i/uv.lock w/uv.lock
index e8d8720..aa8ea26 100644
--- i/uv.lock
+++ w/uv.lock
@@ -1,6 +1,47 @@
 version = 1
 revision = 3
 requires-python = ">=3.12"
+resolution-markers = [
+    "python_full_version >= '3.14' and sys_platform == 'win32'",
+    "python_full_version >= '3.14' and sys_platform == 'emscripten'",
+    "python_full_version >= '3.14' and sys_platform != 'emscripten' and sys_platform != 'win32'",
+    "python_full_version < '3.14' and sys_platform == 'win32'",
+    "python_full_version < '3.14' and sys_platform == 'emscripten'",
+    "python_full_version < '3.14' and sys_platform != 'emscripten' and sys_platform != 'win32'",
+]
+
+[manifest]
+members = [
+    "automations",
+    "test-nb",
+]
+
+[[package]]
+LARGE CHUNKS OF USELESS DATA
```

## remove kernel

```bash
# remove_kernel
uv run cleanup/remove_kernel.py --dry-run  # should list test_nb
uv run cleanup/remove_kernel.py  # remove it, verify gone from kernelspec list
```

### results

dry run:

```
uv run cleanup/remove_kernel.py --dry-run
Installed 11 packages in 31ms

found 20 kernel(s):

kernel name    display name          venv
au             Au                    MISSING /Users/rjlarson/src/Au/.venv
databases      databases             MISSING /Users/rjlarson/src/databases/.venv
deepspaceten   DeepSpaceTen          MISSING /Users/rjlarson/src/DeepSpaceTen/.venv
fifteens       fifteens              /Users/rjlarson/src/fifteens/.venv
githubutils    GithubUtils           MISSING /Users/rjlarson/src/GithubUtils/.venv
laughtale      LaughTale             /Users/rjlarson/vaults/Laugh-Tale/.venv
lmbooktesting  LMBookTesting         /Users/rjlarson/src/LMBookTesting/.venv
mailcall       MailCall              MISSING /Users/rjlarson/src/MailCall/.venv
marktechpost   MarkTechPost          MISSING /Users/rjlarson/src/forks/AI-Tutorial-Codes-Included/.venv
onetabdeob     OneTabDeob            MISSING /Users/rjlarson/src/OneTabDeob/.venv
parsing        parsing               MISSING /Users/rjlarson/src/sysa/mit-ocw_courses/.venv
project        project               MISSING /Users/rjlarson/src/Agents/ToyLangGraph/.venv
pymtg          pyMTG                 MISSING /Users/rjlarson/src/mtg_tools/pyMTG/.venv
python3        Python 3 (ipykernel)  MISSING /Users/rjlarson/src/sysa/mit-ocw_courses/.venv
spacy-tests    spacy-tests           MISSING /Users/rjlarson/src/spacy-tests/.venv
sysa           SySa                  /Users/rjlarson/src/SySA/.venv
test_nb        test_nb               MISSING /Users/rjlarson/src/automations/test-nb/.venv
tfs            TFS                   MISSING /Users/rjlarson/src/TransformerFromScratch/.venv
toylanggraph   ToyLangGraph          MISSING /Users/rjlarson/src/Agents/ToyLangGraph/.venv
voicevault     VoiceVault            MISSING /Users/rjlarson/src/VoiceVault/.venv

? Select kernels to remove (space to toggle, enter to confirm): done (17 selections)

  (dry run) removing au  →  /Users/rjlarson/Library/Jupyter/kernels/au
  (dry run) removing databases  →  /Users/rjlarson/Library/Jupyter/kernels/databases
  (dry run) removing deepspaceten  →  /Users/rjlarson/Library/Jupyter/kernels/deepspaceten
  (dry run) removing fifteens  →  /Users/rjlarson/Library/Jupyter/kernels/fifteens
  (dry run) removing githubutils  →  /Users/rjlarson/Library/Jupyter/kernels/githubutils
  (dry run) removing mailcall  →  /Users/rjlarson/Library/Jupyter/kernels/mailcall
  (dry run) removing marktechpost  →  /Users/rjlarson/Library/Jupyter/kernels/marktechpost
  (dry run) removing onetabdeob  →  /Users/rjlarson/Library/Jupyter/kernels/onetabdeob
  (dry run) removing parsing  →  /Users/rjlarson/Library/Jupyter/kernels/parsing
  (dry run) removing project  →  /Users/rjlarson/Library/Jupyter/kernels/project
  (dry run) removing pymtg  →  /Users/rjlarson/Library/Jupyter/kernels/pymtg
  (dry run) removing python3  →  /Users/rjlarson/Library/Jupyter/kernels/python3
  (dry run) removing spacy-tests  →  /Users/rjlarson/Library/Jupyter/kernels/spacy-tests
  (dry run) removing test_nb  →  /Users/rjlarson/Library/Jupyter/kernels/test_nb
  (dry run) removing tfs  →  /Users/rjlarson/Library/Jupyter/kernels/tfs
  (dry run) removing toylanggraph  →  /Users/rjlarson/Library/Jupyter/kernels/toylanggraph
  (dry run) removing voicevault  →  /Users/rjlarson/Library/Jupyter/kernels/voicevault

done. removed 17 kernels (dry run — nothing deleted)

```

regular: worked

## python_lib

```bash
# python_lib
uv run init/python_lib.py test-lib --no-github
cd test-lib && uv run pytest && uvx pre-commit run --all-files
```

### results

works

## python_script

```bash
# python_script
uv run init/python_script.py test-script --no-github
cd test-script && uv run test_script.py
```

### results

works

## test crate

```bash
# rust
uv run init/rust.py test-crate --no-github
cd test-crate && cargo run && uvx pre-commit run --all-files
```

### results

works

## js vite

```bash
# js (vite, no bun dependency)
uv run init/js.py test-js --flavor vite --npm --no-github
cd test-js && npm run dev
```

### results

hung, the dev command did not run

## generic

```bash
# generic
uv run init/generic.py test-generic --lang gleam --no-commit --no-github
cd test-generic && cat .gitignore  # gleam extras present
```

### results

worked

## hugo

```bash
# hugo (skip if hugo not installed)
uv run init/hugo.py  # interactive; enter test values, --no-github
cd <name> && hugo server
```

### results

worked

## update

```bash
# update.py
uv run update.py --root . --yes  # should find automations' own config
```

### results

worked
