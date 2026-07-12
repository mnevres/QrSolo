import qrcode
from PIL import Image, ImageOps
from PyQt5.QtGui import QColor

def make_custom_qr(data, fg_color="#000000", bg_color="#ffffff", is_transparent=False, is_svg=False, size=None):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    
    if is_svg:
        from qrcode.image.svg import SvgPathImage
        
        svg_kwargs = {"fill_color": fg_color}
        if not is_transparent:
            svg_kwargs["back_color"] = bg_color
            
        img = qr.make_image(image_factory=SvgPathImage, **svg_kwargs)
        # Fix for qrcode's SvgPathImage ignoring fill_color for the path itself sometimes
        svg_str = img.to_string().decode('utf-8')
        
        # Standardize the fill on the path
        if 'fill="#000000"' in svg_str:
            svg_str = svg_str.replace('fill="#000000"', f'fill="{fg_color}"')
        elif 'fill="black"' in svg_str:
            svg_str = svg_str.replace('fill="black"', f'fill="{fg_color}"')
        
        # We need to return an object with a .save() method to match PIL
        class SvgWrapper:
            def __init__(self, content): self.content = content
            def save(self, path):
                with open(path, 'w', encoding='utf-8') as f: f.write(self.content)
        return SvgWrapper(svg_str)
    else:
        # Generate a crisp black/white mask
        mask = qr.make_image(fill_color="black", back_color="white").convert("L")
        if size:
            mask = mask.resize((size, size), Image.NEAREST)
        
        # Create the final image
        fg_q = QColor(fg_color)
        bg_q = QColor(bg_color)
        
        fg_rgba = (fg_q.red(), fg_q.green(), fg_q.blue(), 255)
        bg_rgba = (bg_q.red(), bg_q.green(), bg_q.blue(), 0 if is_transparent else 255)
        
        # Create image with target background, then stamp the foreground color
        # through the QR mask in one vectorized PIL call (fast even at 2000px)
        img = Image.new("RGBA", mask.size, bg_rgba)
        fg_layer = Image.new("RGBA", mask.size, fg_rgba)
        qr_mask = ImageOps.invert(mask)  # QR modules (dark in mask) -> opaque
        img.paste(fg_layer, (0, 0), qr_mask)

        return img
