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


class WiFiTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
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

        self.generate_button_wifi = QPushButton('Save WiFi QR')
        self.generate_button_wifi.clicked.connect(self.generate_qr_code)
        export_section.addWidget(self.generate_button_wifi)

        layout.addLayout(export_section)
        layout.addStretch()

    def _update_password_enabled(self, security_choice):
        self.password_input.setEnabled(security_choice != 'None')

    def update_language_ui(self, t):
        self.ssid_label.setText(t.get('wifi_ssid', 'Network Name (SSID)'))
        self.password_label.setText(t.get('wifi_password', 'Password'))
        self.security_label.setText(t.get('wifi_security', 'Security Type'))
        self.hidden_check.setText(t.get('wifi_hidden', 'Hidden Network'))
        self.format_label_wifi.setText(t.get('export_format', 'Select Format:'))
        self.generate_button_wifi.setText(t.get('generate_button_wifi', 'Save WiFi QR'))

    def build_wifi_string(self):
        ssid = self.ssid_input.text().strip()
        password = self.password_input.text()
        security_choice = self.security_combo.currentText()
        hidden = 'true' if self.hidden_check.isChecked() else 'false'

        sec = {'WPA/WPA2': 'WPA', 'WEP': 'WEP'}.get(security_choice, 'nopass')

        parts = [f"WIFI:T:{sec}", f"S:{_wifi_escape(ssid)}"]
        if sec != 'nopass':
            parts.append(f"P:{_wifi_escape(password)}")
        parts.append(f"H:{hidden}")
        return ";".join(parts) + ";;"

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
                mw.show_toast(mw.success_qr_message)
        except Exception as e:
            logging.error("Error generating or saving WiFi QR: %s", e, exc_info=True)
            print(f"WIFI QR ERROR: {e}")
            mw.show_toast(mw.error_message, is_error=True)
