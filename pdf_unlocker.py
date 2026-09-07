"""
pdf_unlocker.py
===============
Remove the owner/user password from a PDF, given the correct password.

Uses pikepdf (Python bindings for the qpdf library). Writes the decrypted
output to a temp file first, verifies it opens with no encryption, then
atomically replaces the original — the original is only ever overwritten
once we've confirmed the decrypted copy is valid.
"""

import os
import logging

logger = logging.getLogger(__name__)


def decrypt_pdf_inplace(file_path: str, password: str, log=None) -> dict:
    """
    Remove password protection from *file_path*, saving back to the same path.

    :param file_path: Absolute path to the PDF file.
    :param password:  Password to open the PDF (owner or user password).
    :param log:       Optional callable for status messages.
    :returns: dict with keys:
              ``status`` — one of "decrypted", "already_unencrypted", "failed"
              ``reason`` — present only when status == "failed"
    """

    def _log(msg: str):
        if log:
            log(msg)
        logger.debug(msg)

    filename = os.path.basename(file_path)

    try:
        import pikepdf
    except ImportError:
        _log("[PDF Unlock] pikepdf is not installed.")
        return {"status": "failed", "reason": "pikepdf not installed"}

    if not os.path.exists(file_path):
        return {"status": "failed", "reason": "file not found"}

    # Is it even encrypted?
    try:
        with pikepdf.open(file_path):
            return {"status": "already_unencrypted"}
    except pikepdf.PasswordError:
        pass  # encrypted — continue below
    except Exception as e:
        return {"status": "failed", "reason": f"could not open file: {e}"}

    # Open with the supplied password
    try:
        with pikepdf.open(file_path, password=password) as pdf:
            tmp_path = file_path + ".decrypted.tmp"
            pdf.save(tmp_path)
    except pikepdf.PasswordError:
        return {"status": "failed", "reason": "wrong password"}
    except Exception as e:
        return {"status": "failed", "reason": f"error opening/saving: {e}"}

    # Verify the temp file is genuinely decrypted before replacing the original
    try:
        with pikepdf.open(tmp_path) as verify_pdf:
            if verify_pdf.is_encrypted:
                raise ValueError("output file still reports as encrypted")
    except Exception as e:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        return {"status": "failed", "reason": f"verification failed: {e}"}

    os.replace(tmp_path, file_path)
    _log(f"[PDF Unlock] Decrypted {filename}")
    return {"status": "decrypted"}
