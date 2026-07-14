<p align="center">
  <img src="icon.png" alt="QRSolo ikonu" width="128" />
</p>

<h1 align="center">QRSolo</h1>

<p align="center">Windows için ücretsiz, tamamen çevrimdışı çalışan QR kod oluşturucu.</p>

<p align="center">
  <a href="README.md">English</a> · <a href="#türkçe">Türkçe</a>
</p>

---

<a name="türkçe"></a>

## Türkçe

**QRSolo**, linkler, kartvizitler, WiFi ağları ve e-postalar için PNG veya SVG formatında QR kod oluşturan ücretsiz bir masaüstü uygulamasıdır. Her şey yerelde çalışır: hesap gerektirmez, internet bağlantısı gerektirmez, hiçbir şeyi takip etmez ve sunucuyla "haberleşen" dinamik QR kodlar üretmez. Oluşturduğunuz kod, hiçbir yerde sunucuda çalışan bir şeye bağlı olmadan sonsuza kadar çalışan, standart, statik bir QR koddur.

### ✨ Özellikler

- **Dört QR türü:** URL, VCard (dijital kartvizit), WiFi ağı ve E-posta.
- **Merkez logo:** QR kodunun ortasına kendi logonuzu, orijinal en-boy oranı bozulmadan yerleştirin.
- **Toplu üretim:** bir CSV dosyasından, dört türden herhangi biri için yüzlerce QR kodunu tek seferde oluşturun.
- **Arşiv:** kaydettiğiniz her QR kodu, türe göre yerel ve aranabilir bir geçmişte tutulur; istediğiniz zaman tekrar yükleyip düzenleyebilir veya dışa aktarabilirsiniz.
- **PNG veya SVG olarak dışa aktarma**, PNG için ayarlanabilir çözünürlük.
- **Özel renkler:** ön plan/arka plan rengini veya şeffaf arka planı kendiniz belirleyin.
- **Türkçe ve İngilizce arayüz**, uygulama içinden anında değiştirilebilir.
- **%100 çevrimdışı:** verileriniz (WiFi şifreleri, kişiler, kayıtlı geçmiş) hiçbir zaman bilgisayarınızdan çıkmaz.

### 📦 Kurulum

**Windows kurulum dosyası:** [Releases](../../releases) sayfasından en güncel `QRSolo_Setup.exe` dosyasını indirip çalıştırın — yönetici hakkı gerektirmez.

**Kaynak koddan çalıştırma:**

```bash
git clone https://github.com/mnevres/qrsolo.git
cd qrsolo
pip install -r requirements.txt
python qr_code_generator.py
```

**Kendi .exe'nizi derlemek isterseniz** (PyInstaller + Inno Setup):

```bash
pip install pyinstaller
pyinstaller qr_code_generator.spec
# ardından tek dosyalık kurulum programı için setup.iss dosyasını Inno Setup 6 ile derleyin
```

### 🛠️ Kullanılan teknolojiler

[PyQt5](https://pypi.org/project/PyQt5/) · [qrcode](https://pypi.org/project/qrcode/) · [Pillow](https://pypi.org/project/pillow/) · [vobject](https://pypi.org/project/vobject/) · SQLite

### 📄 Lisans

Kaynak belirttiğiniz sürece kişisel veya ticari amaçla her yerde ücretsiz kullanabilirsiniz. Resmi bir lisans gerekmez.

### 📬 İletişim

**Mehmet Nevresoğlu**
E-posta: [mehmet@nevresoglu.net](mailto:mehmet@nevresoglu.net)
LinkedIn: [mehmet-nevresoglu](https://www.linkedin.com/in/mehmet-nevresoglu-bb44341a/)
