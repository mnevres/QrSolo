import qrcode
from qrcode.image.svg import SvgPathImage
import vobject

def test_vcard_svg():
    fn = "Mehmet"
    ln = "Nevresoglu"
    org = "KPMG"
    title = "Yazılım Uzmanı" # Contains non-ASCII
    
    vcard = vobject.vCard()
    vcard.add('fn').value = f"{fn} {ln}".strip()
    vcard.add('n').value = vobject.vcard.Name(family=ln, given=fn)
    if org: vcard.add('org').value = [org]
    if title: vcard.add('title').value = title
    
    vcard_text = vcard.serialize()
    print("VCard Text:")
    print(vcard_text)
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(vcard_text)
    qr.make(fit=True)
    
    # Test with transparency (back_color=None)
    # We simulate our fix in _make_custom_qr
    svg_kwargs = {"fill_color": "#000000"}
    # back_color = None  # This would crash if passed to make_image
    
    img = qr.make_image(image_factory=SvgPathImage, **svg_kwargs)
    
    with open("test_vcard.svg", "wb") as f:
        img.save(f)
    
    print("Saved test_vcard.svg")

if __name__ == "__main__":
    test_vcard_svg()
