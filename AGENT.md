# DocUnlok — Developer Guide & AI Agent Guidelines

DocUnlok is a small PyQt6 desktop utility that strips password protection from PDF files. Select one or more password-protected PDFs, supply the password, and the tool decrypts them in place.

---

## AI Agent Response & Workflow Guidelines

### Mandatory workflow for every feature / bug fix

1. **Open a GitHub issue** — before anything else, create a GitHub issue for the task (`gh issue create`). Use the appropriate label (`bug`, `enhancement`, `feature`) and priority (`P1`/`P2`/`P3`). Record the issue number.
   - Every issue body must mention the creation/report date in `YYYY-MM-DD` format.
2. **Plan** — prepare an implementation plan, save it as a `.md` file in the untracked `PlansofThisProject/` subfolder, and get user approval before writing any code.
   - Plan filenames must start with the issue number prefix: `F-<n>_<description>.md`, `B-<n>_<description>.md`, etc.
3. **Implement** — build the feature or fix following the approved plan.
4. **Close the issue** — before closing, add a closing comment stating what changed and the verification performed. Then close it (`gh issue close <number>`).

### General guidelines

- **Plain English Only:** When explaining anything to the user, use plain, everyday language — not technical jargon. This does not apply to code, commit messages, or code comments.
- **Concise Responses:** Avoid long conversational padding. No trailing summaries. No emojis unless explicitly requested.
- **Active Python Path:** Use the explicit `.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows) interpreter.

---

## Project Layout

```
DocUnlok/
├── app.py                  # Main window — all Qt widgets, batch runner
├── version.py               # Single source of truth: __version__ = "X.Y.Z"
├── themes.py                # ThemeColors dataclass, dark/light theme builders
├── pdf_unlocker.py           # pikepdf-based decrypt-in-place logic
├── requirements.txt
├── scripts/
│   └── setup_and_build.ps1   # Windows build (Nuitka standalone exe)
├── resources/                # Icons
└── PlansofThisProject/       # untracked planning docs
```

---

## Key Architecture Decisions

- **PyQt6** for UI — stylesheet-based theming via `themes.py`. Do not switch to tkinter or CustomTkinter.
- **pikepdf** (qpdf bindings) for PDF decryption — write to a temp file, verify it opens unencrypted, then `os.replace` onto the original. Never overwrite the original before verification succeeds.
- **QThread** for the batch job — keeps the Qt event loop responsive. Never call widget methods from the worker thread directly; use signals (`line_ready`, `finished`).
- **No Nuitka installer** — this is a single small utility; the Windows build produces a standalone `.exe` only, no Inno Setup/WiX installer.

---

## Versioning

**Single source of truth:** `version.py`

```python
__version__ = "1.0.0"
```

Bump manually when releasing a new version; update `README.md`'s version line to match.

---

## Dev Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

---

## Windows Build

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_and_build.ps1
```

Produces `dist\DocUnlok.exe` (standalone, no installer).

Prerequisite: `pip install nuitka ordered-set zstandard` (handled by the build script).
