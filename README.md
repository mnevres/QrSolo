<p align="center">
  <img src="icon.png" alt="QRSolo icon" width="128" />
</p>

<h1 align="center">QrSolo</h1>

<p align="center">A free, fully offline QR code generator for Windows.</p>

<p align="center">
  <a href="#english">English</a> · <a href="README.tr.md">Türkçe</a>
</p>

---

<a name="english"></a>

## English

**QRSolo** is a free desktop application for generating QR codes — for links, contact cards, Wi-Fi networks, or emails — in PNG or SVG format. Everything runs locally: there's no account, no internet connection required, no tracking, and no "dynamic" QR codes that phone home. What you generate is a static, standard QR code that works forever, with nothing running on a server anywhere.

### ✨ Features

- **Four QR types:** URL, VCard (digital business card), Wi-Fi network, and Email.
- **Center logo:** embed your own logo in the middle of a QR code, with its original aspect ratio preserved (no stretching).
- **Bulk generation:** generate hundreds of QR codes at once from a CSV file, for any of the four types.
- **Archive:** every QR code you save is kept in a local, searchable history per type, so you can reload, edit, or re-export it later.
- **PNG or SVG export**, with adjustable resolution for PNG.
- **Custom colors:** set foreground/background colors or a transparent background.
- **Turkish and English UI**, switchable at runtime.
- **100% offline:** your data (Wi-Fi passwords, contacts, saved history) never leaves your computer.

### 📦 Installation

**Windows installer:** download the latest `QRSolo_Setup.exe` from [Releases](../../releases) and run it — no admin rights required.

**From source:**

```bash
git clone https://github.com/mnevres/QrSolo.git
cd QrSolo
pip install -r requirements.txt
python qr_code_generator.py
```

**Building the .exe yourself** (PyInstaller + Inno Setup):

```bash
pip install pyinstaller
pyinstaller qr_code_generator.spec
# then compile setup.iss with Inno Setup 6 to produce a single installer
```

### 🛠️ Built with

[PyQt5](https://pypi.org/project/PyQt5/) · [qrcode](https://pypi.org/project/qrcode/) · [Pillow](https://pypi.org/project/pillow/) · [vobject](https://pypi.org/project/vobject/) · SQLite

### 📄 License

Free to use anywhere, for personal or commercial purposes, as long as you credit the original author. No formal license required.

### 📬 Contact

**Mehmet Nevresoğlu**
Email: [mehmet@nevresoglu.net](mailto:mehmet@nevresoglu.net)
LinkedIn: [mehmet-nevresoglu](https://www.linkedin.com/in/mehmet-nevresoglu-bb44341a/)
