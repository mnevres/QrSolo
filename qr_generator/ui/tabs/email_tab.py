import logging
from urllib.parse import quote
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
                             QLineEdit, QPlainTextEdit, QRadioButton, QButtonGroup, QPushButton, QFileDialog)

from qr_generator.engine import make_custom_qr
from qr_generator.utils import sanitize_filename


def build_email_uri(to, subject, message):
    uri = f"mailto:{to}"
    params = []
    if subject:
        params.append(f"subject={quote(subject)}")
    if message:
        params.append(f"body={quote(message)}")
    if params:
        uri += "?" + "&".join(params)
    return uri


class EmailTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.editing_email_id = None

        self.tab_hlayout = QHBoxLayout(self)
        self.tab_hlayout.setContentsMargins(0, 0, 0, 0)
        self.tab_hlayout.setSpacing(0)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.to_label = QLabel('Email Address')
        self.to_input = QLineEdit()
        form_layout.addRow(self.to_label, self.to_input)

        self.subject_label = QLabel('Subject')
        self.subject_input = QLineEdit()
        form_layout.addRow(self.subject_label, self.subject_input)

        self.message_label = QLabel('Message')
        self.message_input = QPlainTextEdit()
        self.message_input.setFixedHeight(100)
        # QPlainTextEdit isn't covered by the global QLineEdit stylesheet rule,
        # so its look has to be matched here by hand.
        self.message_input.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1c1c1e;
                color: #ffffff;
                border: 1px solid #2c2c2e;
                padding: 8px 12px;
                border-radius: 10px;
                font-size: 14px;
            }
            QPlainTextEdit:focus {
                border: 1px solid #007AFF;
                background-color: #222226;
            }
        """)
        form_layout.addRow(self.message_label, self.message_input)

        layout.addLayout(form_layout)

        export_section = QVBoxLayout()
        export_section.setSpacing(10)
        self.format_label_email = QLabel('Select Format:')
        export_section.addWidget(self.format_label_email)

        radio_layout = QHBoxLayout()
        self.png_radio_email = QRadioButton("PNG")
        self.svg_radio_email = QRadioButton("SVG")
        self.svg_radio_email.setChecked(True)
        self.radio_group_email = QButtonGroup()
        self.radio_group_email.addButton(self.png_radio_email)
        self.radio_group_email.addButton(self.svg_radio_email)
        radio_layout.addWidget(self.png_radio_email)
        radio_layout.addWidget(self.svg_radio_email)
        radio_layout.addStretch()
        export_section.addLayout(radio_layout)

        # Stacked instead of side-by-side -- same fix as the WiFi tab, since
        # splitting this narrow column between two buttons clipped "Save
        # Email QR" once its label got uppercased by the global style.
        email_buttons_layout = QVBoxLayout()
        email_buttons_layout.setSpacing(10)
        self.generate_button_email = QPushButton('Save Email QR')
        self.generate_button_email.clicked.connect(self.generate_qr_code)
        email_buttons_layout.addWidget(self.generate_button_email)

        self.clear_email_btn = QPushButton('New Email')
        self.clear_email_btn.setObjectName("clear_vcard_btn")
        self.clear_email_btn.clicked.connect(self.clear_email_form)
        email_buttons_layout.addWidget(self.clear_email_btn)

        export_section.addLayout(email_buttons_layout)

        layout.addLayout(export_section)
        layout.addStretch()

        self.tab_hlayout.addWidget(content_widget, stretch=1)

        self.to_input.textChanged.connect(self.main_window.update_preview)
        self.subject_input.textChanged.connect(self.main_window.update_preview)
        self.message_input.textChanged.connect(self.main_window.update_preview)

    def update_language_ui(self, t):
        self.to_label.setText(t.get('email_to', 'Email Address'))
        self.subject_label.setText(t.get('email_subject', 'Subject'))
        self.message_label.setText(t.get('email_message', 'Message'))
        self.format_label_email.setText(t.get('export_format', 'Select Format:'))
        self.generate_button_email.setText(t.get('generate_button_email', 'Save Email QR'))
        self.clear_email_btn.setText(t.get('new_email_button', 'New Email'))

    def build_email_uri(self):
        to = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        message = self.message_input.toPlainText().strip()
        return build_email_uri(to, subject, message)

    def clear_email_form(self):
        self.editing_email_id = None
        self.to_input.clear()
        self.subject_input.clear()
        self.message_input.clear()
        self.main_window.update_preview()

    def load_email(self, email_id, to_address, subject, message):
        self.editing_email_id = email_id
        self.to_input.setText(to_address)
        self.subject_input.setText(subject)
        self.message_input.setPlainText(message)
        self.main_window.update_preview()

    def generate_qr_code(self):
        mw = self.main_window
        try:
            to = self.to_input.text().strip()
            if not to:
                mw.show_toast(mw.email_error_message, is_error=True)
                return

            email_uri = self.build_email_uri()

            is_svg = not self.png_radio_email.isChecked()
            mw.qr_img = make_custom_qr(email_uri, fg_color=mw.fg_color, bg_color=mw.bg_color, is_transparent=mw.is_transparent, is_svg=is_svg, size=mw.img_size, logo_path=mw.logo_path)

            filename = f"{sanitize_filename(to)}_email" + (".svg" if is_svg else ".png")
            file_type = "SVG Files (*.svg)" if is_svg else "PNG Files (*.png)"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Email QR", filename, file_type)
            if file_path:
                mw.qr_img.save(file_path)
                subject = self.subject_input.text().strip()
                message = self.message_input.toPlainText().strip()
                if self.editing_email_id is not None:
                    mw.db.update_email(self.editing_email_id, to, subject, message)
                else:
                    self.editing_email_id = mw.db.add_email(to, subject, message)
                mw.archive_window.load_archive()
                mw.populate_sidebar()
                mw.show_toast(mw.success_qr_message)
        except Exception as e:
            logging.error("Error generating or saving Email QR: %s", e, exc_info=True)
            print(f"EMAIL QR ERROR: {e}")
            mw.show_toast(mw.error_message, is_error=True)
