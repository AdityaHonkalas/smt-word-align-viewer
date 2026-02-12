# SMT Word Align Viewer

Flask app for sentence translation and word-level alignment visualization.

## System architecture design

### High-level architecture

```text
+------------------+        HTTP         +------------------------------+
| Browser UI       | <-----------------> | Flask app (`app.py`)         |
| (HTML/CSS)       |                     | Routes: `/`, `/translate`    |
+------------------+                     +--------------+---------------+
                                                       |
                                                       v
                                      +-------------------------------+
                                      | SMT service (`smt/engine.py`) |
                                      | - Tokenize input              |
                                      | - Decode/translate            |
                                      | - Build word alignments       |
                                      +---------+---------------------+
                                                |
                 +------------------------------+-------------------------------+
                 |                                                              |
                 v                                                              v
  +-------------------------------+                             +-------------------------------+
  | Python translation libraries  |                             | Optional SMT toolkits         |
  | Polyglot / deep-translator    |                             | Moses / FastAlign / GIZA++    |
  | sentence-level translation    |                             | for external training         |
  +-------------------------------+                             +-------------------------------+
```

### Component design

- Presentation layer:
  - `templates/index.html`, `templates/base.html`, `static/style.css`
  - Renders input form, translated output, and alignment matrix.
- Application/API layer:
  - `app.py`
  - Handles web requests and invokes SMT translation service.
- SMT core layer:
  - `smt/engine.py`: sentence-level translation orchestration and alignment payload generation.
  - `smt/library_translate.py`: Polyglot-first translation backend with Python-library fallback.
  - `smt/tokenize.py`: tokenization and detokenization utilities.
  - `smt/alignment.py`: heuristic/positional word alignment and matrix generation.
  - `smt/config.py`: runtime configuration from environment variables.
  - `smt/toolkit.py`: subprocess wrappers for Moses/FastAlign/atools (optional).

### Runtime flow

1. User enters a source sentence in the Flask UI.
2. `POST /translate` sends text to `SMTTranslator`.
3. `SMTTranslator` performs sentence-level translation using Python library backends:
   - Polyglot first
   - deep-translator fallback
4. Word alignment is computed heuristically for visualization.
5. The app returns:
   - translated full sentence in target language,
   - backend identifier,
   - GIZA-format alignment pairs,
   - alignment matrix for visualization.

### Deployment notes

- App runs as a single Flask service process.
- Translation libraries may require internet access depending on the backend.
- SMT binaries (Moses/FastAlign/GIZA++) remain optional.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000/`.

## Environment variables

- `SMT_TARGET_LANGUAGES` comma-separated target language codes (default: `hi,bn,ta,te,mr,gu`)
- `SMT_DEFAULT_TARGET_LANGUAGE` default target language code (default: first from `SMT_TARGET_LANGUAGES`)
- `SMT_SOURCE_LANGUAGE` source language code for library translation (default: `en`)
- `MOSES_BIN` path to Moses decoder executable
- `FAST_ALIGN_BIN` path to `fast_align`
- `ATOOLS_BIN` path to `atools`
- `GIZA_ROOT` path to GIZA++ installation

## Toolkit integration

The app now uses Python translation libraries for runtime sentence translation.
If Polyglot is unavailable in your environment, it automatically falls back to `deep-translator`.
SMT toolkit scripts are still available if you want to train/export alignments externally.
