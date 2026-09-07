# DocUnlok

**v1.0.0** — A small standalone desktop utility that strips password protection from PDF files. Select one or more password-protected PDFs, supply the password, and it decrypts them in place.

Built with **PyQt6** + **pikepdf**. Runs on Windows, macOS, and Linux.

---

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

---

## Features

| Feature | Details |
|---|---|
| Multi-file select | Pick any number of PDFs at once |
| In-place decrypt | Removes owner + user password, same filename/folder |
| Already-unencrypted detection | Skipped safely, reported not as an error |
| Wrong password handling | Reported per-file, batch continues |
| Safe write | Decrypts to a temp file, verifies it, only then replaces the original |
| Responsive UI | Batch runs on a background thread |

---

## Building a standalone .exe (Windows)

Requires Python 3.10+ and Nuitka.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_and_build.ps1
```

This creates a virtual environment, installs dependencies, and compiles the app with Nuitka to `dist\DocUnlok.exe` — no Python installation needed to run it.

Manual build (if you'd rather not use the script):

```powershell
pip install nuitka ordered-set zstandard
python -m nuitka --standalone --onefile --windows-console-mode=disable ^
  --output-dir=dist --output-filename=DocUnlok.exe ^
  --enable-plugin=pyqt6 --assume-yes-for-downloads app.py
```
