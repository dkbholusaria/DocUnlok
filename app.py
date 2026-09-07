"""
app.py — DocUnlok main window.

Select one or more password-protected PDFs from any location, supply the
password, and strip the password protection in place. Batch runs on a
background thread so the GUI stays responsive.
"""

import os
import sys
import logging

from PyQt6.QtCore import (
    Qt, QObject, QThread, QTimer, QUrl, QMetaObject, Q_ARG, pyqtSignal, pyqtSlot,
)
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QAbstractItemView, QDialog,
)

from themes import THEMES
from pdf_unlocker import decrypt_pdf_inplace
from version import __version__

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)

STATUS_COL = 2
t = THEMES["dark"]


class Worker(QObject):
    """Runs the batch decrypt job on a background thread, signalling results back."""

    row_status = pyqtSignal(int, str)  # row index, status text
    finished = pyqtSignal(int, int, int)  # decrypted, already_unencrypted, failed

    def __init__(self, files: list[str], password: str):
        super().__init__()
        self.files = files
        self.password = password

    def run(self):
        decrypted = already = failed = 0
        for row, path in enumerate(self.files):
            result = decrypt_pdf_inplace(path, self.password)
            status = result["status"]
            if status == "decrypted":
                decrypted += 1
                self.row_status.emit(row, "Decrypted")
            elif status == "already_unencrypted":
                already += 1
                self.row_status.emit(row, "Already unencrypted")
            else:
                failed += 1
                self.row_status.emit(row, f"Failed: {result.get('reason', 'unknown error')}")
        self.finished.emit(decrypted, already, failed)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocUnlok")
        self.resize(820, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {t.bg_window}; }}")

        self.selected_files: list[str] = []
        self.worker: Worker | None = None
        self.thread: QThread | None = None

        root_widget = QWidget()
        self.setCentralWidget(root_widget)
        root = QVBoxLayout(root_widget)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._mk_header())
        root.addWidget(self._mk_main_panel(), 1)
        root.addWidget(self._mk_footer())

        QTimer.singleShot(3000, self._check_for_update)

    # ── Header ────────────────────────────────────────────────────────────

    def _mk_header(self):
        hdr = QFrame()
        hdr.setFixedHeight(90)
        hdr.setStyleSheet(f"QFrame {{ background: {t.bg_window}; border: none; }}")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(32, 0, 32, 0)
        hl.setSpacing(0)

        icon = QLabel("\U0001F513")  # open-lock emoji as a simple visual anchor
        icon.setStyleSheet("font-size:40px; background:transparent; border:none;")
        hl.addWidget(icon)
        hl.addSpacing(16)

        name_block = QWidget()
        name_block.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(name_block)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(3)
        vl.addStretch()

        title = QLabel("DocUnlok")
        title.setStyleSheet(
            f"color:{t.text_primary}; font-size:24px; font-weight:700; "
            f"background:transparent; border:none;"
        )
        vl.addWidget(title)

        subtitle = QLabel("Strip password protection from PDF files, in place.")
        subtitle.setStyleSheet(f"color:{t.text_muted}; font-size:12px; background:transparent; border:none;")
        vl.addWidget(subtitle)
        vl.addStretch()

        hl.addWidget(name_block)
        hl.addStretch()

        meta_block = QWidget()
        meta_block.setStyleSheet("background:transparent;")
        ml = QVBoxLayout(meta_block)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(1)
        ml.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        version_lbl = QLabel(f"v{__version__}")
        version_lbl.setStyleSheet(f"color:{t.text_muted}; font-size:11px; background:transparent; border:none;")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        ml.addWidget(version_lbl)

        copy_lbl = QLabel("© 2026 Deepak Bhholusaria")
        copy_lbl.setStyleSheet(f"color:{t.text_muted}; font-size:11px; background:transparent; border:none;")
        copy_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        ml.addWidget(copy_lbl)

        self._update_lnk = QLabel()
        self._update_lnk.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._update_lnk.setOpenExternalLinks(False)
        self._update_lnk.linkActivated.connect(self._on_update_link_clicked)
        self._update_lnk.setFixedHeight(16)
        ml.addWidget(self._update_lnk)

        hl.addWidget(meta_block)
        hl.addSpacing(12)

        about_btn = QPushButton("ⓘ")  # ⓘ
        about_btn.setFixedSize(30, 30)
        about_btn.setToolTip("About DocUnlok")
        about_btn.setStyleSheet(
            f"QPushButton {{ background:transparent; border:none; font-size:18px; color:{t.text_muted}; }}"
            f"QPushButton:hover {{ color:{t.accent}; }}"
        )
        about_btn.clicked.connect(self._show_about)
        hl.addWidget(about_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        return hdr

    # ── Main panel: control bar + table ──────────────────────────────────────

    def _mk_main_panel(self):
        panel = QWidget()
        panel.setStyleSheet(f"background: {t.bg_window};")
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(24, 16, 24, 16)
        pl.setSpacing(14)

        pl.addWidget(self._mk_control_bar())
        pl.addWidget(self._mk_table(), stretch=1)

        return panel

    def _mk_caption(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{t.text_muted}; font-size:10px; font-weight:700; "
            f"letter-spacing:0.8px; background:transparent; border:none;"
        )
        return lbl

    def _mk_control_bar(self):
        bar = QFrame()
        bar.setStyleSheet(f"QFrame {{ background:{t.bg_panel}; border-radius:10px; }}")
        outer = QVBoxLayout(bar)
        outer.setContentsMargins(18, 14, 18, 14)
        outer.setSpacing(10)

        # ── Files row ──
        files_caption_row = QHBoxLayout()
        files_caption_row.addWidget(self._mk_caption("FILES"))
        files_caption_row.addStretch()
        outer.addLayout(files_caption_row)

        files_row = QHBoxLayout()
        files_row.setSpacing(8)

        self.select_btn = QPushButton("Select Files…")
        self.select_btn.setStyleSheet(self._accent_btn_style())
        self.select_btn.clicked.connect(self.on_select_files)
        files_row.addWidget(self.select_btn)

        self.add_btn = QPushButton("Add Files…")
        self.add_btn.setStyleSheet(self._outline_btn_style())
        self.add_btn.clicked.connect(self.on_add_files)
        files_row.addWidget(self.add_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet(self._outline_btn_style())
        self.clear_btn.clicked.connect(self.on_clear_files)
        files_row.addWidget(self.clear_btn)

        self.file_count_label = QLabel("No files selected")
        self.file_count_label.setStyleSheet(f"color:{t.text_muted}; font-size:12px; background:transparent;")
        files_row.addWidget(self.file_count_label, stretch=1)
        outer.addLayout(files_row)

        # ── Password row ──
        outer.addWidget(self._mk_caption("PASSWORD"))
        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(8)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password common to all selected PDFs")
        self.password_input.setStyleSheet(self._line_edit_style())
        pwd_row.addWidget(self.password_input, stretch=1)

        self.toggle_pwd_btn = QPushButton("Show")
        self.toggle_pwd_btn.setCheckable(True)
        self.toggle_pwd_btn.setStyleSheet(self._outline_btn_style())
        self.toggle_pwd_btn.setFixedWidth(70)
        self.toggle_pwd_btn.toggled.connect(self.on_toggle_password_visibility)
        pwd_row.addWidget(self.toggle_pwd_btn)

        outer.addLayout(pwd_row)

        return bar

    def _mk_table(self):
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Path", "Status"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setStyleSheet(
            f"QTableWidget {{ border: 1.5px solid {t.border}; border-radius: 8px;"
            f" background: {t.bg_table}; alternate-background-color: {t.bg_table_alt};"
            f" outline: 0; gridline-color: {t.grid}; color: {t.text_primary}; font-size: 12px; }}"
            f"QTableWidget::item {{ border-bottom: 1px solid {t.grid}; padding: 5px 8px; }}"
        )
        header.setStyleSheet(
            f"QHeaderView::section {{ background-color: {t.bg_header}; border: none;"
            f" border-bottom: 1px solid {t.border}; font-weight: bold; color: {t.text_muted};"
            f" font-size: 11px; height: 32px; padding: 0 8px; }}"
        )
        return self.table

    # ── Footer ────────────────────────────────────────────────────────────

    def _mk_footer(self):
        footer = QFrame()
        footer.setFixedHeight(64)
        footer.setStyleSheet(f"QFrame {{ background:{t.bg_panel}; border-top: 1px solid {t.border}; }}")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(24, 0, 24, 0)
        fl.setSpacing(16)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet(f"color:{t.text_muted}; font-size:12px; background:transparent;")
        fl.addWidget(self.summary_label, stretch=1)

        self.remove_btn = QPushButton("Remove Password")
        self.remove_btn.setStyleSheet(self._accent_btn_style())
        self.remove_btn.setMinimumWidth(180)
        self.remove_btn.clicked.connect(self.on_remove_password)
        fl.addWidget(self.remove_btn)

        return footer

    # ── Shared inline styles ─────────────────────────────────────────────

    def _accent_btn_style(self):
        return (
            f"QPushButton {{ background:{t.accent}; color:{t.accent_text}; border:none;"
            f" border-radius:6px; padding:8px 16px; font-size:13px; font-weight:600; min-height:26px; }}"
            f"QPushButton:hover {{ background:{t.accent_hover}; }}"
            f"QPushButton:disabled {{ background:{t.border}; color:{t.text_disabled}; }}"
        )

    def _outline_btn_style(self):
        return (
            f"QPushButton {{ background:transparent; color:{t.text_primary}; border:1px solid {t.border};"
            f" border-radius:6px; padding:8px 14px; font-size:13px; font-weight:600; min-height:26px; }}"
            f"QPushButton:hover {{ background:{t.bg_table_alt}; }}"
            f"QPushButton:disabled {{ color:{t.text_disabled}; border-color:{t.border}; }}"
        )

    def _line_edit_style(self):
        return (
            f"QLineEdit {{ background:{t.bg_input}; border:1.5px solid {t.border}; border-radius:6px;"
            f" padding:6px 10px; font-size:13px; color:{t.text_primary}; min-height:26px; }}"
            f"QLineEdit:focus {{ border-color:{t.border_focus}; background:{t.bg_input_focus}; }}"
            f"QLineEdit::placeholder {{ color:{t.text_muted}; }}"
        )

    # ── About ─────────────────────────────────────────────────────────────

    def _show_about(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("About DocUnlok")
        dlg.setFixedSize(420, 380)
        dlg.setStyleSheet(
            f"QDialog {{ background:{t.bg_window}; }}"
            f"QLabel {{ border:none; background:transparent; color:{t.text_primary}; }}"
        )

        vl = QVBoxLayout(dlg)
        vl.setContentsMargins(32, 26, 32, 26)
        vl.setSpacing(0)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        icon_lbl = QLabel("\U0001F513")
        icon_lbl.setStyleSheet("font-size:32px; background:transparent; border:none;")
        title_row.addWidget(icon_lbl)
        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name_lbl = QLabel("DocUnlok")
        name_lbl.setStyleSheet(f"color:{t.text_primary}; font-size:18px; font-weight:700;")
        ver_lbl = QLabel(f"Version {__version__}")
        ver_lbl.setStyleSheet(f"color:{t.text_muted}; font-size:12px;")
        name_col.addWidget(name_lbl)
        name_col.addWidget(ver_lbl)
        title_row.addLayout(name_col)
        title_row.addStretch()
        vl.addLayout(title_row)
        vl.addSpacing(14)

        desc = QLabel("A small desktop utility to strip password protection from PDF files, in place.")
        desc.setStyleSheet(f"color:{t.text_primary}; font-size:13px;")
        desc.setWordWrap(True)
        vl.addWidget(desc)
        vl.addSpacing(18)

        div1 = QFrame()
        div1.setFrameShape(QFrame.Shape.HLine)
        div1.setStyleSheet(f"background:{t.border}; border:none; max-height:1px;")
        vl.addWidget(div1)
        vl.addSpacing(16)

        contact_title = QLabel("Contact")
        contact_title.setStyleSheet(f"color:{t.text_muted}; font-size:10px; font-weight:700; letter-spacing:1px;")
        vl.addWidget(contact_title)
        vl.addSpacing(8)

        def _link_row(text: str, url: str | None = None):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            if url:
                lbl = QLabel(f'<a href="{url}" style="color:{t.accent}; text-decoration:none;">{text}</a>')
                lbl.setOpenExternalLinks(True)
            else:
                lbl = QLabel(text)
                lbl.setStyleSheet(f"color:{t.text_primary}; font-size:13px; font-weight:600;")
            lbl.setStyleSheet(lbl.styleSheet() + "font-size:13px; background:transparent; border:none;")
            row.addWidget(lbl)
            row.addStretch()
            return row

        vl.addLayout(_link_row("CA. Deepak Bhholusaria"))
        vl.addSpacing(6)
        vl.addLayout(_link_row("deepak@ailearrning.guru", "mailto:deepak@ailearrning.guru"))
        vl.addSpacing(6)
        vl.addLayout(_link_row("linkedin.com/in/bhholusaria", "https://www.linkedin.com/in/bhholusaria/"))
        vl.addSpacing(6)
        vl.addLayout(_link_row("github.com/dkbholusaria/DocUnlok", "https://github.com/dkbholusaria/DocUnlok"))
        vl.addSpacing(16)

        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet(f"background:{t.border}; border:none; max-height:1px;")
        vl.addWidget(div2)
        vl.addSpacing(12)

        copy = QLabel("© 2026 Deepak Bhholusaria. All rights reserved.")
        copy.setStyleSheet(f"color:{t.text_muted}; font-size:11px;")
        vl.addWidget(copy)
        vl.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet(self._accent_btn_style())
        close_btn.clicked.connect(dlg.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        vl.addLayout(btn_row)

        dlg.exec()

    # ── Update check ──────────────────────────────────────────────────────

    def _check_for_update(self):
        from updater import check_for_update

        def _cb(tag, url):
            # check_for_update runs the callback from a background thread —
            # marshal back onto the GUI thread before touching any widget.
            QMetaObject.invokeMethod(
                self, "_on_update_result",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, tag or ""), Q_ARG(str, url or ""),
            )

        check_for_update(_cb)

    @pyqtSlot(str, str)
    def _on_update_result(self, tag: str, url: str):
        if tag:
            self._update_url = url
            self._update_lnk.setText(
                f'<a href="#" style="color:{t.accent}; font-size:11px;">&#11015; v{tag} available</a>'
            )

    def _on_update_link_clicked(self):
        if getattr(self, "_update_url", None):
            QDesktopServices.openUrl(QUrl(self._update_url))

    # ── File selection ───────────────────────────────────────────────────

    def on_select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        if not files:
            return
        self.selected_files = files
        self._refresh_table()

    def on_add_files(self):
        # Repeated invocations can browse different folders/drives each time;
        # results are appended (de-duplicated) rather than replacing the list.
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add PDF Files", "", "PDF Files (*.pdf)"
        )
        if not files:
            return
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)
        self._refresh_table()

    def on_toggle_password_visibility(self, checked: bool):
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
        self.toggle_pwd_btn.setText("Hide" if checked else "Show")

    def on_clear_files(self):
        self.selected_files = []
        self._refresh_table()

    def _refresh_table(self):
        self.summary_label.setText("")
        self.file_count_label.setText(
            f"{len(self.selected_files)} file(s) selected" if self.selected_files else "No files selected"
        )
        self.table.setRowCount(len(self.selected_files))
        for row, path in enumerate(self.selected_files):
            self.table.setItem(row, 0, QTableWidgetItem(os.path.basename(path)))
            self.table.setItem(row, 1, QTableWidgetItem(os.path.dirname(path)))
            self.table.setItem(row, STATUS_COL, QTableWidgetItem("Pending"))

    def set_row_status(self, row: int, status: str):
        self.table.setItem(row, STATUS_COL, QTableWidgetItem(status))

    # ── Batch run ─────────────────────────────────────────────────────────

    def on_remove_password(self):
        if not self.selected_files:
            QMessageBox.warning(self, "No files selected", "Select one or more PDF files first.")
            return
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "No password", "Enter the PDF password first.")
            return

        self.remove_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.summary_label.setText("Processing…")
        for row in range(self.table.rowCount()):
            self.set_row_status(row, "Pending")

        self.worker = Worker(self.selected_files, password)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.row_status.connect(self.set_row_status)
        self.worker.finished.connect(self.on_batch_finished)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def on_batch_finished(self, decrypted: int, already: int, failed: int):
        total = decrypted + already + failed
        self.summary_label.setText(
            f"Done: {decrypted} decrypted, {already} already unencrypted, "
            f"{failed} failed (out of {total})"
        )
        self.remove_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
