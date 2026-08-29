"""Synthetic DJI capture fixtures: tiny JPEGs with planted EXIF + drone-dji XMP.

Built in pure PIL + byte assembly (no exiftool dependency): EXIF rides
PIL's writer; the XMP packet is inserted as its own APP1 segment, which is
exactly where DJI writes it.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

_XMP_TEMPLATE = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
    'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    '<rdf:Description xmlns:drone-dji="http://www.dji.com/drone-dji/1.0/" {attrs}/>'
    "</rdf:RDF></x:xmpmeta>"
)


def write_dji_jpeg(path: Path, model: str, make: str = "DJI", **xmp_attrs: str) -> Path:
    """A 2x2 JPEG whose EXIF Model is `model` and whose XMP carries `xmp_attrs`."""
    img = Image.new("RGB", (2, 2), (120, 40, 40))
    exif = Image.Exif()
    exif[271] = make
    exif[272] = model
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    data = buf.getvalue()
    if xmp_attrs:
        attrs = " ".join(f'drone-dji:{k}="{v}"' for k, v in xmp_attrs.items())
        packet = b"http://ns.adobe.com/xap/1.0/\x00" + _XMP_TEMPLATE.format(attrs=attrs).encode()
        segment = b"\xff\xe1" + (len(packet) + 2).to_bytes(2, "big") + packet
        data = data[:2] + segment + data[2:]
    path.write_bytes(data)
    return path
