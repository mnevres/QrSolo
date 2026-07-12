import logging
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel,
                             QLineEdit, QRadioButton, QButtonGroup, QPushButton, QFileDialog)

from qr_generator.engine import make_custom_qr
from qr_generator.utils import sanitize_filename


class URLTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.tab_hlayout = QHBoxLayout(self)
        self.tab_hlayout.setContentsMargins(0, 0, 0, 0)
        self.tab_hlayout.setSpacing(0)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.url_label = QLabel('Enter URL:')
        self.url_input = QLineEdit()
        form_layout.addRow(self.url_label, self.url_input)
        layout.addLayout(form_layout)

        export_section = QVBoxLayout()
        export_section.setSpacing(10)
        self.format_label_url = QLabel('Select Format:')
        export_section.addWidget(self.format_label_url)

        radio_layout = QHBoxLayout()
        self.png_radio_url = QRadioButton("PNG")
        self.svg_radio_url = QRadioButton("SVG")
        self.svg_radio_url.setChecked(True)
        self.radio_group_url = QButtonGroup()
        self.radio_group_url.addButton(self.png_radio_url)
        self.radio_group_url.addButton(self.svg_radio_url)
        radio_layout.addWidget(self.png_radio_url)
        radio_layout.addWidget(self.svg_radio_url)
        radio_layout.addStretch()
        export_section.addLayout(radio_layout)

        self.generate_button_url = QPushButton('Save QR Code')
        self.generate_button_url.clicked.connect(self.generate_qr_code)
        export_section.addWidget(self.generate_button_url)

        layout.addLayout(export_section)
        layout.addStretch()

        self.tab_hlayout.addWidget(content_widget, stretch=1)

        self.url_input.textChanged.connect(self.main_window.update_preview)

    def update_language_ui(self, t):
        self.url_label.setText(t.get('enter_url', 'Enter URL:'))
        self.format_label_url.setText(t.get('export_format', 'Select Format:'))
        self.generate_button_url.setText(t.get('generate_button_url', 'Export QR Code'))

    def generate_qr_code(self):
        mw = self.main_window
        try:
            url_text = self.url_input.text()
            if not url_text:
                mw.show_toast(mw.url_error_message, is_error=True)
                return

            is_svg = not self.png_radio_url.isChecked()
            mw.qr_img = make_custom_qr(url_text, fg_color=mw.fg_color, bg_color=mw.bg_color, is_transparent=mw.is_transparent, is_svg=is_svg, size=mw.img_size)

            filename = f"{sanitize_filename(url_text)}_qr" + (".svg" if is_svg else ".png")
            file_type = "SVG Files (*.svg)" if is_svg else "PNG Files (*.png)"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save QR", filename, file_type)
            if file_path:
                mw.qr_img.save(file_path)
                mw.db.add_url(url_text)
                mw.archive_window.load_archive()
                mw.populate_sidebar()
                mw.show_toast(mw.success_qr_message)
        except Exception as e:
            logging.error("Error generating or saving QR: %s", e, exc_info=True)
            print(f"QR ERROR: {e}")
            mw.show_toast(mw.error_message, is_error=True)
