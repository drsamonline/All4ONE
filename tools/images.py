"""Images — resize, convert, watermark and inspect (needs Pillow)."""

from __future__ import annotations

from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import human_size, iter_files, need_dir, need_file, out_path, report_table, require

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff)"
FORMATS = ["PNG", "JPEG", "WEBP", "BMP", "TIFF", "GIF"]


def _open(path: Path):
    require("PIL.Image", "pillow")
    from PIL import Image, ImageOps
    try:
        image = Image.open(path)
        image.load()
        return ImageOps.exif_transpose(image)
    except Exception as exc:  # noqa: BLE001 - Pillow raises many types
        raise ToolError(f"Could not open {path.name}: {exc}") from exc


def _hex(value: str, fallback: str = "#ffffff") -> str:
    """Normalise a colour field to the #rrggbb form Pillow accepts."""
    text = str(value or "").strip()
    if text.startswith("#") and len(text) == 7:
        return text
    if len(text) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in text):
        return "#" + text
    return fallback


def _save(image, target: Path, quality: int = 90, keep_exif: bool = False) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = target.suffix.lower().lstrip(".")
    fmt = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP",
           "bmp": "BMP", "tif": "TIFF", "tiff": "TIFF", "gif": "GIF"}.get(suffix, "PNG")
    params = {}
    if fmt in ("JPEG", "WEBP"):
        params["quality"] = quality
        if fmt == "JPEG" and image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")
    if fmt == "JPEG" and not keep_exif:
        params["exif"] = b""
    if fmt == "TIFF":
        params["compression"] = "tiff_deflate"
    image.save(target, fmt, **params)
    return target


def _single_output(v, source: Path, suffix: str, default_ext: str) -> Path:
    raw = str(v.get("output") or "").strip()
    if raw:
        return out_path(raw, source.stem + suffix + default_ext)
    return source.with_name(source.stem + suffix + default_ext)


@tool(id="image-resize", name="Resize Image", category="Images",
      summary="Resize to exact pixels or a percentage, keeping the aspect ratio if you want.",
      keywords="resize scale dimensions pixels shrink enlarge",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.integer("width", "Width (px)", 800, minimum=0, maximum=20000),
              F.integer("height", "Height (px)", 0, minimum=0, maximum=20000,
                        help="0 = work it out from the width"),
              F.flag("keep_aspect", "Keep the aspect ratio", True),
              F.choice("resample", "Quality", ["High (Lanczos)", "Medium", "Fast"], "High (Lanczos)"),
              F.save("output", "Save as", required=False, filters=IMAGE_FILTER)])
def image_resize(v, ctx):
    from PIL import Image
    path = need_file(v["file"], "Image")
    image = _open(path)
    original = image.size
    width, height = v["width"], v["height"]
    if width <= 0 and height <= 0:
        raise ToolError("Give a width, a height, or both")
    if v["keep_aspect"]:
        if width and height:
            ratio = min(width / image.width, height / image.height)
        elif width:
            ratio = width / image.width
        else:
            ratio = height / image.height
        size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
    else:
        size = (width or image.width, height or image.height)
    method = {"High (Lanczos)": Image.LANCZOS, "Medium": Image.BICUBIC,
              "Fast": Image.NEAREST}[v["resample"]]
    target = _single_output(v, path, f"-{size[0]}x{size[1]}", path.suffix or ".png")
    _save(image.resize(size, method), target)
    ctx.output(str(target))
    return f"{original[0]}×{original[1]} → {size[0]}×{size[1]}  ({target.name})"


@tool(id="image-convert", name="Convert Image Format", category="Images",
      summary="Convert between PNG, JPEG, WebP, BMP, TIFF and GIF with a quality setting.",
      keywords="convert format png jpg webp bmp tiff gif",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.choice("format", "Convert to", FORMATS, "WEBP"),
              F.integer("quality", "Quality", 90, minimum=1, maximum=100),
              F.save("output", "Save as", required=False, filters=IMAGE_FILTER)])
def image_convert(v, ctx):
    path = need_file(v["file"], "Image")
    image = _open(path)
    ext = "." + {"JPEG": "jpg", "TIFF": "tif"}.get(v["format"], v["format"].lower())
    target = _single_output(v, path, "", ext)
    _save(image, target, v["quality"])
    before, after = path.stat().st_size, target.stat().st_size
    ctx.output(str(target))
    return (f"{path.suffix or '?'} → {ext}  ·  {human_size(before)} → {human_size(after)} "
            f"({target.name})")


@tool(id="image-crop", name="Crop Image", category="Images",
      summary="Cut an image to a box, a square, or the centre — with exact coordinates if you like.",
      keywords="crop cut trim box square centre center",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.choice("mode", "Crop to", ["Square (centre)", "Centre percentage",
                                           "Exact box", "Aspect ratio"], "Square (centre)"),
              F.integer("percent", "Centre percentage", 80, minimum=5, maximum=100,
                        show_if=""),
              F.integer("left", "Left", 0, minimum=0),
              F.integer("top", "Top", 0, minimum=0),
              F.integer("right", "Right", 0, minimum=0),
              F.integer("bottom", "Bottom", 0, minimum=0),
              F.number("aspect", "Aspect ratio (width/height)", 1.0, minimum=0.1, maximum=10.0),
              F.save("output", "Save as", required=False, filters=IMAGE_FILTER)])
def image_crop(v, ctx):
    path = need_file(v["file"], "Image")
    image = _open(path)
    width, height = image.size
    mode = v["mode"]
    if mode.startswith("Square"):
        side = min(width, height)
        box = ((width - side) // 2, (height - side) // 2,
               (width + side) // 2, (height + side) // 2)
    elif mode.startswith("Centre"):
        factor = v["percent"] / 100
        box = (int(width * (1 - factor) / 2), int(height * (1 - factor) / 2),
               int(width * (1 + factor) / 2), int(height * (1 + factor) / 2))
    elif mode == "Exact box":
        box = (v["left"], v["top"], v["right"] or width, v["bottom"] or height)
        if box[2] <= box[0] or box[3] <= box[1]:
            raise ToolError("The box is empty — check left/top/right/bottom")
    else:
        ratio = v["aspect"]
        if width / height > ratio:
            new_w, new_h = int(height * ratio), height
        else:
            new_w, new_h = width, int(width / ratio)
        box = ((width - new_w) // 2, (height - new_h) // 2,
               (width + new_w) // 2, (height + new_h) // 2)
    cropped = image.crop(box)
    target = _single_output(v, path, "-crop", path.suffix or ".png")
    _save(cropped, target)
    ctx.output(str(target))
    return f"Cropped to {cropped.width}×{cropped.height}  ({target.name})"


@tool(id="image-rotate", name="Rotate & Flip", category="Images",
      summary="Rotate by any angle or flip horizontally / vertically, with EXIF auto-correction.",
      keywords="rotate flip mirror turn angle orientation",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.choice("action", "Action", ["Rotate 90° right", "Rotate 90° left", "Rotate 180°",
                                            "Rotate by angle", "Flip horizontal", "Flip vertical"],
                       "Rotate 90° right"),
              F.number("angle", "Angle (degrees)", 15.0, minimum=-360.0, maximum=360.0),
              F.flag("expand", "Grow the canvas so nothing is cut off", True),
              F.save("output", "Save as", required=False, filters=IMAGE_FILTER)])
def image_rotate(v, ctx):
    from PIL import Image
    path = need_file(v["file"], "Image")
    image = _open(path)
    action = v["action"]
    if action == "Rotate 90° right":
        result = image.rotate(-90, expand=True)
    elif action == "Rotate 90° left":
        result = image.rotate(90, expand=True)
    elif action == "Rotate 180°":
        result = image.rotate(180, expand=True)
    elif action == "Rotate by angle":
        result = image.rotate(v["angle"], expand=v["expand"], resample=Image.BICUBIC)
    elif action == "Flip horizontal":
        result = image.transpose(Image.FLIP_LEFT_RIGHT)
    else:
        result = image.transpose(Image.FLIP_TOP_BOTTOM)
    target = _single_output(v, path, "-rotated", path.suffix or ".png")
    _save(result, target)
    ctx.output(str(target))
    return f"{action} → {result.width}×{result.height}  ({target.name})"


@tool(id="image-watermark", name="Watermark Image", category="Images",
      summary="Stamp text or a logo onto a photo, with position, opacity, size and colour.",
      keywords="watermark logo copyright text overlay brand",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.text("text", "Watermark text", "© All rights reserved"),
              F.file("logo", "…or a logo image (PNG)", required=False, filters=IMAGE_FILTER),
              F.choice("position", "Position",
                       ["Bottom right", "Bottom left", "Top right", "Top left", "Centre"],
                       "Bottom right"),
              F.integer("opacity", "Opacity", 45, minimum=5, maximum=100, suffix="%"),
              F.integer("size", "Text size", 4, minimum=1, maximum=40,
                        help="Percent of the image height"),
              F.color("colour", "Colour", "#ffffff"),
              F.save("output", "Save as", required=False, filters=IMAGE_FILTER)])
def image_watermark(v, ctx):
    from PIL import Image, ImageDraw, ImageFont
    path = need_file(v["file"], "Image")
    image = _open(path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    alpha = int(255 * v["opacity"] / 100)

    logo_path = str(v["logo"] or "").strip()
    if logo_path:
        logo = _open(need_file(logo_path, "Logo")).convert("RGBA")
        target_width = max(24, int(image.width * 0.18))
        logo = logo.resize((target_width, max(1, int(logo.height * target_width / logo.width))))
        if v["opacity"] < 100:
            logo.putalpha(logo.getchannel("A").point(lambda a: int(a * v["opacity"] / 100)))
        pad = max(8, image.width // 60)
        positions = {
            "Bottom right": (image.width - logo.width - pad, image.height - logo.height - pad),
            "Bottom left": (pad, image.height - logo.height - pad),
            "Top right": (image.width - logo.width - pad, pad),
            "Top left": (pad, pad),
            "Centre": ((image.width - logo.width) // 2, (image.height - logo.height) // 2),
        }
        overlay.alpha_composite(logo, positions[v["position"]])
    else:
        text = v["text"]
        if not text:
            raise ToolError("Give watermark text, or choose a logo image")
        font_size = max(10, int(image.height * v["size"] / 100))
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        colour = v["colour"].lstrip("#")
        rgb = tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4)) if len(colour) == 6 else (255, 255, 255)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad = max(8, image.width // 50)
        spots = {
            "Bottom right": (image.width - tw - pad, image.height - th - pad * 2),
            "Bottom left": (pad, image.height - th - pad * 2),
            "Top right": (image.width - tw - pad, pad),
            "Top left": (pad, pad),
            "Centre": ((image.width - tw) // 2, (image.height - th) // 2),
        }
        draw.text(spots[v["position"]], text, font=font, fill=(*rgb, alpha))
    result = Image.alpha_composite(image, overlay)
    target = _single_output(v, path, "-watermarked", path.suffix or ".png")
    _save(result, target)
    ctx.output(str(target))
    return f"Watermarked → {target.name}"


@tool(id="image-compress", name="Compress Image", category="Images",
      summary="Shrink a photo's file size by re-encoding at a quality you choose.",
      keywords="compress shrink optimise optimize filesize quality",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.integer("quality", "Quality", 75, minimum=10, maximum=95),
              F.integer("max_width", "Shrink to a maximum width (0 = keep)", 0, minimum=0),
              F.save("output", "Save as", required=False, filters=IMAGE_FILTER)])
def image_compress(v, ctx):
    from PIL import Image
    path = need_file(v["file"], "Image")
    image = _open(path)
    if v["max_width"] and image.width > v["max_width"]:
        ratio = v["max_width"] / image.width
        image = image.resize((v["max_width"], max(1, int(image.height * ratio))), Image.LANCZOS)
    ext = ".jpg" if path.suffix.lower() in (".jpg", ".jpeg") else path.suffix or ".jpg"
    target = _single_output(v, path, "-compressed", ext)
    _save(image, target, v["quality"])
    before, after = path.stat().st_size, target.stat().st_size
    saved = (1 - after / before) * 100 if before else 0
    ctx.output(str(target))
    return (f"{human_size(before)} → {human_size(after)}  ({saved:.0f}% smaller)  "
            f"{image.width}×{image.height}")


@tool(id="image-info", name="Image Info", category="Images",
      summary="Dimensions, colour mode, DPI, EXIF camera data and file size at a glance.",
      keywords="image info exif metadata dimensions dpi camera",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.flag("exif", "Include EXIF camera data", True)])
def image_info(v, ctx):
    path = need_file(v["file"], "Image")
    image = _open(path)
    info = {
        "file": path.name,
        "format": image.format,
        "dimensions": f"{image.width}×{image.height}",
        "megapixels": round(image.width * image.height / 1_000_000, 2),
        "colour_mode": image.mode,
        "file_size": human_size(path.stat().st_size),
        "dpi": image.info.get("dpi", "(not recorded)"),
        "has_transparency": image.mode in ("RGBA", "LA", "P") and "transparency" in image.info or image.mode == "RGBA",
    }
    if v["exif"]:
        try:
            from PIL.ExifTags import TAGS
            raw = image.getexif()
            tags = {TAGS.get(tag, tag): str(value)[:120] for tag, value in raw.items()}
            if tags:
                ctx.log("EXIF")
                for tag, value in list(tags.items())[:30]:
                    ctx.log(f"  {tag}: {value}")
                info["exif"] = tags
        except Exception:  # noqa: BLE001 - EXIF is best-effort
            ctx.log("(no readable EXIF)")
    return info


@tool(id="image-strip-metadata", name="Remove Image Metadata", category="Images",
      summary="Strip EXIF, GPS and camera data from photos before sharing them.",
      keywords="exif strip metadata privacy gps remove",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.save("output", "Save as", required=False, filters=IMAGE_FILTER)])
def image_strip_metadata(v, ctx):
    from PIL import Image
    path = need_file(v["file"], "Image")
    with Image.open(path) as raw:
        raw.load()
        clean = raw.copy()
    clean.info = {}
    target = _single_output(v, path, "-clean", path.suffix or ".png")
    target.parent.mkdir(parents=True, exist_ok=True)
    fmt = {"jpg": "JPEG", "jpeg": "JPEG", "tif": "TIFF"}.get(
        target.suffix.lower().lstrip("."), target.suffix.lstrip(".").upper() or "PNG")
    params = {"exif": b""}
    if fmt == "JPEG" and clean.mode in ("RGBA", "LA", "P"):
        clean = clean.convert("RGB")
    clean.save(target, format=fmt, **params)
    ctx.output(str(target))
    return f"Metadata removed → {target.name}"


@tool(id="image-batch-resize", name="Batch Resize Images", category="Images",
      summary="Resize a whole folder of images to one maximum size, in one go.",
      keywords="batch resize folder images bulk thumbnails",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder of images"),
              F.integer("max_width", "Maximum width (px)", 1600, minimum=16, maximum=20000),
              F.integer("quality", "Quality", 85, minimum=10, maximum=100),
              F.folder("output", "Save into", required=False, help="Blank = alongside the originals"),
              F.flag("recursive", "Include subfolders", False)])
def image_batch_resize(v, ctx):
    from PIL import Image
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else None
    files = [p for p in iter_files(root, v["recursive"], "*")
             if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")]
    if not files:
        raise ToolError("No images found in that folder")
    done = 0
    for index, path in enumerate(files, start=1):
        ctx.check_cancel()
        image = _open(path)
        if image.width > v["max_width"]:
            ratio = v["max_width"] / image.width
            image = image.resize((v["max_width"], max(1, int(image.height * ratio))), Image.LANCZOS)
        target = (out_dir or path.parent) / path.name
        _save(image, target, v["quality"])
        done += 1
        ctx.progress(index / len(files) * 100, path.name)
    return f"Resized {done} image(s)"


@tool(id="image-batch-convert", name="Batch Convert Images", category="Images",
      summary="Convert every image in a folder to one format, with a size report.",
      keywords="batch convert folder images format bulk",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder of images"),
              F.choice("format", "Convert to", FORMATS, "WEBP"),
              F.integer("quality", "Quality", 85, minimum=10, maximum=100),
              F.folder("output", "Save into", required=False),
              F.flag("recursive", "Include subfolders", False)])
def image_batch_convert(v, ctx):
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else None
    ext = "." + {"JPEG": "jpg", "TIFF": "tif"}.get(v["format"], v["format"].lower())
    files = [p for p in iter_files(root, v["recursive"], "*")
             if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif")]
    if not files:
        raise ToolError("No images found in that folder")
    before = after = 0
    for index, path in enumerate(files, start=1):
        ctx.check_cancel()
        image = _open(path)
        target = (out_dir or path.parent) / (path.stem + ext)
        _save(image, target, v["quality"])
        before += path.stat().st_size
        after += target.stat().st_size
        ctx.progress(index / len(files) * 100, path.name)
    return (f"Converted {len(files)} image(s) to {v['format']}: "
            f"{human_size(before)} → {human_size(after)}")


@tool(id="image-thumbnails", name="Make Thumbnails", category="Images",
      summary="Square-cropped thumbnails for a whole folder — perfect for cards and galleries.",
      keywords="thumbnail thumbs gallery preview square batch",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder of images"),
              F.integer("size", "Thumbnail size (px)", 400, minimum=32, maximum=2000),
              F.folder("output", "Save into", required=False),
              F.choice("format", "Format", ["JPEG", "PNG", "WEBP"], "JPEG")])
def image_thumbnails(v, ctx):
    from PIL import Image
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else root / "thumbnails"
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [p for p in iter_files(root, False, "*")
             if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")]
    if not files:
        raise ToolError("No images found in that folder")
    ext = "." + {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[v["format"]]
    size = v["size"]
    for index, path in enumerate(files, start=1):
        ctx.check_cancel()
        image = _open(path)
        side = min(image.size)
        left = (image.width - side) // 2
        top = (image.height - side) // 2
        square = image.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
        _save(square, out_dir / (path.stem + ext), 85)
        ctx.progress(index / len(files) * 100, path.name)
    return f"{len(files)} thumbnail(s) in {out_dir}"


@tool(id="image-adjust", name="Adjust Brightness & Colour", category="Images",
      summary="Brighten, darken, add contrast, saturation or blur in one pass.",
      keywords="brightness contrast saturation colour adjust filter blur sharpen",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.integer("brightness", "Brightness", 100, minimum=10, maximum=300, suffix="%"),
              F.integer("contrast", "Contrast", 100, minimum=10, maximum=300, suffix="%"),
              F.integer("saturation", "Saturation", 100, minimum=0, maximum=300, suffix="%"),
              F.integer("sharpness", "Sharpness", 100, minimum=0, maximum=300, suffix="%"),
              F.integer("blur", "Blur radius (0 = none)", 0, minimum=0, maximum=50),
              F.save("output", "Save as", required=False, filters=IMAGE_FILTER)])
def image_adjust(v, ctx):
    from PIL import ImageEnhance, ImageFilter
    path = need_file(v["file"], "Image")
    image = _open(path)
    for key, enhancer in (("brightness", ImageEnhance.Brightness),
                          ("contrast", ImageEnhance.Contrast),
                          ("saturation", ImageEnhance.Color),
                          ("sharpness", ImageEnhance.Sharpness)):
        if v[key] != 100:
            image = enhancer(image).enhance(v[key] / 100)
    if v["blur"]:
        image = image.filter(ImageFilter.GaussianBlur(v["blur"]))
    target = _single_output(v, path, "-adjusted", path.suffix or ".png")
    _save(image, target, 92)
    ctx.output(str(target))
    return f"Adjusted → {target.name}"


@tool(id="image-effect", name="Apply an Effect", category="Images",
      summary="Grayscale, sepia, invert, pixelate, sketch or posterise an image.",
      keywords="effect filter grayscale sepia invert pixelate sketch posterise",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.choice("effect", "Effect", ["Grayscale", "Sepia", "Invert", "Pixelate",
                                            "Sketch", "Posterise", "Edge enhance"],
                       "Grayscale"),
              F.integer("strength", "Strength", 8, minimum=2, maximum=64),
              F.save("output", "Save as", required=False, filters=IMAGE_FILTER)])
def image_effect(v, ctx):
    from PIL import Image, ImageFilter, ImageOps
    path = need_file(v["file"], "Image")
    image = _open(path).convert("RGB")
    effect = v["effect"]
    if effect == "Grayscale":
        result = ImageOps.grayscale(image).convert("RGB")
    elif effect == "Sepia":
        gray = ImageOps.grayscale(image)
        result = ImageOps.colorize(gray, black="#3b2412", white="#ffe9c4", mid="#a67b4f")
    elif effect == "Invert":
        result = ImageOps.invert(image)
    elif effect == "Pixelate":
        small = image.resize((max(1, image.width // v["strength"]),
                              max(1, image.height // v["strength"])), Image.NEAREST)
        result = small.resize(image.size, Image.NEAREST)
    elif effect == "Sketch":
        result = image.filter(ImageFilter.CONTOUR)
    elif effect == "Posterise":
        result = ImageOps.posterize(image, max(1, min(8, v["strength"] // 4)))
    else:
        result = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
    target = _single_output(v, path, "-" + effect.lower(), path.suffix or ".png")
    _save(result, target, 92)
    ctx.output(str(target))
    return f"{effect} applied → {target.name}"


@tool(id="image-border", name="Add a Border", category="Images",
      summary="Frame an image with a solid border or padding — great for social posts.",
      keywords="border frame padding margin outline",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.integer("width", "Border width (px)", 24, minimum=1, maximum=500),
              F.color("colour", "Colour", "#ffffff"),
              F.save("output", "Save as", required=False, filters=IMAGE_FILTER)])
def image_border(v, ctx):
    from PIL import ImageOps
    path = need_file(v["file"], "Image")
    image = _open(path)
    colour = v["colour"].lstrip("#")
    rgb = tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4)) if len(colour) == 6 else (255, 255, 255)
    result = ImageOps.expand(image, border=v["width"], fill=rgb)
    target = _single_output(v, path, "-bordered", path.suffix or ".png")
    _save(result, target, 92)
    ctx.output(str(target))
    return f"{image.width}×{image.height} → {result.width}×{result.height}  ({target.name})"


@tool(id="image-contact-sheet", name="Contact Sheet", category="Images",
      summary="Tile a folder of images into one overview sheet with captions.",
      keywords="contact sheet montage grid tile overview",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder of images"),
              F.integer("columns", "Columns", 5, minimum=1, maximum=20),
              F.integer("cell", "Cell size (px)", 240, minimum=48, maximum=1200),
              F.color("background", "Background", "#111827"),
              F.save("output", "Save sheet as", required=True, filters=IMAGE_FILTER)])
def image_contact_sheet(v, ctx):
    from PIL import Image, ImageDraw
    root = need_dir(v["folder"])
    files = sorted(p for p in iter_files(root, False, "*")
                   if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp"))
    if not files:
        raise ToolError("No images found in that folder")
    cell, cols = v["cell"], v["columns"]
    label_height = max(14, cell // 10)
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + label_height)),
                      _hex(v["background"]))
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(files):
        ctx.check_cancel()
        image = _open(path)
        image.thumbnail((cell - 8, cell - 8))
        col, row = index % cols, index // cols
        x = col * cell + (cell - image.width) // 2
        y = row * (cell + label_height) + (cell - image.height) // 2
        sheet.paste(image.convert("RGB"), (x, y))
        draw.text((col * cell + 4, row * (cell + label_height) + cell), path.stem[:28],
                  fill="#d1d5db")
    target = out_path(v["output"], "contact-sheet.jpg")
    _save(sheet, target, 88)
    ctx.output(str(target))
    return f"{len(files)} image(s) tiled into {sheet.width}×{sheet.height}"


@tool(id="image-colours", name="Dominant Colours", category="Images",
      summary="The main colours in an image with their hex codes — for palettes and themes.",
      keywords="colour color palette dominant hex extract",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.integer("count", "How many colours", 8, minimum=1, maximum=20)])
def image_colours(v, ctx):
    from PIL import Image
    path = need_file(v["file"], "Image")
    image = _open(path).convert("RGB")
    image.thumbnail((240, 240))
    quantised = image.quantize(colors=v["count"], method=Image.MEDIANCUT)
    palette = quantised.getpalette() or []
    counts = sorted(quantised.getcolors() or [], reverse=True)
    rows = []
    total = sum(count for count, _ in counts) or 1
    for count, index in counts[:v["count"]]:
        rgb = tuple(palette[index * 3:index * 3 + 3])
        rows.append({"hex": "#%02x%02x%02x" % rgb, "rgb": ", ".join(map(str, rgb)),
                     "share": f"{count / total * 100:.1f}%"})
    ctx.log("\n".join(f"{r['hex']}  {r['share']}  ({r['rgb']})" for r in rows))
    return rows


@tool(id="image-split-tiles", name="Split Image Into Tiles", category="Images",
      summary="Cut an image into a grid of equal tiles — for puzzles, maps and carousels.",
      keywords="split tiles grid cut puzzle carousel",
      needs=("pillow",),
      fields=[F.file("file", "Image", filters=IMAGE_FILTER),
              F.integer("rows", "Rows", 3, minimum=1, maximum=20),
              F.integer("columns", "Columns", 3, minimum=1, maximum=20),
              F.folder("output", "Save into", required=False)])
def image_split_tiles(v, ctx):
    path = need_file(v["file"], "Image")
    image = _open(path)
    out_dir = Path(v["output"]) if v["output"].strip() else path.parent / f"{path.stem}-tiles"
    out_dir.mkdir(parents=True, exist_ok=True)
    tile_w, tile_h = image.width // v["columns"], image.height // v["rows"]
    count = 0
    for row in range(v["rows"]):
        for col in range(v["columns"]):
            box = (col * tile_w, row * tile_h, (col + 1) * tile_w, (row + 1) * tile_h)
            target = out_dir / f"{path.stem}-r{row + 1}c{col + 1}.png"
            _save(image.crop(box), target)
            count += 1
    ctx.output(str(out_dir))
    return f"{count} tile(s) of {tile_w}×{tile_h} in {out_dir}"


@tool(id="image-stitch", name="Join Images", category="Images",
      summary="Place several images side by side or stacked into one picture.",
      keywords="join stitch combine side by side stack collage",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder of images"),
              F.choice("direction", "Arrange", ["Side by side", "Stacked vertically", "Grid"], "Side by side"),
              F.integer("columns", "Grid columns", 3, minimum=1, maximum=10),
              F.integer("gap", "Gap between images (px)", 8, minimum=0, maximum=100),
              F.color("background", "Background", "#ffffff"),
              F.save("output", "Save as", required=True, filters=IMAGE_FILTER)])
def image_stitch(v, ctx):
    from PIL import Image
    root = need_dir(v["folder"])
    files = sorted(p for p in iter_files(root, False, "*")
                   if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp"))
    if not files:
        raise ToolError("No images found in that folder")
    images = [_open(p).convert("RGB") for p in files]
    gap = v["gap"]
    direction = v["direction"]
    if direction == "Side by side":
        width = sum(i.width for i in images) + gap * (len(images) - 1)
        height = max(i.height for i in images)
        canvas = Image.new("RGB", (width, height), _hex(v["background"]))
        x = 0
        for image in images:
            canvas.paste(image, (x, (height - image.height) // 2))
            x += image.width + gap
    elif direction == "Stacked vertically":
        width = max(i.width for i in images)
        height = sum(i.height for i in images) + gap * (len(images) - 1)
        canvas = Image.new("RGB", (width, height), _hex(v["background"]))
        y = 0
        for image in images:
            canvas.paste(image, ((width - image.width) // 2, y))
            y += image.height + gap
    else:
        cols = v["columns"]
        cell_w = max(i.width for i in images)
        cell_h = max(i.height for i in images)
        rows = (len(images) + cols - 1) // cols
        canvas = Image.new("RGB", (cols * (cell_w + gap) + gap, rows * (cell_h + gap) + gap),
                           _hex(v["background"]))
        for index, image in enumerate(images):
            col, row = index % cols, index // cols
            canvas.paste(image, (gap + col * (cell_w + gap), gap + row * (cell_h + gap)))
    target = out_path(v["output"], "joined.png")
    _save(canvas, target, 92)
    ctx.output(str(target))
    return f"{len(images)} image(s) → {canvas.width}×{canvas.height}  ({target.name})"


@tool(id="image-to-ico", name="Make a Windows Icon", category="Images",
      summary="Turn an image into a multi-size .ico file for apps, folders and shortcuts.",
      keywords="ico icon favicon windows app shortcut",
      needs=("pillow",),
      fields=[F.file("file", "Image (square works best)", filters=IMAGE_FILTER),
              F.save("output", "Save as", required=True, filters="Icon (*.ico)")])
def image_to_ico(v, ctx):
    path = need_file(v["file"], "Image")
    image = _open(path).convert("RGBA")
    side = min(image.size)
    image = image.crop(((image.width - side) // 2, (image.height - side) // 2,
                        (image.width + side) // 2, (image.height + side) // 2))
    target = out_path(v["output"], path.stem + ".ico")
    if target.suffix.lower() != ".ico":
        target = target.with_suffix(".ico")
    image.save(target, format="ICO",
               sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    ctx.output(str(target))
    return f"Icon with 7 sizes written to {target.name}"


@tool(id="image-folder-report", name="Image Folder Report", category="Images",
      summary="Count and total the images in a folder by format, with resolution warnings.",
      keywords="images report folder count formats dimensions audit",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder"),
              F.save("report", "Save CSV to", required=False)])
def image_folder_report(v, ctx):
    from ._util import write_csv
    root = need_dir(v["folder"])
    rows = []
    for path in iter_files(root, True):
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"):
            continue
        ctx.check_cancel()
        try:
            image = _open(path)
            rows.append({"name": path.name, "format": image.format, "width": image.width,
                         "height": image.height, "bytes": path.stat().st_size})
        except ToolError:
            continue
    if not rows:
        return "No readable images found."
    by_format: dict[str, dict] = {}
    for row in rows:
        entry = by_format.setdefault(row["format"] or "?", {"format": row["format"], "count": 0, "bytes": 0})
        entry["count"] += 1
        entry["bytes"] += row["bytes"]
    for entry in by_format.values():
        entry["size"] = human_size(entry["bytes"])
    ctx.log(report_table(sorted(by_format.values(), key=lambda r: r["bytes"], reverse=True),
                         ["format", "count", "size"]))
    if v["report"].strip():
        target = write_csv(out_path(v["report"], "images.csv"), rows)
        ctx.output(str(target))
    return f"{len(rows)} image(s), {len(by_format)} format(s)"
