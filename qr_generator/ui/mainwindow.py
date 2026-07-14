import os
import logging
import json
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, QFrame,
                             QLabel, QMenuBar, QAction, QLineEdit, QApplication,
                             QListWidget, QListWidgetItem, QMenu)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QImage
from PyQt5.QtCore import Qt

from qr_generator import __version__
from qr_generator.database import Database
from qr_generator.engine import make_custom_qr
from qr_generator.utils import resource_path
from qr_generator.ui.widgets import ToastNotification
from qr_generator.ui.dialogs import SettingsWindow, ArchiveWindow, AboutWindow
from qr_generator.ui.tabs.url_tab import URLTab
from qr_generator.ui.tabs.vcard_tab import VCardTab
from qr_generator.ui.tabs.wifi_tab import WiFiTab
from qr_generator.ui.tabs.email_tab import EmailTab
from qr_generator.ui.tabs.bulk_tab import BulkTab

class QRCodeGenerator(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f'QRSolo v{__version__}')
        self.setMinimumSize(1060, 600)
        self.resize(1060, 650)
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
        self.sidebar_container.setFixedWidth(340)
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
                padding: 0px 12px;
                font-size: 13px;
                margin-bottom: 5px;
                min-height: 32px;
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

        self.url_tab = URLTab(self)
        self.vcard_tab = VCardTab(self)
        self.wifi_tab = WiFiTab(self)
        self.email_tab = EmailTab(self)
        self.bulk_tab = BulkTab(self)

        self.tabs.addTab(self.url_tab, "URL")
        self.tabs.addTab(self.vcard_tab, "VCard")
        self.tabs.addTab(self.wifi_tab, "WiFi")
        self.tabs.addTab(self.email_tab, "Email")
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

        # Now connect tab signal after tabs are ready
        self.tabs.currentChanged.connect(self.update_preview)

        self.db = Database()
        self.img_size = 1000
        self.qr_img = None
        self.show_sidebar = True
        self.logo_path = None
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
        self.wifi_ssid_error_message = "Please enter a network name."
        self.email_error_message = "Please enter an email address."
        self.error_message = "An error occurred."
        self.duplicate_vcard_message = "This VCard already exists in the archive."
        self.success_export_message = "Archive exported successfully."
        self.success_import_done_message = "Archive imported successfully."

        self.archive_window = ArchiveWindow(self)
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

    @property
    def editing_vcard_id(self):
        return self.vcard_tab.editing_vcard_id

    @editing_vcard_id.setter
    def editing_vcard_id(self, value):
        self.vcard_tab.editing_vcard_id = value

    @property
    def editing_wifi_id(self):
        return self.wifi_tab.editing_wifi_id

    @editing_wifi_id.setter
    def editing_wifi_id(self, value):
        self.wifi_tab.editing_wifi_id = value

    @property
    def editing_email_id(self):
        return self.email_tab.editing_email_id

    @editing_email_id.setter
    def editing_email_id(self, value):
        self.email_tab.editing_email_id = value

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
            QScrollBar:vertical {
                background: #1c1c1e;
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3c;
                min-height: 24px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a4a4c;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background: #1c1c1e;
                height: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #3a3a3c;
                min-width: 24px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #4a4a4c;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
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
            self.logo_path = settings[6] if len(settings) > 6 and settings[6] and os.path.isfile(settings[6]) else None
        else:
            self.current_language = 'English'
            self.img_size = 1000
            self.fg_color = "#000000"
            self.bg_color = "#ffffff"
            self.is_transparent = False
            self.show_sidebar = True
            self.logo_path = None

        self.set_language(self.current_language)
        self.update_sidebar_visibility()

    def set_language(self, language):
        self.current_language = language
        t = self.translations.get(language, self.translations.get('English', {}))
        if not t:
            return

        try:
            self.setWindowTitle(f"{t.get('window_title', 'QRSolo')} v{__version__}")
            self.tabs.setTabText(0, t.get('url_tab', 'URL'))
            self.tabs.setTabText(1, t.get('vcard_tab', 'VCard'))
            self.tabs.setTabText(2, t.get('wifi_tab', 'WiFi'))
            self.tabs.setTabText(3, t.get('email_tab', 'Email'))
            self.tabs.setTabText(4, t.get('bulk_tab', 'Bulk'))

            self.sidebar_search.setPlaceholderText(t.get('search_placeholder', 'Search...'))
            self.populate_sidebar()

            self.url_tab.update_language_ui(t)
            self.vcard_tab.update_language_ui(t)
            self.wifi_tab.update_language_ui(t)
            self.email_tab.update_language_ui(t)
            self.bulk_tab.update_language_ui(t)

            self.success_language_message = t.get('success_language', 'Language set.')
            self.success_resolution_message = t.get('success_resolution', 'Resolution set.')
            self.success_qr_message = t.get('success_qr', 'QR saved.')
            self.success_vcard_message = t.get('success_vcard', 'VCard saved.')
            self.input_error_message = t.get('input_error', 'Invalid input.')
            self.url_error_message = t.get('url_error', 'Enter URL.')
            self.vcard_error_message = t.get('vcard_error', 'Enter name.')
            self.wifi_ssid_error_message = t.get('wifi_ssid_error', 'Enter a network name.')
            self.email_error_message = t.get('email_error', 'Enter an email address.')
            self.error_message = t.get('error_generic', 'Error.')
            self.duplicate_vcard_message = t.get('duplicate_vcard', 'Duplicate.')

            # Update Menu titles
            actions = self.menuBar().actions()
            if len(actions) > 0: actions[0].setText(t.get('archive', 'Archive'))
            if len(actions) > 1: actions[1].setText(t.get('settings', 'Settings'))
            if len(actions) > 2: actions[2].setText(t.get('about', 'About'))

            # Update archive windows manually
            if hasattr(self, 'archive_window'):
                self.archive_window.update_language_ui(language)

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

            if tab not in (0, 1, 2, 3):
                return

            self.populate_sidebar()

            if tab == 0:
                data = self.url_tab.url_input.text().strip()
                is_empty = not data
            elif tab == 1:
                fn = self.vcard_tab.fn_input.text().strip()
                ln = self.vcard_tab.ln_input.text().strip()
                data = f"BEGIN:VCARD\nFN:{fn} {ln}\nEND:VCARD"
                is_empty = not fn and not ln
            elif tab == 2:
                is_empty = not self.wifi_tab.ssid_input.text().strip()
                data = self.wifi_tab.build_wifi_string()
            else:
                is_empty = not self.email_tab.to_input.text().strip()
                data = self.email_tab.build_email_uri()

            if is_empty:
                self.preview_label.clear()
                self.preview_label.setText(self.preview_placeholder)
                return

            img = make_custom_qr(data, fg_color=self.fg_color, bg_color=self.bg_color, is_transparent=self.is_transparent, is_svg=False, size=240, logo_path=self.logo_path)
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
        # Default the archive dropdown to match the tab you're on, so opening
        # it from VCard/WiFi/Email doesn't silently show the URL list first.
        # Bulk (index 4) has nothing to retrieve, so it leaves whatever mode
        # was last selected.
        tab = self.tabs.currentIndex()
        if tab in (0, 1, 2, 3):
            self.archive_window.type_combo.setCurrentIndex(tab)
        self.archive_window.load_archive()
        self.archive_window.show()
    def open_settings(self): self.settings_window.show()
    def open_about(self): self.about_window.show()
    def load_url(self, url):
        self.url_tab.url_input.setText(url)
        self.update_preview()

    def load_vcard(self, *args):
        self.vcard_tab.load_vcard(*args)

    def load_wifi(self, *args):
        self.wifi_tab.load_wifi(*args)

    def load_email(self, *args):
        self.email_tab.load_email(*args)

    def filter_sidebar(self):
        search_text = self.sidebar_search.text().lower()
        for i in range(self.sidebar_list.count()):
            item = self.sidebar_list.item(i)
            item.setHidden(search_text not in item.text().lower())

    def update_sidebar_visibility(self):
        tab = self.tabs.currentIndex()
        is_visible = self.show_sidebar and tab in (0, 1, 2, 3)

        if is_visible:
            # Move shared widgets to current tab's horizontal layout
            tab_widgets = [self.url_tab, self.vcard_tab, self.wifi_tab, self.email_tab]
            target_layout = tab_widgets[tab].tab_hlayout

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
        elif tab == 2: # WiFi
            self.sidebar_title.setText(t.get('wifi_archive_list', 'Saved WiFi Networks'))
            for wifi_row in self.db.get_wifis():
                item = QListWidgetItem(wifi_row[1]) # ssid
                item.setData(Qt.UserRole, wifi_row[0]) # id
                self.sidebar_list.addItem(item)
        elif tab == 3: # Email
            self.sidebar_title.setText(t.get('email_archive_list', 'Saved Emails'))
            for email_row in self.db.get_emails():
                label = f"{email_row[1]} ({email_row[2]})" if email_row[2] else email_row[1] # to (subject)
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, email_row[0]) # id
                self.sidebar_list.addItem(item)

        self.filter_sidebar() # Re-apply search filter if any

    def load_from_sidebar(self, item):
        tab = self.tabs.currentIndex()
        if tab == 0:
            self.url_tab.url_input.setText(item.text())
            self.update_preview()
        elif tab == 1:
            vcard_id = item.data(Qt.UserRole)
            for v in self.db.get_vcards():
                if v[0] == vcard_id:
                    self.load_vcard(*v)
                    break
        elif tab == 2:
            wifi_id = item.data(Qt.UserRole)
            for w in self.db.get_wifis():
                if w[0] == wifi_id:
                    self.load_wifi(*w)
                    break
        elif tab == 3:
            email_id = item.data(Qt.UserRole)
            for e in self.db.get_emails():
                if e[0] == email_id:
                    self.load_email(*e)
                    break

    def show_sidebar_context_menu(self, pos):
        item = self.sidebar_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        t = self.translations.get(self.current_language, self.translations.get('English', {}))

        delete_action = menu.addAction(t.get('delete', 'Delete'))
        action = menu.exec_(self.sidebar_list.mapToGlobal(pos))

        if action == delete_action:
            tab = self.tabs.currentIndex()
            if tab == 0:
                self.db.delete_url(item.text())
            elif tab == 1:
                vcard_id = item.data(Qt.UserRole)
                self.db.delete_vcard(vcard_id)
                if self.editing_vcard_id == vcard_id:
                    self.editing_vcard_id = None
            elif tab == 2:
                wifi_id = item.data(Qt.UserRole)
                self.db.delete_wifi(wifi_id)
                if self.editing_wifi_id == wifi_id:
                    self.editing_wifi_id = None
            elif tab == 3:
                email_id = item.data(Qt.UserRole)
                self.db.delete_email(email_id)
                if self.editing_email_id == email_id:
                    self.editing_email_id = None
            self.populate_sidebar()
            self.archive_window.load_archive()
