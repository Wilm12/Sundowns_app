import base64
from io import BytesIO

import qrcode
from django import template

register = template.Library()


@register.filter
def qr_code_base64(value):
    qr = qrcode.make(str(value))
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{image_base64}"
