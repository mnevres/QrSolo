import logging
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
                             QLineEdit, QRadioButton, QButtonGroup, QComboBox,
                             QCheckBox, QPushButton, QFileDialog)

from qr_generator.engine import make_custom_qr
from qr_generator.utils import sanitize_filename


def _wifi_escape(value):
    """Backslash-escape characters that are special in the WIFI: QR payload format."""
    return re.sub(r'([\\;,":])', r'\\\1', value)


def build_wifi_string(ssid, password, security_choice, hidden):
    sec = {'WPA/WPA2': 'WPA', 'WEP': 'WEP'}.get(security_choice, 'nopass')

    parts = [f"WIFI:T:{sec}", f"S:{_wifi_escape(ssid)}"]
    if sec != 'nopass':
        parts.append(f"P:{_wifi_escape(password)}")
    parts.append(f"H:{'true' if hidden else 'false'}")
    return ";".join(parts) + ";;"


class WiFiTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.editing_wifi_id = None

        self.tab_hlayout = QHBoxLayout(self)
        self.tab_hlayout.setContentsMargins(0, 0, 0, 0)
        self.tab_hlayout.setSpacing(0)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.ssid_label = QLabel('Network Name (SSID)')
        self.ssid_input = QLineEdit()
        form_layout.addRow(self.ssid_label, self.ssid_input)

        self.password_label = QLabel('Password')
        self.password_input = QLineEdit()
        form_layout.addRow(self.password_label, self.password_input)

        self.security_label = QLabel('Security Type')
        self.security_combo = QComboBox()
        self.security_combo.addItems(['WPA/WPA2', 'WEP', 'None'])
        self.security_combo.currentTextChanged.connect(self._update_password_enabled)
        form_layout.addRow(self.security_label, self.security_combo)

        layout.addLayout(form_layout)

        self.hidden_check = QCheckBox('Hidden Network')
        self.hidden_check.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.hidden_check)

        export_section = QVBoxLayout()
        export_section.setSpacing(10)
        self.format_label_wifi = QLabel('Select Format:')
        export_section.addWidget(self.format_label_wifi)

        radio_layout = QHBoxLayout()
        self.png_radio_wifi = QRadioButton("PNG")
        self.svg_radio_wifi = QRadioButton("SVG")
        self.svg_radio_wifi.setChecked(True)
        self.radio_group_wifi = QButtonGroup()
        self.radio_group_wifi.addButton(self.png_radio_wifi)
        self.radio_group_wifi.addButton(self.svg_radio_wifi)
        radio_layout.addWidget(self.png_radio_wifi)
        radio_layout.addWidget(self.svg_radio_wifi)
        radio_layout.addStretch()
        export_section.addLayout(radio_layout)

        # Stacked instead of side-by-side: this column is narrow enough that
        # splitting it between two buttons left "Save WiFi QR" too little
        # room and its uppercased label got visually clipped. Full-width
        # rows (matching the URL tab's single Save button) give each one
        # all the space it needs.
        wifi_buttons_layout = QVBoxLayout()
        wifi_buttons_layout.setSpacing(10)
        self.generate_button_wifi = QPushButton('Save WiFi QR')
        self.generate_button_wifi.clicked.connect(self.generate_qr_code)
        wifi_buttons_layout.addWidget(self.generate_button_wifi)

        self.clear_wifi_btn = QPushButton('New WiFi')
        self.clear_wifi_btn.setObjectName("clear_vcard_btn")
        self.clear_wifi_btn.clicked.connect(self.clear_wifi_form)
        wifi_buttons_layout.addWidget(self.clear_wifi_btn)

        export_section.addLayout(wifi_buttons_layout)

        layout.addLayout(export_section)
        layout.addStretch()

        self.tab_hlayout.addWidget(content_widget, stretch=1)

        self.ssid_input.textChanged.connect(self.main_window.update_preview)
        self.password_input.textChanged.connect(self.main_window.update_preview)
        self.security_combo.currentTextChanged.connect(lambda _: self.main_window.update_preview())
        self.hidden_check.stateChanged.connect(lambda _: self.main_window.update_preview())

    def _update_password_enabled(self, security_choice):
        self.password_input.setEnabled(security_choice != 'None')

    def update_language_ui(self, t):
        self.ssid_label.setText(t.get('wifi_ssid', 'Network Name (SSID)'))
        self.password_label.setText(t.get('wifi_password', 'Password'))
        self.security_label.setText(t.get('wifi_security', 'Security Type'))
        self.hidden_check.setText(t.get('wifi_hidden', 'Hidden Network'))
        self.format_label_wifi.setText(t.get('export_format', 'Select Format:'))
        self.generate_button_wifi.setText(t.get('generate_button_wifi', 'Save WiFi QR'))
        self.clear_wifi_btn.setText(t.get('new_wifi_button', 'New WiFi'))

    def build_wifi_string(self):
        ssid = self.ssid_input.text().strip()
        password = self.password_input.text()
        security_choice = self.security_combo.currentText()
        hidden = self.hidden_check.isChecked()
        return build_wifi_string(ssid, password, security_choice, hidden)

    def clear_wifi_form(self):
        self.editing_wifi_id = None
        self.ssid_input.clear()
        self.password_input.clear()
        self.security_combo.setCurrentIndex(0)
        self.hidden_check.setChecked(False)
        self.main_window.update_preview()

    def load_wifi(self, wifi_id, ssid, password, security, hidden):
        self.editing_wifi_id = wifi_id
        self.ssid_input.setText(ssid)
        self.password_input.setText(password)
        index = self.security_combo.findText(security)
        self.security_combo.setCurrentIndex(index if index >= 0 else 0)
        self.hidden_check.setChecked(bool(hidden))
        self.main_window.update_preview()

    def generate_qr_code(self):
        mw = self.main_window
        try:
            ssid = self.ssid_input.text().strip()
            if not ssid:
                mw.show_toast(mw.wifi_ssid_error_message, is_error=True)
                return

            wifi_data = self.build_wifi_string()

            is_svg = not self.png_radio_wifi.isChecked()
            mw.qr_img = make_custom_qr(wifi_data, fg_color=mw.fg_color, bg_color=mw.bg_color, is_transparent=mw.is_transparent, is_svg=is_svg, size=mw.img_size, logo_path=mw.logo_path)

            filename = f"{sanitize_filename(ssid)}_wifi" + (".svg" if is_svg else ".png")
            file_type = "SVG Files (*.svg)" if is_svg else "PNG Files (*.png)"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save WiFi QR", filename, file_type)
            if file_path:
                mw.qr_img.save(file_path)
                security = self.security_combo.currentText()
                hidden = 1 if self.hidden_check.isChecked() else 0
                if self.editing_wifi_id is not None:
                    mw.db.update_wifi(self.editing_wifi_id, ssid, self.password_input.text(), security, hidden)
                else:
                    self.editing_wifi_id = mw.db.add_wifi(ssid, self.password_input.text(), security, hidden)
                mw.archive_window.load_archive()
                mw.populate_sidebar()
                mw.show_toast(mw.success_qr_message)
        except Exception as e:
            logging.error("Error generating or saving WiFi QR: %s", e, exc_info=True)
            print(f"WIFI QR ERROR: {e}")
            mw.show_toast(mw.error_message, is_error=True)
