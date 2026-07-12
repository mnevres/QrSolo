import logging
import vobject
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel,
                             QLineEdit, QRadioButton, QButtonGroup, QPushButton, QFileDialog)
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp

from qr_generator.engine import make_custom_qr
from qr_generator.utils import sanitize_filename


class VCardTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.editing_vcard_id = None

        self.tab_hlayout = QHBoxLayout(self)
        self.tab_hlayout.setContentsMargins(0, 0, 0, 0)
        self.tab_hlayout.setSpacing(0)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.fn_label = QLabel('First Name')
        self.ln_label = QLabel('Last Name')
        self.org_label = QLabel('Organization')
        self.title_label = QLabel('Title')
        self.email_label = QLabel('Email')
        self.phone_label = QLabel('Phone')
        self.mobile_label = QLabel('Mobile Phone')
        self.url_vcard_label = QLabel('Url/WebSite')

        self.fn_input = QLineEdit()
        self.ln_input = QLineEdit()
        self.org_input = QLineEdit()
        self.title_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.mobile_input = QLineEdit()
        self.url_input_vcard = QLineEdit()

        phone_validator = QRegExpValidator(QRegExp(r'[0-9 +]*'))
        self.phone_input.setValidator(phone_validator)
        self.mobile_input.setValidator(phone_validator)

        form_layout.addRow(self.fn_label, self.fn_input)
        form_layout.addRow(self.ln_label, self.ln_input)
        form_layout.addRow(self.org_label, self.org_input)
        form_layout.addRow(self.title_label, self.title_input)
        form_layout.addRow(self.email_label, self.email_input)
        form_layout.addRow(self.phone_label, self.phone_input)
        form_layout.addRow(self.mobile_label, self.mobile_input)
        form_layout.addRow(self.url_vcard_label, self.url_input_vcard)
        layout.addLayout(form_layout)

        export_section = QVBoxLayout()
        self.format_label_vcard = QLabel('Select Format:')
        export_section.addWidget(self.format_label_vcard)

        radio_layout = QHBoxLayout()
        self.png_radio_vcard = QRadioButton("PNG")
        self.svg_radio_vcard = QRadioButton("SVG")
        self.svg_radio_vcard.setChecked(True)
        self.radio_group_vcard = QButtonGroup()
        self.radio_group_vcard.addButton(self.png_radio_vcard)
        self.radio_group_vcard.addButton(self.svg_radio_vcard)
        radio_layout.addWidget(self.png_radio_vcard)
        radio_layout.addWidget(self.svg_radio_vcard)
        radio_layout.addStretch()
        export_section.addLayout(radio_layout)

        vcard_buttons_layout = QHBoxLayout()
        self.generate_button_vcard = QPushButton('Save VCard')
        self.generate_button_vcard.clicked.connect(self.generate_vcard_qr_code)
        vcard_buttons_layout.addWidget(self.generate_button_vcard, stretch=1)

        self.clear_vcard_btn = QPushButton('New VCard')
        self.clear_vcard_btn.setObjectName("clear_vcard_btn")
        self.clear_vcard_btn.clicked.connect(self.clear_vcard_form)
        vcard_buttons_layout.addWidget(self.clear_vcard_btn)

        export_section.addLayout(vcard_buttons_layout)

        layout.addLayout(export_section)
        layout.addStretch()

        self.tab_hlayout.addWidget(content_widget, stretch=1)

        self.fn_input.textChanged.connect(self.main_window.update_preview)
        self.ln_input.textChanged.connect(self.main_window.update_preview)
        self.org_input.textChanged.connect(self.main_window.update_preview)
        self.title_input.textChanged.connect(self.main_window.update_preview)
        self.email_input.textChanged.connect(self.main_window.update_preview)
        self.phone_input.textChanged.connect(self.main_window.update_preview)
        self.mobile_input.textChanged.connect(self.main_window.update_preview)
        self.url_input_vcard.textChanged.connect(self.main_window.update_preview)

    def update_language_ui(self, t):
        self.fn_label.setText(t.get('first_name', 'First Name'))
        self.ln_label.setText(t.get('last_name', 'Last Name'))
        self.org_label.setText(t.get('organization', 'Organization'))
        self.title_label.setText(t.get('title', 'Title'))
        self.email_label.setText(t.get('email', 'Email'))
        self.phone_label.setText(t.get('phone', 'Phone'))
        self.mobile_label.setText(t.get('mobile_phone', 'Mobile Phone'))
        self.url_vcard_label.setText(t.get('url_website', 'Url/WebSite'))
        self.format_label_vcard.setText(t.get('export_format', 'Select Format:'))
        self.generate_button_vcard.setText(t.get('generate_button_vcard', 'Generate VCard'))
        self.clear_vcard_btn.setText(t.get('new_vcard_button', 'New VCard'))

    def generate_vcard_qr_code(self):
        mw = self.main_window
        try:
            fn, ln = self.fn_input.text().strip(), self.ln_input.text().strip()
            org = self.org_input.text().strip()
            title = self.title_input.text().strip()
            email = self.email_input.text().strip()
            phone = self.phone_input.text().strip()
            mobile = self.mobile_input.text().strip()
            url_vcard = self.url_input_vcard.text().strip()

            if not fn and not ln:
                mw.show_toast(mw.vcard_error_message, is_error=True)
                return

            vcard = vobject.vCard()
            vcard.add('fn').value = f"{fn} {ln}".strip()
            vcard.add('n').value = vobject.vcard.Name(family=ln, given=fn)
            if org: vcard.add('org').value = [org]
            if title: vcard.add('title').value = title
            if email: vcard.add('email').value = email
            if phone:
                tel = vcard.add('tel')
                tel.type_param = 'WORK'
                tel.value = phone
            if mobile:
                tel = vcard.add('tel')
                tel.type_param = 'CELL'
                tel.value = mobile
            if url_vcard: vcard.add('url').value = url_vcard

            vcard_text = vcard.serialize()

            is_svg = not self.png_radio_vcard.isChecked()
            mw.qr_img = make_custom_qr(vcard_text, fg_color=mw.fg_color, bg_color=mw.bg_color, is_transparent=mw.is_transparent, is_svg=is_svg, size=mw.img_size)

            filename = f"{sanitize_filename(fn + '_' + ln)}_vcard" + (".svg" if is_svg else ".png")
            file_type = "SVG Files (*.svg)" if is_svg else "PNG Files (*.png)"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save VCard", filename, file_type)
            if file_path:
                mw.qr_img.save(file_path)
                full_name = " ".join(f"{fn} {ln}".split()) # Normalize spaces
                if self.editing_vcard_id is not None:
                    mw.db.update_vcard(self.editing_vcard_id, full_name, fn, ln, org, title, email, phone, mobile, url_vcard, vcard_text)
                else:
                    self.editing_vcard_id = mw.db.add_vcard(full_name, fn, ln, org, title, email, phone, mobile, url_vcard, vcard_text)
                mw.vcard_archive_window.load_archive()
                mw.populate_sidebar()
                mw.show_toast(mw.success_vcard_message)
        except Exception as e:
            logging.error("Error generating or saving VCard: %s", e, exc_info=True)
            print(f"VCARD ERROR: {e}")
            mw.show_toast(mw.error_message, is_error=True)

    def clear_vcard_form(self):
        self.editing_vcard_id = None
        self.fn_input.clear()
        self.ln_input.clear()
        self.org_input.clear()
        self.title_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.mobile_input.clear()
        self.url_input_vcard.clear()
        self.main_window.update_preview()

    def load_vcard(self, vcard_id, name, fn, ln, org, title, email, phone, mobile, url, vcard):
        self.editing_vcard_id = vcard_id
        self.fn_input.setText(fn)
        self.ln_input.setText(ln)
        self.org_input.setText(org)
        self.title_input.setText(title)
        self.email_input.setText(email)
        self.phone_input.setText(phone)
        self.mobile_input.setText(mobile)
        self.url_input_vcard.setText(url)
        self.main_window.update_preview()
