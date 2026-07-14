import os
import csv
import logging
import vobject
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QRadioButton, QButtonGroup, QLineEdit, QPushButton, QFileDialog)

from qr_generator.engine import make_custom_qr
from qr_generator.utils import sanitize_filename
from qr_generator.ui.tabs.wifi_tab import build_wifi_string
from qr_generator.ui.tabs.email_tab import build_email_uri


class BulkTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.bulk_error_missing = "Please select both a CSV file and an output folder."
        self.bulk_success_template = "Successfully generated {0} QR codes in {1}"

        self.bulk_layout = QVBoxLayout(self)
        self.bulk_layout.setContentsMargins(30, 30, 30, 30)
        self.bulk_layout.setSpacing(20)

        self.bulk_title = QLabel("Bulk QR Generation")
        self.bulk_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        self.bulk_layout.addWidget(self.bulk_title)

        self.bulk_desc = QLabel("Select a CSV file and output folder to generate multiple QR codes at once.")
        self.bulk_desc.setWordWrap(True)
        self.bulk_desc.setStyleSheet("color: #8e8e93; margin-bottom: 10px;")
        self.bulk_layout.addWidget(self.bulk_desc)

        type_layout = QHBoxLayout()
        self.bulk_type_label = QLabel("Data Type:")
        self.bulk_type_combo = QComboBox()
        self.bulk_type_combo.addItems(["URL", "VCard", "WiFi", "Email"])
        type_layout.addWidget(self.bulk_type_label)
        type_layout.addWidget(self.bulk_type_combo)
        type_layout.addStretch()
        self.bulk_layout.addLayout(type_layout)

        # Format selection
        self.format_label_bulk = QLabel('Select Format:')
        self.bulk_layout.addWidget(self.format_label_bulk)
        radio_layout = QHBoxLayout()
        self.png_radio_bulk = QRadioButton("PNG")
        self.svg_radio_bulk = QRadioButton("SVG")
        self.svg_radio_bulk.setChecked(True)
        self.radio_group_bulk = QButtonGroup()
        self.radio_group_bulk.addButton(self.png_radio_bulk)
        self.radio_group_bulk.addButton(self.svg_radio_bulk)
        radio_layout.addWidget(self.png_radio_bulk)
        radio_layout.addWidget(self.svg_radio_bulk)
        radio_layout.addStretch()
        self.bulk_layout.addLayout(radio_layout)

        self.csv_path_label = QLineEdit()
        self.csv_path_label.setPlaceholderText("Select CSV file...")
        self.csv_path_label.setReadOnly(True)
        self.select_csv_btn = QPushButton("Browse CSV")
        self.select_csv_btn.setFixedWidth(170)
        # Match the adjacent QLineEdit's height (38px) instead of the taller
        # global QPushButton default (42px) so the row lines up evenly.
        self.select_csv_btn.setStyleSheet("min-height: 38px; max-height: 38px;")
        self.select_csv_btn.clicked.connect(self.select_bulk_csv)

        csv_layout = QHBoxLayout()
        csv_layout.setSpacing(10)
        csv_layout.addWidget(self.csv_path_label)
        csv_layout.addWidget(self.select_csv_btn)
        self.bulk_layout.addLayout(csv_layout)

        self.output_path_label = QLineEdit()
        self.output_path_label.setPlaceholderText("Select output folder...")
        self.output_path_label.setReadOnly(True)
        self.select_output_btn = QPushButton("Browse Folder")
        self.select_output_btn.setFixedWidth(170)
        self.select_output_btn.setStyleSheet("min-height: 38px; max-height: 38px;")
        self.select_output_btn.clicked.connect(self.select_bulk_output)

        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)
        output_layout.addWidget(self.output_path_label)
        output_layout.addWidget(self.select_output_btn)
        self.bulk_layout.addLayout(output_layout)

        self.start_bulk_btn = QPushButton("Start Bulk Generation")
        self.start_bulk_btn.setObjectName("start_bulk_btn")
        self.start_bulk_btn.clicked.connect(self.run_bulk_generation)
        self.bulk_layout.addWidget(self.start_bulk_btn)

        self.download_template_btn = QPushButton("Download Example CSV")
        self.download_template_btn.setObjectName("download_template_btn")
        self.download_template_btn.clicked.connect(self.download_csv_template)
        self.bulk_layout.addWidget(self.download_template_btn)

    def update_language_ui(self, t):
        self.bulk_title.setText(t.get('bulk_title', 'Bulk QR Generation'))
        self.bulk_desc.setText(t.get('bulk_desc', 'Description text'))
        self.bulk_type_label.setText(t.get('bulk_type', 'Data Type:'))
        self.format_label_bulk.setText(t.get('export_format', 'Select Format:'))
        self.select_csv_btn.setText(t.get('browse_csv', 'Browse CSV'))
        self.select_output_btn.setText(t.get('browse_folder', 'Browse Folder'))
        self.start_bulk_btn.setText(t.get('start_bulk', 'Start Bulk Generation'))
        self.download_template_btn.setText(t.get('download_template', 'Download Example CSV'))
        self.bulk_error_missing = t.get('bulk_error_missing', 'Missing files.')
        self.bulk_success_template = t.get('bulk_success', 'Success.')

    def select_bulk_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if path:
            self.csv_path_label.setText(path)

    def select_bulk_output(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self.output_path_label.setText(path)

    def run_bulk_generation(self):
        mw = self.main_window
        csv_path = self.csv_path_label.text()
        output_dir = self.output_path_label.text()
        data_type = self.bulk_type_combo.currentText()

        if not csv_path or not output_dir:
            mw.show_toast(self.bulk_error_missing, is_error=True)
            return

        is_svg = self.svg_radio_bulk.isChecked()
        ext = ".svg" if is_svg else ".png"

        try:
            with open(csv_path, 'r', newline='', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                count = 0
                if data_type == "URL":
                    for row in reader:
                        if row:
                            url = row[0]
                            filename = f"{sanitize_filename(url)}_qrcode" + ext
                            img = make_custom_qr(url, fg_color=mw.fg_color, bg_color=mw.bg_color, is_transparent=mw.is_transparent, is_svg=is_svg, logo_path=mw.logo_path)
                            file_path = os.path.join(output_dir, filename)
                            img.save(file_path)
                            logging.info(f"Bulk saved URL QR: {file_path}")
                            count += 1
                elif data_type == "VCard":
                    for row in reader:
                        if len(row) >= 8:
                            vcard_obj = vobject.vCard()
                            fn = row[0] if len(row) > 0 else ""
                            ln = row[1] if len(row) > 1 else ""
                            org = row[2] if len(row) > 2 else ""
                            title = row[3] if len(row) > 3 else ""
                            email = row[4] if len(row) > 4 else ""
                            phone = row[5] if len(row) > 5 else ""
                            mobile = row[6] if len(row) > 6 else ""
                            url_vcard = row[7] if len(row) > 7 else ""

                            if fn or ln:
                                vcard_obj.add('fn').value = f"{fn} {ln}".strip()
                                vcard_obj.add('n').value = vobject.vcard.Name(family=ln, given=fn)
                                if org: vcard_obj.add('org').value = [org]
                                if title: vcard_obj.add('title').value = title
                                if email: vcard_obj.add('email').value = email
                                if phone:
                                    tel = vcard_obj.add('tel')
                                    tel.type_param = 'WORK'
                                    tel.value = phone
                                if mobile:
                                    tel = vcard_obj.add('tel')
                                    tel.type_param = 'CELL'
                                    tel.value = mobile
                                if url_vcard: vcard_obj.add('url').value = url_vcard

                                vcard_text = vcard_obj.serialize()
                                name_for_file = f"{fn}_{ln}".strip('_') if fn or ln else f"vcard_{count}"
                                filename = f"{sanitize_filename(name_for_file)}_vcard" + ext
                                img = make_custom_qr(vcard_text, fg_color=mw.fg_color, bg_color=mw.bg_color, is_transparent=mw.is_transparent, is_svg=is_svg, logo_path=mw.logo_path)
                                file_path = os.path.join(output_dir, filename)
                                img.save(file_path)
                                logging.info(f"Bulk saved VCard QR: {file_path}")
                                count += 1
                elif data_type == "WiFi":
                    for row in reader:
                        if row:
                            ssid = row[0] if len(row) > 0 else ""
                            password = row[1] if len(row) > 1 else ""
                            security = row[2] if len(row) > 2 else "WPA/WPA2"
                            hidden = row[3].strip().lower() in ("true", "1", "yes") if len(row) > 3 else False

                            if ssid:
                                wifi_data = build_wifi_string(ssid, password, security, hidden)
                                filename = f"{sanitize_filename(ssid)}_wifi" + ext
                                img = make_custom_qr(wifi_data, fg_color=mw.fg_color, bg_color=mw.bg_color, is_transparent=mw.is_transparent, is_svg=is_svg, logo_path=mw.logo_path)
                                file_path = os.path.join(output_dir, filename)
                                img.save(file_path)
                                logging.info(f"Bulk saved WiFi QR: {file_path}")
                                count += 1
                else: # Email
                    for row in reader:
                        if row:
                            to = row[0] if len(row) > 0 else ""
                            subject = row[1] if len(row) > 1 else ""
                            message = row[2] if len(row) > 2 else ""

                            if to:
                                email_uri = build_email_uri(to, subject, message)
                                filename = f"{sanitize_filename(to)}_email" + ext
                                img = make_custom_qr(email_uri, fg_color=mw.fg_color, bg_color=mw.bg_color, is_transparent=mw.is_transparent, is_svg=is_svg, logo_path=mw.logo_path)
                                file_path = os.path.join(output_dir, filename)
                                img.save(file_path)
                                logging.info(f"Bulk saved Email QR: {file_path}")
                                count += 1

                mw.show_toast(self.bulk_success_template.format(count, output_dir))
                logging.info(f"Bulk generation finished. Created {count} files in {output_dir}")
        except Exception as e:
            logging.error(f"Bulk generation error: {e}", exc_info=True)
            mw.show_toast(f"An error occurred: {e}", is_error=True)

    def download_csv_template(self):
        mw = self.main_window
        data_type = self.bulk_type_combo.currentText()
        if data_type == "URL":
            default_name = "url_template.csv"
            headers = ["URL"]
            sample_data = [["https://google.com"]]
        elif data_type == "VCard":
            default_name = "vcard_template.csv"
            headers = ["First Name", "Last Name", "Organization", "Title", "Email", "Phone", "Mobile Phone", "URL"]
            sample_data = [["John", "Doe", "ACME", "CEO", "john@example.com", "123", "456", "http://john.com"]]
        elif data_type == "WiFi":
            default_name = "wifi_template.csv"
            headers = ["SSID", "Password", "Security", "Hidden"]
            sample_data = [["MyHomeWiFi", "supersecret123", "WPA/WPA2", "false"]]
        else: # Email
            default_name = "email_template.csv"
            headers = ["To", "Subject", "Message"]
            sample_data = [["john@example.com", "Hello", "This is a sample message."]]

        path, _ = QFileDialog.getSaveFileName(self, "Save Template", default_name, "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                    writer.writerow(headers)
                    writer.writerows(sample_data)
                mw.show_toast(mw.success_qr_message)
            except Exception as e:
                mw.show_toast(f"Could not save template: {e}", is_error=True)
