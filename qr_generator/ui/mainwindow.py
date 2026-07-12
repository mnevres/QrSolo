import os
import sys
import logging
import json
import csv
import vobject
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QFrame, QLabel, QMenuBar, QAction,
                             QLineEdit, QRadioButton, QButtonGroup, QFormLayout,
                             QPushButton, QComboBox, QFileDialog, QApplication,
                             QListWidget, QListWidgetItem)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QRegExpValidator, QImage
from PyQt5.QtCore import Qt, QRegExp

from qr_generator.database import Database
from qr_generator.engine import make_custom_qr
from qr_generator.utils import sanitize_filename, resource_path
from qr_generator.ui.widgets import ToastNotification
from qr_generator.ui.dialogs import SettingsWindow, URLArchiveWindow, VCardArchiveWindow, AboutWindow

class QRCodeGenerator(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('QR Code Generator')
        self.setMinimumSize(1000, 600)
        self.resize(1000, 650)
        self.setWindowIcon(QIcon(resource_path('icon.png')))
        self.center()

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.setCentralWidget(self.main_widget)

        # Move Sidebar and Preview logic but don't add to main_layout yet
        self.sidebar_container = QFrame(self)
        self.sidebar_container.setObjectName("sidebar_container")
        self.sidebar_container.setFrameShape(QFrame.StyledPanel)
        self.sidebar_container.setFixedWidth(280)
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        
        self.sidebar_title = QLabel("Saved Items")
        self.sidebar_title.setStyleSheet("font-weight: bold; color: #8e8e93; margin-bottom: 5px;")
        self.sidebar_layout.addWidget(self.sidebar_title)

        self.sidebar_search = QLineEdit()
        self.sidebar_search.setPlaceholderText("Search...")
        self.sidebar_search.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                margin-bottom: 5px;
                min-height: 44px;
                border: 1px solid transparent;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
                background-color: rgba(255, 255, 255, 0.12);
            }
        """)
        self.sidebar_search.textChanged.connect(self.filter_sidebar)
        self.sidebar_layout.addWidget(self.sidebar_search)
        
        self.sidebar_list = QListWidget()
        self.sidebar_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sidebar_list.customContextMenuRequested.connect(self.show_sidebar_context_menu)
        self.sidebar_list.itemClicked.connect(self.load_from_sidebar)
        self.sidebar_layout.addWidget(self.sidebar_list)

        # Middle part: Tabs (Now spans full width)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Right side: Preview logic (Not added to layout yet)
        self.preview_container = QFrame(self)
        self.preview_container.setObjectName("preview_container")
        self.preview_container.setFrameShape(QFrame.StyledPanel)
        self.preview_layout = QVBoxLayout(self.preview_container)
        
        self.preview_title = QLabel("Preview")
        self.preview_title.setAlignment(Qt.AlignCenter)
        self.preview_layout.addWidget(self.preview_title)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(250, 250)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setObjectName("preview_qr_label")
        self.preview_layout.addWidget(self.preview_label)

        self.preview_placeholder = "Preview\nArea" 
        
        self.url_tab = QWidget()
        self.vcard_tab = QWidget()
        self.bulk_tab = QWidget()

        self.tabs.addTab(self.url_tab, "URL")
        self.tabs.addTab(self.vcard_tab, "VCard")
        self.tabs.addTab(self.bulk_tab, "Bulk")

        # Add buttons
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        archive_action = QAction('Archive', self)
        archive_action.triggered.connect(self.open_archive)
        menu_bar.addAction(archive_action)

        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.open_settings)
        menu_bar.addAction(settings_action)
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.open_about)
        menu_bar.addAction(about_action)

        self.init_url_tab()
        self.init_vcard_tab()
        self.init_bulk_tab()
        
        # Now connect tab signal after tabs are ready
        self.tabs.currentChanged.connect(self.update_preview)

        self.db = Database()
        self.img_size = 1000
        self.qr_img = None
        self.editing_vcard_id = None
        self.show_sidebar = True
        self.translations = {}
        self.load_translations()

        # Initialize translation attributes with defaults to prevent AttributeErrors
        self.success_language_message = "Language set successfully."
        self.success_resolution_message = "Resolution set successfully."
        self.success_qr_message = "QR Code saved successfully."
        self.success_vcard_message = "VCard saved successfully."
        self.input_error_message = "Please enter a valid number between 100 and 2000."
        self.url_error_message = "Please enter a URL."
        self.vcard_error_message = "Please enter first and last name."
        self.error_message = "An error occurred."
        self.duplicate_vcard_message = "This VCard already exists in the archive."
        self.bulk_error_missing = "Please select both a CSV file and an output folder."
        self.bulk_success_template = "Successfully generated {0} QR codes in {1}"
        self.success_export_message = "Archive exported successfully."
        self.success_import_done_message = "Archive imported successfully."

        self.url_archive_window = URLArchiveWindow(self)
        self.vcard_archive_window = VCardArchiveWindow(self)
        self.settings_window = SettingsWindow(self)
        self.about_window = AboutWindow(self)

        self.apply_styles()

        # Load settings
        self.load_settings()
        
        # Ensure at least one language is set if load_settings didn't do it
        if not hasattr(self, 'current_language'):
            self.set_language('English')
            
        # Initial Preview
        self.update_preview()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0b0c;
            }
            QTabWidget {
                background-color: transparent;
                border: none;
            }
            QTabWidget::pane {
                border: 1px solid #1e1e24;
                background-color: #141417;
                border-radius: 20px;
                margin-top: 10px;
            }
            QTabBar {
                background-color: #1a1a1e;
                border-radius: 12px;
            }
            QTabBar::tab {
                background: transparent;
                color: #a1a1a6;
                padding: 14px 28px;
                font-weight: 700;
                font-size: 15px;
                border-radius: 10px;
                margin: 4px;
                min-width: 110px;
            }
            QTabBar::tab:hover {
                color: #ffffff;
                background-color: #25252a;
            }
            QTabBar::tab:selected {
                background-color: #2c2c31;
                color: #007AFF;
                border: 1px solid #3c3c43;
            }
            QTabBar QToolButton {
                width: 0px;
                height: 0px;
            }
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QRadioButton {
                color: #ffffff;
                font-size: 14px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            #preview_title {
                color: #ffffff;
                font-size: 24px;
                font-weight: 800;
                margin-bottom: 25px;
            }
            #preview_qr_label {
                border: 2px solid #28282e;
                background: #09090b;
                border-radius: 15px;
            }
            QLineEdit {
                background-color: #1c1c1e;
                color: #ffffff;
                border: 1px solid #2c2c2e;
                padding: 0px 12px;
                border-radius: 10px;
                font-size: 14px;
                min-height: 38px;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
                background-color: #222226;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #007AFF, stop:1 #0056b3);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 5px 20px;
                border-radius: 10px;
                font-weight: 600;
                font-size: 14px;
                min-height: 42px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a8bff, stop:1 #006aff);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background: #004a99;
                padding-top: 12px;
            }
            QDialog, QMessageBox {
                background-color: #1c1c1e;
                color: #ffffff;
            }
            QMessageBox QPushButton {
                min-height: 32px;
                min-width: 80px;
                font-size: 12px;
                padding: 5px 15px;
                background: #2c2c2e;
                border: 1px solid #3a3a3c;
                border-radius: 8px;
            }
            QMessageBox QPushButton:hover {
                background: #3a3a3c;
            }
            QMessageBox QLabel {
                font-size: 14px;
                padding: 10px;
                color: #ffffff;
            }
            #sidebar_container, #preview_container {
                background-color: #141417;
                border: 1px solid #1e1e24;
                border-radius: 20px;
                margin: 5px;
                padding: 20px;
            }
            #preview_container {
                padding: 30px;
            }
            QMenuBar {
                background-color: #0b0b0c;
                color: #ffffff;
                padding: 12px;
                font-weight: 600;
                font-size: 14px;
                border-bottom: 1px solid #1e1e24;
            }
            QMenuBar::item {
                padding: 8px 16px;
                border-radius: 8px;
            }
            QMenuBar::item:selected {
                background-color: #1c1c1e;
                color: white;
            }
            QComboBox {
                background-color: #1c1c1e;
                color: white;
                border: 1px solid #2c2c2e;
                border-radius: 10px;
                padding: 0px 12px;
                min-width: 140px;
                min-height: 38px;
                font-size: 14px;
            }
            QComboBox QAbstractItemView {
                background-color: #1c1c1e;
                color: #ffffff;
                border: 1px solid #2c2c2e;
                selection-background-color: #007AFF;
                outline: none;
            }
            #start_bulk_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #32d74b, stop:1 #248a3d);
                min-height: 44px;
            }
            #start_bulk_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3af25c, stop:1 #2bb24e);
            }
            #download_template_btn {
                background: #2c2c2e;
                color: #007AFF;
                border: 1px solid #3a3a3c;
                min-height: 36px;
                font-size: 13px;
            }
            #download_template_btn:hover {
                background: #3a3a3c;
                color: #ffffff;
            }
            #clear_vcard_btn {
                background: #2c2c2e;
                color: #007AFF;
                border: 1px solid #3a3a3c;
                min-width: 90px;
            }
            #clear_vcard_btn:hover {
                background: #3a3a3c;
                color: #ffffff;
            }
        """)
        self.tabs.setUsesScrollButtons(False)
        self.tabs.setDocumentMode(False)
        self.sidebar_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 8px;
                color: #e0e0e0;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 2px;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QListWidget::item:selected {
                background-color: #007aff;
                color: white;
            }
        """)
        self.preview_container.setObjectName("preview_container")
        self.preview_title.setObjectName("preview_title")

    def show_toast(self, message, is_error=False):
        color = "#ff453a" if is_error else "#32d74b"
        toast = ToastNotification(self, message, color=color)
        toast.show_toast()

    def load_translations(self):
        try:
            # Look for translations.json in the project root
            # Assume it's in the same directory as the script or project root
            # Since we'll run from root, this relative path is fine.
            with open(resource_path('translations.json'), 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except Exception as e:
            logging.error("Error loading translations: %s", e)

    def load_settings(self):
        settings = self.db.get_settings()
        if settings:
            self.current_language = settings[0] if settings[0] else 'English'
            self.img_size = settings[1] if settings[1] else 1000
            self.fg_color = settings[2] if len(settings) > 2 and settings[2] else "#000000"
            self.bg_color = settings[3] if len(settings) > 3 and settings[3] else "#ffffff"
            self.is_transparent = bool(settings[4]) if len(settings) > 4 else False
            self.show_sidebar = bool(settings[5]) if len(settings) > 5 else True
        else:
            self.current_language = 'English'
            self.img_size = 1000
            self.fg_color = "#000000"
            self.bg_color = "#ffffff"
            self.is_transparent = False
            self.show_sidebar = True
        
        self.set_language(self.current_language)
        self.update_sidebar_visibility()

    def set_language(self, language):
        self.current_language = language
        t = self.translations.get(language, self.translations.get('English', {}))
        if not t:
            return

        try:
            self.setWindowTitle(t.get('window_title', 'QR Code Generator'))
            self.tabs.setTabText(0, t.get('url_tab', 'URL'))
            self.tabs.setTabText(1, t.get('vcard_tab', 'VCard'))
            self.tabs.setTabText(2, t.get('bulk_tab', 'Bulk'))
            
            self.url_label.setText(t.get('enter_url', 'Enter URL:'))
            format_text = t.get('export_format', 'Select Format:')
            if hasattr(self, 'format_label_url'): self.format_label_url.setText(format_text)
            if hasattr(self, 'format_label_vcard'): self.format_label_vcard.setText(format_text)
            if hasattr(self, 'format_label_bulk'): self.format_label_bulk.setText(format_text)
            
            self.sidebar_search.setPlaceholderText(t.get('search_placeholder', 'Search...'))
            self.populate_sidebar()
            self.generate_button_url.setText(t.get('generate_button_url', 'Export QR Code'))

            self.fn_label.setText(t.get('first_name', 'First Name'))
            self.ln_label.setText(t.get('last_name', 'Last Name'))
            self.org_label.setText(t.get('organization', 'Organization'))
            self.title_label.setText(t.get('title', 'Title'))
            self.email_label.setText(t.get('email', 'Email'))
            self.phone_label.setText(t.get('phone', 'Phone'))
            self.mobile_label.setText(t.get('mobile_phone', 'Mobile Phone'))
            self.url_vcard_label.setText(t.get('url_website', 'Url/WebSite'))
            self.generate_button_vcard.setText(t.get('generate_button_vcard', 'Generate VCard'))
            self.clear_vcard_btn.setText(t.get('new_vcard_button', 'New VCard'))

            self.bulk_title.setText(t.get('bulk_title', 'Bulk QR Generation'))
            self.bulk_desc.setText(t.get('bulk_desc', 'Description text'))
            self.bulk_type_label.setText(t.get('bulk_type', 'Data Type:'))
            self.select_csv_btn.setText(t.get('browse_csv', 'Browse CSV'))
            self.select_output_btn.setText(t.get('browse_folder', 'Browse Folder'))
            self.start_bulk_btn.setText(t.get('start_bulk', 'Start Bulk Generation'))
            self.bulk_error_missing = t.get('bulk_error_missing', 'Missing files.')
            self.bulk_success_template = t.get('bulk_success', 'Success.')

            self.success_language_message = t.get('success_language', 'Language set.')
            self.success_resolution_message = t.get('success_resolution', 'Resolution set.')
            self.success_qr_message = t.get('success_qr', 'QR saved.')
            self.success_vcard_message = t.get('success_vcard', 'VCard saved.')
            self.input_error_message = t.get('input_error', 'Invalid input.')
            self.url_error_message = t.get('url_error', 'Enter URL.')
            self.vcard_error_message = t.get('vcard_error', 'Enter name.')
            self.error_message = t.get('error_generic', 'Error.')
            self.duplicate_vcard_message = t.get('duplicate_vcard', 'Duplicate.')

            # Update Menu titles
            actions = self.menuBar().actions()
            if len(actions) > 0: actions[0].setText(t.get('archive', 'Archive'))
            if len(actions) > 1: actions[1].setText(t.get('settings', 'Settings'))
            if len(actions) > 2: actions[2].setText(t.get('about', 'About'))

            # Update archive windows manually
            if hasattr(self, 'url_archive_window'):
                self.url_archive_window.setWindowTitle(t.get('url_archive_title', 'URL Archive'))
                self.url_archive_window.get_button.setText(t.get('retrieve_from_archive', 'Retrieve'))
                self.url_archive_window.delete_button.setText(t.get('delete', 'Delete'))
            
            if hasattr(self, 'settings_window'): self.settings_window.update_language_ui(language)
            if hasattr(self, 'about_window'): self.about_window.update_language_ui(language)

            self.preview_title.setText(t.get('preview', 'Preview'))
        except Exception as e:
            logging.error(f"Error in set_language: {e}")

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_url_tab(self):
        self.url_tab_hlayout = QHBoxLayout(self.url_tab)
        self.url_tab_hlayout.setContentsMargins(0, 0, 0, 0)
        self.url_tab_hlayout.setSpacing(0)

        # Content area
        self.url_content_widget = QWidget()
        layout = QVBoxLayout(self.url_content_widget)
        layout.setContentsMargins(30,30,30,30)
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
        
        self.url_tab_hlayout.addWidget(self.url_content_widget, stretch=1)
        
        self.url_input.textChanged.connect(self.update_preview)

    def init_bulk_tab(self):
        self.bulk_layout = QVBoxLayout(self.bulk_tab)
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
        self.bulk_type_combo.addItems(["URL", "VCard"])
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

    def select_bulk_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if path:
            self.csv_path_label.setText(path)

    def select_bulk_output(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self.output_path_label.setText(path)

    def run_bulk_generation(self):
        csv_path = self.csv_path_label.text()
        output_dir = self.output_path_label.text()
        data_type = self.bulk_type_combo.currentText()

        if not csv_path or not output_dir:
            self.show_toast(self.bulk_error_missing, is_error=True)
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
                            img = make_custom_qr(url, fg_color=self.fg_color, bg_color=self.bg_color, is_transparent=self.is_transparent, is_svg=is_svg)
                            file_path = os.path.join(output_dir, filename)
                            img.save(file_path)
                            logging.info(f"Bulk saved URL QR: {file_path}")
                            count += 1
                else: # VCard
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
                                img = make_custom_qr(vcard_text, fg_color=self.fg_color, bg_color=self.bg_color, is_transparent=self.is_transparent, is_svg=is_svg)
                                file_path = os.path.join(output_dir, filename)
                                img.save(file_path)
                                logging.info(f"Bulk saved VCard QR: {file_path}")
                                count += 1
                
                self.show_toast(self.bulk_success_template.format(count, output_dir))
                logging.info(f"Bulk generation finished. Created {count} files in {output_dir}")
        except Exception as e:
            logging.error(f"Bulk generation error: {e}", exc_info=True)
            self.show_toast(f"An error occurred: {e}", is_error=True)

    def download_csv_template(self):
        data_type = self.bulk_type_combo.currentText()
        if data_type == "URL":
            default_name = "url_template.csv"
            headers = ["URL"]
            sample_data = [["https://google.com"]]
        else:
            default_name = "vcard_template.csv"
            headers = ["First Name", "Last Name", "Organization", "Title", "Email", "Phone", "Mobile Phone", "URL"]
            sample_data = [["John", "Doe", "ACME", "CEO", "john@example.com", "123", "456", "http://john.com"]]

        path, _ = QFileDialog.getSaveFileName(self, "Save Template", default_name, "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(sample_data)
                self.show_toast(self.success_qr_message)
            except Exception as e:
                self.show_toast(f"Could not save template: {e}", is_error=True)

    def init_vcard_tab(self):
        self.vcard_tab_hlayout = QHBoxLayout(self.vcard_tab)
        self.vcard_tab_hlayout.setContentsMargins(0, 0, 0, 0)
        self.vcard_tab_hlayout.setSpacing(0)

        # Content area
        self.vcard_content_widget = QWidget()
        layout = QVBoxLayout(self.vcard_content_widget)
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
        
        self.vcard_tab_hlayout.addWidget(self.vcard_content_widget, stretch=1)

        self.fn_input.textChanged.connect(self.update_preview)
        self.ln_input.textChanged.connect(self.update_preview)
        self.org_input.textChanged.connect(self.update_preview)
        self.title_input.textChanged.connect(self.update_preview)
        self.email_input.textChanged.connect(self.update_preview)
        self.phone_input.textChanged.connect(self.update_preview)
        self.mobile_input.textChanged.connect(self.update_preview)
        self.url_input_vcard.textChanged.connect(self.update_preview)

    def generate_qr_code(self):
        try:
            url_text = self.url_input.text()
            if not url_text:
                self.show_toast(self.url_error_message, is_error=True)
                return

            is_svg = not self.png_radio_url.isChecked()
            self.qr_img = make_custom_qr(url_text, fg_color=self.fg_color, bg_color=self.bg_color, is_transparent=self.is_transparent, is_svg=is_svg, size=self.img_size)

            filename = f"{sanitize_filename(url_text)}_qr" + (".svg" if is_svg else ".png")
            file_type = "SVG Files (*.svg)" if is_svg else "PNG Files (*.png)"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save QR", filename, file_type)
            if file_path:
                self.qr_img.save(file_path)
                self.db.add_url(url_text)
                self.url_archive_window.load_archive()
                self.populate_sidebar() # Ensure sidebar updates
                self.show_toast(self.success_qr_message)
        except Exception as e:
            logging.error("Error generating or saving QR: %s", e, exc_info=True)
            print(f"QR ERROR: {e}")
            self.show_toast(self.error_message, is_error=True)

    def generate_vcard_qr_code(self):
        try:
            fn, ln = self.fn_input.text().strip(), self.ln_input.text().strip()
            org = self.org_input.text().strip()
            title = self.title_input.text().strip()
            email = self.email_input.text().strip()
            phone = self.phone_input.text().strip()
            mobile = self.mobile_input.text().strip()
            url_vcard = self.url_input_vcard.text().strip()

            if not fn and not ln:
                self.show_toast(self.vcard_error_message, is_error=True)
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
            self.qr_img = make_custom_qr(vcard_text, fg_color=self.fg_color, bg_color=self.bg_color, is_transparent=self.is_transparent, is_svg=is_svg, size=self.img_size)

            filename = f"{sanitize_filename(fn + '_' + ln)}_vcard" + (".svg" if is_svg else ".png")
            file_type = "SVG Files (*.svg)" if is_svg else "PNG Files (*.png)"
            file_path, _ = QFileDialog.getSaveFileName(self, "Save VCard", filename, file_type)
            if file_path:
                self.qr_img.save(file_path)
                full_name = " ".join(f"{fn} {ln}".split()) # Normalize spaces
                if self.editing_vcard_id is not None:
                    self.db.update_vcard(self.editing_vcard_id, full_name, fn, ln, org, title, email, phone, mobile, url_vcard, vcard_text)
                else:
                    self.editing_vcard_id = self.db.add_vcard(full_name, fn, ln, org, title, email, phone, mobile, url_vcard, vcard_text)
                self.vcard_archive_window.load_archive()
                self.populate_sidebar()
                self.show_toast(self.success_vcard_message)
        except Exception as e:
            logging.error("Error generating or saving VCard: %s", e, exc_info=True)
            print(f"VCARD ERROR: {e}")
            self.show_toast(self.error_message, is_error=True)

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
        self.update_preview()

    def _get_checkerboard_pattern(self, size=240):
        tile_size = 10
        pixmap = QPixmap(size, size)
        painter = QPainter(pixmap)
        color1, color2 = QColor(220, 220, 220), QColor(255, 255, 255)
        for y in range(0, size, tile_size):
            for x in range(0, size, tile_size):
                painter.fillRect(x, y, tile_size, tile_size, color1 if (x//tile_size + y//tile_size)%2==0 else color2)
        painter.end()
        return pixmap

    def update_preview(self):
        try:
            tab = self.tabs.currentIndex()
            self.update_sidebar_visibility()
            
            if tab == 2:
                return
            
            self.populate_sidebar()
                
            data = self.url_input.text().strip() if tab==0 else f"BEGIN:VCARD\nFN:{self.fn_input.text()} {self.ln_input.text()}\nEND:VCARD"
            if not data.strip() or data == "BEGIN:VCARD\nFN: \nEND:VCARD":
                self.preview_label.clear()
                self.preview_label.setText(self.preview_placeholder)
                return

            img = make_custom_qr(data, fg_color=self.fg_color, bg_color=self.bg_color, is_transparent=self.is_transparent, is_svg=False, size=240)
            if self.is_transparent:
                qimg = QImage(img.tobytes("raw", "RGBA"), img.size[0], img.size[1], QImage.Format_RGBA8888)
                base = self._get_checkerboard_pattern(240)
                p = QPainter(base)
                p.drawPixmap(0,0, QPixmap.fromImage(qimg))
                p.end()
                self.preview_label.setPixmap(base)
            else:
                img = img.convert("RGB")
                qimg = QImage(img.tobytes("raw", "RGB"), img.size[0], img.size[1], QImage.Format_RGB888)
                self.preview_label.setPixmap(QPixmap.fromImage(qimg))
        except Exception as e:
            logging.error(f"Preview error: {e}")

    def open_archive(self): 
        (self.open_url_archive if self.tabs.currentIndex()==0 else self.open_vcard_archive)()
    def open_url_archive(self): self.url_archive_window.load_archive(); self.url_archive_window.show()
    def open_vcard_archive(self): self.vcard_archive_window.load_archive(); self.vcard_archive_window.show()
    def open_settings(self): self.settings_window.show()
    def open_about(self): self.about_window.show()
    def load_url(self, url): 
        self.url_input.setText(url)
        self.update_preview()

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
        self.update_preview()

    def filter_sidebar(self):
        search_text = self.sidebar_search.text().lower()
        for i in range(self.sidebar_list.count()):
            item = self.sidebar_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def update_sidebar_visibility(self):
        tab = self.tabs.currentIndex()
        is_visible = self.show_sidebar and tab != 2
        
        if is_visible:
            # Move shared widgets to current tab's horizontal layout
            target_layout = self.url_tab_hlayout if tab == 0 else self.vcard_tab_hlayout
            
            # Re-insert into layout if missing or moved
            if target_layout.indexOf(self.sidebar_container) == -1:
                target_layout.insertWidget(0, self.sidebar_container)
            if target_layout.indexOf(self.preview_container) == -1:
                target_layout.addWidget(self.preview_container)
            
            self.sidebar_container.show()
            self.preview_container.show()
            self.populate_sidebar()
        else:
            self.sidebar_container.hide()
            self.preview_container.hide()

    def populate_sidebar(self):
        self.sidebar_list.clear()
        tab = self.tabs.currentIndex()
        t = self.translations.get(self.current_language, self.translations.get('English', {}))
        
        if tab == 0: # URL
            self.sidebar_title.setText(t.get('url_archive_list', 'Saved URLs'))
            urls = self.db.get_urls()
            for url_row in urls:
                self.sidebar_list.addItem(url_row[0])
        elif tab == 1: # VCard
            self.sidebar_title.setText(t.get('vcard_archive_list', 'Saved VCards'))
            vcards = self.db.get_vcards()
            for vcard_row in vcards:
                item = QListWidgetItem(vcard_row[1]) # name
                item.setData(Qt.UserRole, vcard_row[0]) # id
                self.sidebar_list.addItem(item)
        
        self.filter_sidebar() # Re-apply search filter if any

    def load_from_sidebar(self, item):
        tab = self.tabs.currentIndex()
        if tab == 0:
            self.url_input.setText(item.text())
            self.update_preview()
        elif tab == 1:
            vcard_id = item.data(Qt.UserRole)
            vcards = self.db.get_vcards()
            for v in vcards:
                if v[0] == vcard_id:
                    self.load_vcard(*v)
                    break

    def show_sidebar_context_menu(self, pos):
        item = self.sidebar_list.itemAt(pos)
        if not item:
            return
        
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        t = self.translations.get(self.current_language, self.translations.get('English', {}))
        
        delete_action = menu.addAction(t.get('delete', 'Delete'))
        action = menu.exec_(self.sidebar_list.mapToGlobal(pos))
        
        if action == delete_action:
            tab = self.tabs.currentIndex()
            if tab == 0:
                self.db.delete_url(item.text())
            else:
                vcard_id = item.data(Qt.UserRole)
                self.db.delete_vcard(vcard_id)
                if self.editing_vcard_id == vcard_id:
                    self.editing_vcard_id = None
            self.populate_sidebar()
            self.url_archive_window.load_archive()
            self.vcard_archive_window.load_archive()
