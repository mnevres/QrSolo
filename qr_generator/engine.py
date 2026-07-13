import base64
import os
import re
from io import BytesIO

import qrcode
from PIL import Image, ImageOps
from PyQt5.QtGui import QColor


def _add_logo_to_png(img, logo_path):
    logo = Image.open(logo_path).convert("RGBA")
    qr_w, qr_h = img.size
    logo_size = int(qr_w * 0.22)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    # White backing square behind the logo so it stands out from the QR
    # pattern and stays legible regardless of the logo's own transparency.
    pad = int(logo_size * 0.08)
    box_size = logo_size + pad * 2
    box_pos = ((qr_w - box_size) // 2, (qr_h - box_size) // 2)
    backing = Image.new("RGBA", (box_size, box_size), (255, 255, 255, 255))
    img.paste(backing, box_pos, backing)

    logo_pos = ((qr_w - logo_size) // 2, (qr_h - logo_size) // 2)
    img.paste(logo, logo_pos, logo)
    return img


def _add_logo_to_svg(svg_str, logo_path):
    match = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg_str)
    if not match:
        return svg_str
    width, height = float(match.group(1)), float(match.group(2))

    logo = Image.open(logo_path).convert("RGBA")
    buf = BytesIO()
    logo.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')

    logo_size = width * 0.22
    box_size = logo_size + (logo_size * 0.08) * 2
    box_pos = ((width - box_size) / 2, (height - box_size) / 2)
    logo_pos = ((width - logo_size) / 2, (height - logo_size) / 2)

    overlay = (
        f'<rect x="{box_pos[0]:.2f}" y="{box_pos[1]:.2f}" width="{box_size:.2f}" height="{box_size:.2f}" fill="#ffffff"/>'
        f'<image x="{logo_pos[0]:.2f}" y="{logo_pos[1]:.2f}" width="{logo_size:.2f}" height="{logo_size:.2f}" '
        f'href="data:image/png;base64,{b64}"/>'
    )
    return svg_str.replace('</svg>', overlay + '</svg>')


def make_custom_qr(data, fg_color="#000000", bg_color="#ffffff", is_transparent=False, is_svg=False, size=None, logo_path=None):
    has_logo = bool(logo_path and os.path.isfile(logo_path))
    # A center logo covers part of the code, so bump error correction to
    # the highest level (tolerates ~30% damage) only when it's actually needed --
    # higher error correction makes the code visually denser for the same data.
    error_correction = qrcode.constants.ERROR_CORRECT_H if has_logo else qrcode.constants.ERROR_CORRECT_L
    qr = qrcode.QRCode(version=1, error_correction=error_correction, box_size=10, border=4)
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

        if has_logo:
            svg_str = _add_logo_to_svg(svg_str, logo_path)

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

        if has_logo:
            img = _add_logo_to_png(img, logo_path)

        return img
