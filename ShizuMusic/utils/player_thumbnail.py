"""Create a branded music-player thumbnail from a YouTube thumbnail."""
from __future__ import annotations

import io
import os
import textwrap
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


_CACHE = Path("/tmp/shizu_player_thumbs")
_CACHE.mkdir(parents=True, exist_ok=True)


def _font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def _circle_crop(image: Image.Image, size: int) -> Image.Image:
    image = ImageOps.fit(image.convert("RGB"), (size, size), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(image, (0, 0), mask)
    return out


async def _download(url: str) -> bytes:
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            resp.raise_for_status()
            return await resp.read()


def _build(raw: bytes, title: str, duration: str) -> str:
    src = Image.open(io.BytesIO(raw)).convert("RGB")
    W, H = 1000, 560

    # Blurred/darkened copy gives the same polished music-card feel while keeping
    # the original artwork visible behind the player information.
    bg = ImageOps.fit(src, (W, H), method=Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(16))
    bg = ImageEnhance.Brightness(bg).enhance(0.42)
    bg = ImageEnhance.Contrast(bg).enhance(1.08)
    canvas = bg.convert("RGBA")

    # Dark translucent overlay.
    overlay = Image.new("RGBA", (W, H), (8, 10, 18, 105))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    # Artwork circle.
    art_size = 300
    art = _circle_crop(src, art_size)
    x, y = 72, 130
    draw.ellipse((x - 9, y - 9, x + art_size + 9, y + art_size + 9), fill=(235, 190, 0, 235))
    canvas.alpha_composite(art, (x, y))

    # Branding and title.
    brand_font = _font(32, True)
    title_font = _font(36, True)
    meta_font = _font(20, False)
    small_font = _font(18, False)

    draw.text((70, 52), "YOR × MUSIC  🎧", font=brand_font, fill=(255, 255, 255, 245))

    title_lines = textwrap.wrap(str(title or "Unknown Song"), width=27)[:3]
    tx, ty = 430, 155
    for line in title_lines:
        draw.text((tx, ty), line, font=title_font, fill=(255, 255, 255, 250))
        ty += 48

    draw.text((tx, ty + 8), "RM music  |  YouTube", font=meta_font, fill=(225, 225, 225, 225))

    # Fake player progress line — the actual live progress is shown by the bot
    # controls underneath the message, so this is only visual decoration.
    py = 365
    draw.rounded_rectangle((430, py, 895, py + 8), radius=4, fill=(210, 210, 210, 90))
    draw.rounded_rectangle((430, py, 670, py + 8), radius=4, fill=(235, 205, 25, 230))
    draw.ellipse((662, py - 6, 678, py + 14), fill=(235, 205, 25, 255))
    draw.text((430, py + 28), "00:00", font=small_font, fill=(235, 235, 235, 210))
    draw.text((840, py + 28), str(duration or "0:00"), font=small_font, fill=(235, 235, 235, 210))

    # Decorative controls inside the thumbnail.
    controls = ["↝", "|◀", "▶", "▶|", "□"]
    cx = 500
    for symbol in controls:
        draw.text((cx, 445), symbol, font=_font(27, True), fill=(255, 255, 255, 235))
        cx += 82

    out = _CACHE / f"{abs(hash((title, duration, len(raw))))}.jpg"
    canvas.convert("RGB").save(out, "JPEG", quality=90, optimize=True)
    return str(out)


async def make_player_thumbnail(url: str, title: str, duration: str) -> str | None:
    if not url:
        return None
    try:
        raw = await _download(url)
        return _build(raw, title, duration)
    except Exception:
        return None
