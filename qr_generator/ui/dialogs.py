import csv
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QComboBox, QFrame, QLineEdit, QCheckBox, QListWidget, QListWidgetItem,
                             QFileDialog, QApplication)
from PyQt5.QtGui import QColor, QRegExpValidator
from PyQt5.QtCore import Qt, QRegExp

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_obj = parent # Avoid using 'parent' as it's a QObject method
        self.setWindowTitle('Settings')
        self.setGeometry(100, 100, 300, 300)
        self.center()
        
        # Initialize defaults
        self.fg_color = "#000000"
        self.bg_color = "#ffffff"
        self.is_transparent = False
        self.show_sidebar = True

        self.layout = QVBoxLayout()
        
        # Language settings
        self.language_label = QLabel('Language')
        font = self.language_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        self.language_label.setFont(font)
        self.layout.addWidget(self.language_label)

        self.language_combo = QComboBox()
        self.language_combo.addItems(['English', 'Türkçe'])
        self.layout.addWidget(self.language_combo)

        self.set_language_button = QPushButton('Set Language')
        self.set_language_button.clicked.connect(self.set_language)
        self.layout.addWidget(self.set_language_button)
        
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(self.separator)
        
        # Resolution settings
        self.resolution_title = QLabel('QR Code Resolution')
        self.resolution_title.setFont(font)
        self.layout.addWidget(self.resolution_title)
        
        self.label_info = QLabel('Min: 100 px, Max: 2000 px')
        self.layout.addWidget(self.label_info)
        
        self.label_dimensions = QLabel('Current Resolution: 1000 x 1000 px')
        self.layout.addWidget(self.label_dimensions)
        
        self.resolution_input = QLineEdit()
        self.resolution_input.setValidator(QRegExpValidator(QRegExp(r'[0-9]*')))
        self.layout.addWidget(self.resolution_input)
        
        self.set_button = QPushButton('Set Resolution')
        self.set_button.clicked.connect(self.set_resolution)
        self.layout.addWidget(self.set_button)

        self.layout.addWidget(self.separator)

        # Style settings
        self.style_title = QLabel('QR Style & Transparency')
        self.style_title.setFont(font)
        self.layout.addWidget(self.style_title)

        # Foreground Color
        fg_layout = QHBoxLayout()
        self.fg_color_label = QLabel("Foreground Color")
        self.fg_color_btn = QPushButton("Select Color")
        self.fg_color_btn.clicked.connect(self.pick_fg_color)
        fg_layout.addWidget(self.fg_color_label)
        fg_layout.addWidget(self.fg_color_btn)
        self.layout.addLayout(fg_layout)

        # Background Color
        bg_layout = QHBoxLayout()
        self.bg_color_label = QLabel("Background Color")
        self.bg_color_btn = QPushButton("Select Color")
        self.bg_color_btn.clicked.connect(self.pick_bg_color)
        bg_layout.addWidget(self.bg_color_label)
        bg_layout.addWidget(self.bg_color_btn)
        self.layout.addLayout(bg_layout)

        # Transparency
        self.transparency_check = QCheckBox("Transparent Background")
        self.transparency_check.setStyleSheet("color: white; font-weight: bold;")
        self.transparency_check.stateChanged.connect(self.on_transparency_toggled)
        self.layout.addWidget(self.transparency_check)

        # Sidebar toggle
        self.sidebar_check = QCheckBox("Show Archive Sidebar")
        self.sidebar_check.setStyleSheet("color: white; font-weight: bold;")
        self.sidebar_check.stateChanged.connect(self.save_all_settings)
        self.layout.addWidget(self.sidebar_check)
        
        self.setLayout(self.layout)
        
        self.load_settings()
    
    def load_settings(self):
        settings = self.parent_obj.db.get_settings()
        if settings:
            language = settings[0]
            resolution = settings[1]
            if language:
                self.language_combo.setCurrentText(language)
            if resolution:
                self.resolution_input.setText(str(resolution))
                self.label_dimensions.setText(f'Current Resolution: {resolution} x {resolution} px')
            
            fg = settings[2] if len(settings) > 2 else "#000000"
            bg = settings[3] if len(settings) > 3 else "#ffffff"
            trans = settings[4] if len(settings) > 4 else 0
            sidebar = settings[5] if len(settings) > 5 else 1
            
            self.fg_color = fg
            self.bg_color = bg
            self.fg_color_btn.setStyleSheet(f"background-color: {fg}; color: {'white' if QColor(fg).lightness() < 128 else 'black'};")
            self.bg_color_btn.setStyleSheet(f"background-color: {bg}; color: {'white' if QColor(bg).lightness() < 128 else 'black'};")
            
            self.transparency_check.blockSignals(True)
            self.sidebar_check.blockSignals(True)
            self.transparency_check.setChecked(bool(trans))
            self.sidebar_check.setChecked(bool(sidebar))
            self.transparency_check.blockSignals(False)
            self.sidebar_check.blockSignals(False)
            
            self.update_ui_states()

    def on_transparency_toggled(self):
        self.update_ui_states()
        self.save_all_settings()

    def update_ui_states(self):
        is_trans = self.transparency_check.isChecked()
        self.bg_color_btn.setEnabled(not is_trans)
        self.bg_color_label.setEnabled(not is_trans)
        if is_trans:
            self.bg_color_btn.setStyleSheet("background-color: #444; color: #888; border: 1px solid #555;")
        else:
            bg = self.bg_color
            self.bg_color_btn.setStyleSheet(f"background-color: {bg}; color: {'white' if QColor(bg).lightness() < 128 else 'black'};")

    def pick_fg_color(self):
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor(QColor(self.fg_color), self, "Select Foreground Color")
        if color.isValid():
            self.fg_color = color.name()
            self.fg_color_btn.setStyleSheet(f"background-color: {self.fg_color}; color: {'white' if color.lightness() < 128 else 'black'};")
            self.save_all_settings()

    def pick_bg_color(self):
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor(QColor(self.bg_color), self, "Select Background Color")
        if color.isValid():
            self.bg_color = color.name()
            self.bg_color_btn.setStyleSheet(f"background-color: {self.bg_color}; color: {'white' if color.lightness() < 128 else 'black'};")
            self.save_all_settings()

    def save_all_settings(self):
        lang = self.language_combo.currentText()
        try:
            res = int(self.resolution_input.text())
        except (ValueError, TypeError):
            res = self.parent_obj.img_size
        
        trans = 1 if self.transparency_check.isChecked() else 0
        sidebar = 1 if self.sidebar_check.isChecked() else 0
        self.parent_obj.db.set_settings(lang, res, self.fg_color, self.bg_color, trans, sidebar)
        self.parent_obj.load_settings() # Reload in main window
        self.parent_obj.update_preview()

    def set_resolution(self):
        self.save_all_settings()
        self.parent_obj.show_toast(self.parent_obj.success_resolution_message)
    
    def set_language(self):
        self.save_all_settings()
        self.parent_obj.set_language(self.language_combo.currentText())
        self.parent_obj.show_toast(self.parent_obj.success_language_message)

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def update_language_ui(self, language):
        t = self.parent_obj.translations.get(language, self.parent_obj.translations.get('English', {}))

        self.setWindowTitle(t.get('settings', 'Settings'))
        self.language_label.setText(t.get('language_label', 'Language'))
        self.set_language_button.setText(t.get('set_language', 'Set Language'))
        self.resolution_title.setText(t.get('resolution_title', 'QR Code Resolution'))
        self.label_info.setText(t.get('resolution_info', 'Min: 100 px, Max: 2000 px'))
        self.set_button.setText(t.get('set_resolution', 'Set Resolution'))
        self.label_dimensions.setText(t.get('current_resolution', 'Current Resolution: {0} x {0} px').format(self.parent_obj.img_size))
        self.style_title.setText(t.get('style_title', 'QR Style & Transparency'))
        self.fg_color_label.setText(t.get('fg_color', 'Foreground Color'))
        self.bg_color_label.setText(t.get('bg_color', 'Background Color'))
        self.fg_color_btn.setText(t.get('select_color', 'Select Color'))
        self.bg_color_btn.setText(t.get('select_color', 'Select Color'))
        self.transparency_check.setText(t.get('transparent_bg', 'Transparent Background'))
        self.sidebar_check.setText(t.get('show_sidebar', 'Show Archive Sidebar'))

class URLArchiveWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_obj = parent
        self.setWindowTitle('URL Archive')
        self.setGeometry(100, 100, 300, 400)
        self.center()
        
        self.layout = QVBoxLayout()
        
        self.url_list_widget = QListWidget()
        self.layout.addWidget(self.url_list_widget)
        
        self.get_button = QPushButton('Retrieve from Archive')
        self.get_button.clicked.connect(self.return_selected)
        self.layout.addWidget(self.get_button)
        
        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete_selected)
        self.layout.addWidget(self.delete_button)

        self.export_button = QPushButton('Export Archive to CSV')
        self.export_button.clicked.connect(self.export_to_csv)
        self.layout.addWidget(self.export_button)

        self.import_button = QPushButton('Import Archive from CSV')
        self.import_button.clicked.connect(self.import_from_csv)
        self.layout.addWidget(self.import_button)
        
        self.setLayout(self.layout)
        
        self.db = self.parent_obj.db
        self.load_archive()
    
    def load_archive(self):
        self.url_list_widget.clear()
        urls = self.db.get_urls()
        self.url_list_widget.addItems([url[0] for url in urls])

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def return_selected(self):
        selected_url = self.url_list_widget.currentItem()
        if not selected_url:
            return
        self.parent_obj.load_url(selected_url.text())
        self.close()
    
    def delete_selected(self):
        selected_url = self.url_list_widget.currentItem()
        if selected_url:
            self.db.delete_url(selected_url.text())
            self.url_list_widget.takeItem(self.url_list_widget.row(selected_url))

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "url_archive.csv", "CSV Files (*.csv)")
        if path:
            try:
                urls = self.db.get_urls()
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["URL"])
                    writer.writerows(urls)
                self.parent_obj.show_toast(self.parent_obj.success_export_message)
            except Exception as e:
                self.parent_obj.show_toast(f"Could not export: {e}", is_error=True)

    def import_from_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'r', newline='', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if header and any("URL" in h for h in header):
                        for row in reader:
                            if row:
                                self.db.add_url(row[0])
                        self.load_archive()
                        self.parent_obj.show_toast(self.parent_obj.success_import_done_message)
                    else:
                        self.parent_obj.show_toast("This is not a valid URL archive CSV.", is_error=True)
            except Exception as e:
                self.parent_obj.show_toast(f"Could not import: {e}", is_error=True)

class VCardArchiveWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_obj = parent
        self.setWindowTitle('VCard Archive')
        self.setGeometry(100, 100, 300, 400)
        self.center()
        
        self.layout = QVBoxLayout()
        
        self.vcard_list_widget = QListWidget()
        self.layout.addWidget(self.vcard_list_widget)
        
        self.get_button = QPushButton('Retrieve from Archive')
        self.get_button.clicked.connect(self.return_selected)
        self.layout.addWidget(self.get_button)
        
        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete_selected)
        self.layout.addWidget(self.delete_button)

        self.export_button = QPushButton('Export Archive to CSV')
        self.export_button.clicked.connect(self.export_to_csv)
        self.layout.addWidget(self.export_button)

        self.import_button = QPushButton('Import Archive from CSV')
        self.import_button.clicked.connect(self.import_from_csv)
        self.layout.addWidget(self.import_button)
        
        self.setLayout(self.layout)
        
        self.db = self.parent_obj.db
        self.load_archive()
    
    def load_archive(self):
        self.vcard_list_widget.clear()
        vcards = self.db.get_vcards()
        for vcard in vcards:
            item = QListWidgetItem(vcard[1])  # name
            item.setData(Qt.UserRole, vcard[0])  # id
            self.vcard_list_widget.addItem(item)

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def return_selected(self):
        selected_item = self.vcard_list_widget.currentItem()
        if not selected_item:
            return
        vcard_id = selected_item.data(Qt.UserRole)
        vcards = self.db.get_vcards()
        for vcard in vcards:
            if vcard[0] == vcard_id:
                self.parent_obj.load_vcard(*vcard)
                break
        self.close()

    def delete_selected(self):
        selected_item = self.vcard_list_widget.currentItem()
        if selected_item:
            vcard_id = selected_item.data(Qt.UserRole)
            self.db.delete_vcard(vcard_id)
            if self.parent_obj.editing_vcard_id == vcard_id:
                self.parent_obj.editing_vcard_id = None
            self.vcard_list_widget.takeItem(self.vcard_list_widget.row(selected_item))

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "vcard_archive.csv", "CSV Files (*.csv)")
        if path:
            try:
                vcards = self.db.get_vcards()
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Name", "First Name", "Last Name", "Organization", "Title", "Email", "Phone", "Mobile", "Website", "VCard Text"])
                    writer.writerows([v[1:] for v in vcards])  # skip internal id
                self.parent_obj.show_toast(self.parent_obj.success_export_message)
            except Exception as e:
                self.parent_obj.show_toast(f"Could not export: {e}", is_error=True)

    def import_from_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'r', newline='', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if header and any("Name" in h for h in header):
                        for row in reader:
                            if len(row) >= 10:
                                self.db.add_vcard(*row)
                        self.load_archive()
                        self.parent_obj.show_toast(self.parent_obj.success_import_done_message)
                    else:
                        self.parent_obj.show_toast("This is not a valid VCard archive CSV.", is_error=True)
            except Exception as e:
                self.parent_obj.show_toast(f"Could not import: {e}", is_error=True)

class AboutWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('About')
        self.setGeometry(100, 100, 400, 200)
        self.center()

        self.layout = QVBoxLayout()

        self.creator_label = QLabel('Creator: Mehmet Nevresoğlu')
        self.layout.addWidget(self.creator_label)

        self.contact_label = QLabel('Contact: <a href="mailto:mehmet@nevresoglu.net" style="color: #4da3ff;">mehmet@nevresoglu.net</a>')
        self.contact_label.setOpenExternalLinks(True)
        self.layout.addWidget(self.contact_label)

        self.linkedin_label = QLabel('LinkedIn: <a href="https://www.linkedin.com/in/mehmet-nevresoglu-bb44341a/" style="color: #4da3ff;">Click here</a>')
        self.linkedin_label.setOpenExternalLinks(True)
        self.layout.addWidget(self.linkedin_label)

        self.usage_label = QLabel('You can use this program anywhere as long as you cite it as a reference. No license required.')
        self.layout.addWidget(self.usage_label)

        self.setLayout(self.layout)
    
    def update_language_ui(self, language):
        if language == 'Türkçe':
            self.setWindowTitle('Hakkında')
            self.creator_label.setText('Geliştirici: Mehmet Nevresoğlu')
            self.contact_label.setText('İletişim: <a href="mailto:mehmet@nevresoglu.net" style="color: #4da3ff;">mehmet@nevresoglu.net</a>')
            self.linkedin_label.setText('LinkedIn: <a href="https://www.linkedin.com/in/mehmet-nevresoglu-bb44341a/" style="color: #4da3ff;">Buraya tıklayın</a>')
            self.usage_label.setText('Bu programı kaynak belirttiğiniz sürece her yerde kullanabilirsiniz. Lisans gerektirmez.')
        else:
            self.setWindowTitle('About')
            self.creator_label.setText('Creator: Mehmet Nevresoğlu')
            self.contact_label.setText('Contact: <a href="mailto:mehmet@nevresoglu.net" style="color: #4da3ff;">mehmet@nevresoglu.net</a>')
            self.linkedin_label.setText('LinkedIn: <a href="https://www.linkedin.com/in/mehmet-nevresoglu-bb44341a/" style="color: #4da3ff;">Click here</a>')
            self.usage_label.setText('You can use this program anywhere as long as you cite it as a reference. No license required.')

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
