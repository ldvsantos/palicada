"""Recompress EPUB images so the file fits the Kindle 50 MB upload limit.

Reads the original EPUB and writes a new EPUB next to it with PNGs converted
to JPEG (quality 80, max side 1600 px) and JPEGs re-encoded at quality 80.
"""
from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent.parent
SRC = HERE / "Metodologia_Palicadas_Bambu.epub"
DST = HERE / "Metodologia_Palicadas_Bambu_kindle.epub"

MAX_SIDE = 1600
JPEG_QUALITY = 80
TARGET_BYTES = 49 * 1024 * 1024


def recompress_image(name: str, data: bytes) -> tuple[str, bytes, str | None]:
    """Return (new_name, new_bytes, new_media_type) for an EPUB image entry."""
    suffix = Path(name).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg"}:
        return name, data, None
    with Image.open(io.BytesIO(data)) as im:
        im.load()
        if im.mode in {"RGBA", "LA", "P"}:
            background = Image.new("RGB", im.size, (255, 255, 255))
            rgba = im.convert("RGBA")
            background.paste(rgba, mask=rgba.split()[-1])
            im = background
        else:
            im = im.convert("RGB")
        if max(im.size) > MAX_SIDE:
            im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        new_data = buf.getvalue()
    new_name = str(Path(name).with_suffix(".jpg")).replace("\\", "/")
    return new_name, new_data, "image/jpeg"


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"EPUB not found: {SRC}")
    rename_map: dict[str, str] = {}
    with zipfile.ZipFile(SRC, "r") as zin:
        names = zin.namelist()
        entries: list[tuple[str, bytes]] = []
        for name in names:
            data = zin.read(name)
            if name.lower().endswith((".png", ".jpg", ".jpeg")) and not name.endswith("/"):
                new_name, new_data, _ = recompress_image(name, data)
                if new_name != name:
                    rename_map[name] = new_name
                entries.append((new_name, new_data))
            else:
                entries.append((name, data))

    def rewrite_text(name: str, data: bytes) -> bytes:
        if not name.lower().endswith((".xhtml", ".html", ".opf", ".ncx", ".xml", ".css")):
            return data
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return data
        for old, new in rename_map.items():
            text = text.replace(old, new)
            text = text.replace(Path(old).name, Path(new).name)
        if name.endswith(".opf"):
            text = text.replace('media-type="image/png"', 'media-type="image/jpeg"')
        return text.encode("utf-8")

    DST.unlink(missing_ok=True)
    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        # mimetype must be the first entry, stored uncompressed
        mimetype = next((d for n, d in entries if n == "mimetype"), b"application/epub+zip")
        zinfo = zipfile.ZipInfo("mimetype")
        zinfo.compress_type = zipfile.ZIP_STORED
        zout.writestr(zinfo, mimetype)
        for name, data in entries:
            if name == "mimetype":
                continue
            data = rewrite_text(name, data)
            zout.writestr(name, data)

    size = DST.stat().st_size
    status = "OK" if size <= TARGET_BYTES else "STILL TOO LARGE"
    print(f"{DST.name}: {size:,} bytes ({size/1024/1024:.2f} MiB) -> {status}")


if __name__ == "__main__":
    main()
