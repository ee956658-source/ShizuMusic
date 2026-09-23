"""Create a branded music-player thumbnail from a YouTube thumbnail."""
from __future__ import annotations

import io
import os
import re
import textwrap
import tempfile
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


def _thumbnail_candidates(url: str) -> list[str]:
    """Return several known-good YouTube thumbnail URLs.

    Some YouTube search results expose a thumbnail variant that can be opened by
    Telegram but intermittently fails when fetched by aiohttp.  When possible,
    derive the video id and try the stable img.youtube.com variants as well.
    """
    clean = (url or "").split("?", 1)[0].strip()
    candidates: list[str] = []

    def add(value: str):
        if value and value not in candidates:
            candidates.append(value)

    add(clean)

    # i.ytimg.com/vi/<id>/<variant>.jpg
    match = re.search(r"(?:i\.ytimg\.com|img\.youtube\.com)/vi/([^/]+)/", clean)
    if match:
        video_id = match.group(1)
        for variant in ("maxresdefault.jpg", "hq720.jpg", "sddefault.jpg", "hqdefault.jpg"):
            add(f"https://i.ytimg.com/vi/{video_id}/{variant}")
            add(f"https://img.youtube.com/vi/{video_id}/{variant}")

    return candidates


async def _download(url: str) -> bytes:
    timeout = aiohttp.ClientTimeout(total=15, connect=8, sock_read=12)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://www.youtube.com/",
    }

    last_error = None
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        for candidate in _thumbnail_candidates(url):
            for attempt in range(2):
                try:
                    async with session.get(candidate, allow_redirects=True) as resp:
                        if resp.status != 200:
                            raise RuntimeError(f"HTTP {resp.status}")
                        raw = await resp.read()
                        if len(raw) < 1024:
                            raise RuntimeError("thumbnail response was too small")
                        # Verify that the bytes really are an image before using them.
                        with Image.open(io.BytesIO(raw)) as image:
                            image.verify()
                        return raw
                except Exception as exc:
                    last_error = exc
                    if attempt == 0:
                        continue

    raise RuntimeError(f"could not download thumbnail: {last_error}")


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


async def _download_via_telegram(bot, chat_id: int, url: str) -> bytes:
    """Use Telegram as a relay when the hosting server cannot fetch YouTube.

    Telegram can often fetch the same thumbnail URL even when the bot host's
    outbound DNS/network cannot. The temporary message is deleted immediately
    after its photo is downloaded.
    """
    temp = None
    tmp_path = None
    try:
        temp = await bot.send_photo(chat_id, photo=url)
        fd, tmp_path = tempfile.mkstemp(prefix="shizu_thumb_", suffix=".jpg")
        os.close(fd)
        downloaded = await bot.download_media(temp, file_name=tmp_path)
        if not downloaded:
            raise RuntimeError("Telegram thumbnail download returned no file")
        raw = Path(downloaded).read_bytes()
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
        return raw
    finally:
        if temp is not None:
            try:
                await temp.delete()
            except Exception:
                pass
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass


async def make_player_thumbnail(
    url: str,
    title: str,
    duration: str,
    bot=None,
    chat_id: int | None = None,
) -> str | None:
    if not url:
        return None

    try:
        raw = await _download(url)
        return _build(raw, title, duration)
    except Exception as direct_error:
        # Do not silently fall back to Telegram's raw YouTube thumbnail.
        # Relay it through Telegram and build the branded card from the bytes.
        if bot is not None and chat_id is not None:
            try:
                raw = await _download_via_telegram(bot, chat_id, url)
                return _build(raw, title, duration)
            except Exception as relay_error:
                try:
                    from ShizuMusic import LOGGER
                    LOGGER.warning(
                        f"[PLAYER THUMB] generation failed: direct={direct_error!r}, relay={relay_error!r}"
                    )
                except Exception:
                    pass
        else:
            try:
                from ShizuMusic import LOGGER
                LOGGER.warning(f"[PLAYER THUMB] direct generation failed: {direct_error!r}")
            except Exception:
                pass

    return None
