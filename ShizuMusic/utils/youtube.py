# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import logging
import os
import re
from typing import Union

import aiofiles
import aiohttp
import yt_dlp
from py_yt import Playlist, VideosSearch
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from ShizuMusic.utils.formatters import sec_to_iso

logger = logging.getLogger(__name__)

# ── API config ────────────────────────────────────────────────────────────────
# NexGenBots (primary — fastest)
NEXGEN_API_URL = os.environ.get(
    "NEXGEN_API_URL",
    "https://pvtz.nexgenbots.xyz",
)
NEXGEN_VIDEO_API_URL = os.environ.get(
    "NEXGEN_VIDEO_API_URL",
    "https://api.video.nexgenbots.xyz",
)
NEXGEN_API_KEY = os.environ.get(
    "NEXGEN_API_KEY",
    "30DxNexGenBots66383d",
)

# Shruti (fallback)
SHRUTI_API_URL = os.environ.get(
    "SHRUTI_API_URL",
    "https://api.shrutibots.site",
)
SHRUTI_API_KEY = os.environ.get(
    "SHRUTI_API_KEY",
    "ShrutiBots88hgntDhLBAxmui2bE72",
)

DOWNLOAD_DIR = "downloads"
SHRUTI_TOKEN_TIMEOUT = 10
SHRUTI_STREAM_TIMEOUT = 900
NEXGEN_TIMEOUT = 0.9  # ultra-tight — race with yt-dlp, don't block

# ── Caches ───────────────────────────────────────────────────────────────────
_file_cache: dict[str, str] = {}
_search_cache: dict[str, tuple] = {}
_playlist_cache: dict[str, dict] = {}

# Prevent two requests from downloading the same song simultaneously.
_download_locks: dict[str, asyncio.Lock] = {}

_http_session: aiohttp.ClientSession | None = None


# ═════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _extract_video_id(url: str) -> str:
    """Extract raw YouTube video ID from common URL formats."""
    url = str(url).strip()

    if "youtu.be/" in url:
        value = url.split("youtu.be/", 1)[1]
        return value.split("?", 1)[0].split("&", 1)[0].split("/", 1)[0]

    if "watch?v=" in url:
        value = url.split("watch?v=", 1)[1]
        return value.split("&", 1)[0].split("#", 1)[0]

    if "youtube.com/shorts/" in url:
        value = url.split("youtube.com/shorts/", 1)[1]
        return value.split("?", 1)[0].split("&", 1)[0].split("/", 1)[0]

    if "youtube.com/embed/" in url:
        value = url.split("youtube.com/embed/", 1)[1]
        return value.split("?", 1)[0].split("&", 1)[0].split("/", 1)[0]

    return url


def _cleanup(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def time_to_seconds(time) -> int:
    """Convert M:SS or H:MM:SS string to total seconds."""
    stringt = str(time)

    try:
        return sum(
            int(x) * 60 ** i
            for i, x in enumerate(reversed(stringt.split(":")))
        )
    except Exception:
        return 0


def _get_lock(key: str) -> asyncio.Lock:
    lock = _download_locks.get(key)

    if lock is None:
        lock = asyncio.Lock()
        _download_locks[key] = lock

    return lock


async def _get_http_session() -> aiohttp.ClientSession:
    """Reuse one HTTP session instead of creating a new connection every song."""
    global _http_session

    if _http_session is None or _http_session.closed:
        timeout = aiohttp.ClientTimeout(
            total=SHRUTI_STREAM_TIMEOUT,
            connect=SHRUTI_TOKEN_TIMEOUT,
            sock_connect=SHRUTI_TOKEN_TIMEOUT,
            sock_read=SHRUTI_STREAM_TIMEOUT,
        )

        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=10,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
        )

        _http_session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
        )

    return _http_session


def _parse_duration(value) -> int:
    if isinstance(value, dict):
        value = (
            value.get("secondsText")
            or value.get("simpleText")
            or value.get("text")
            or 0
        )

    if isinstance(value, int):
        return value

    value = str(value or "0").strip()

    try:
        if ":" in value:
            return time_to_seconds(value)

        return int(value)
    except Exception:
        return 0


# ═════════════════════════════════════════════════════════════════════════════
# DOWNLOAD HELPERS
# ═════════════════════════════════════════════════════════════════════════════

async def download_song(link: str) -> str:
    """Download audio via Shruti API. Returns local file path or None."""
    video_id = _extract_video_id(link)

    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_path = os.path.join(
        DOWNLOAD_DIR,
        f"{video_id}.mp3",
    )

    # Fast disk cache.
    if os.path.exists(file_path):
        try:
            if os.path.getsize(file_path) > 0:
                return file_path
        except Exception:
            pass

    lock = _get_lock(video_id)

    async with lock:

        # Another request may have completed it while we waited.
        if os.path.exists(file_path):
            try:
                if os.path.getsize(file_path) > 0:
                    return file_path
            except Exception:
                pass

        temp_path = file_path + ".part"

        _cleanup(temp_path)

        try:
            session = await _get_http_session()

            async with session.get(
                f"{SHRUTI_API_URL}/download",
                params={
                    "url": video_id,
                    "type": "audio",
                    "api_key": SHRUTI_API_KEY,
                },
            ) as resp:

                if resp.status != 200:
                    logger.warning(
                        f"[shruti] Audio download failed: HTTP {resp.status}"
                    )
                    return None

                async with aiofiles.open(temp_path, "wb") as f:

                    async for chunk in resp.content.iter_chunked(262144):
                        if chunk:
                            await f.write(chunk)

            if (
                os.path.exists(temp_path)
                and os.path.getsize(temp_path) > 0
            ):
                os.replace(temp_path, file_path)
                return file_path

            return None

        except asyncio.CancelledError:
            _cleanup(temp_path)
            raise

        except Exception as e:
            logger.error(
                f"[shruti] download_song error: {e}"
            )
            _cleanup(temp_path)
            return None


async def download_video(link: str) -> str:
    """Download video via Shruti API. Returns local file path or None."""
    video_id = _extract_video_id(link)

    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_path = os.path.join(
        DOWNLOAD_DIR,
        f"{video_id}.mp4",
    )

    if os.path.exists(file_path):
        try:
            if os.path.getsize(file_path) > 0:
                return file_path
        except Exception:
            pass

    lock = _get_lock(f"video:{video_id}")

    async with lock:

        if os.path.exists(file_path):
            try:
                if os.path.getsize(file_path) > 0:
                    return file_path
            except Exception:
                pass

        temp_path = file_path + ".part"

        _cleanup(temp_path)

        try:
            session = await _get_http_session()

            async with session.get(
                f"{SHRUTI_API_URL}/download",
                params={
                    "url": video_id,
                    "type": "video",
                    "api_key": SHRUTI_API_KEY,
                },
            ) as resp:

                if resp.status != 200:
                    logger.warning(
                        f"[shruti] Video download failed: HTTP {resp.status}"
                    )
                    return None

                async with aiofiles.open(temp_path, "wb") as f:

                    async for chunk in resp.content.iter_chunked(262144):
                        if chunk:
                            await f.write(chunk)

            if (
                os.path.exists(temp_path)
                and os.path.getsize(temp_path) > 0
            ):
                os.replace(temp_path, file_path)
                return file_path

            return None

        except asyncio.CancelledError:
            _cleanup(temp_path)
            raise

        except Exception as e:
            logger.error(
                f"[shruti] download_video error: {e}"
            )
            _cleanup(temp_path)
            return None


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — STREAM RESOLVER
# ═════════════════════════════════════════════════════════════════════════════

async def _nexgen_stream(video_id: str, video: bool = False) -> str | None:
    """Fetch playable stream URL from NexGenBots API (fast path)."""
    if not NEXGEN_API_KEY or not video_id:
        return None

    try:
        session = await _get_http_session()
        if video:
            api_url = f"{NEXGEN_VIDEO_API_URL}/video/{video_id}"
        else:
            api_url = f"{NEXGEN_API_URL}/song/{video_id}"

        async with session.get(
            api_url,
            params={"api": NEXGEN_API_KEY},
            timeout=aiohttp.ClientTimeout(total=NEXGEN_TIMEOUT, connect=0.6),
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json(content_type=None)
            link = data.get("link") if isinstance(data, dict) else None
            if link and (data.get("status") in ("done", "ok", None) or True):
                if link.startswith("http"):
                    logger.info(f"[nexgen] Stream OK ({'video' if video else 'audio'})")
                    return link
    except asyncio.TimeoutError:
        logger.debug("[nexgen] Timeout")
    except Exception as e:
        logger.debug(f"[nexgen] Failed: {e}")
    return None


async def resolve_stream(url: str, video: bool = False) -> str:
    """
    Ultra-fast stream resolver.
    Strategy: cache → disk → NexGen stream → download fallback.
    Target: < 1.5s on warm path, < 2.5s on cold path.
    """
    if os.path.exists(url) and os.path.isfile(url):
        return url

    cache_key = f"{'v:' if video else 'a:'}{url}"
    cached = _file_cache.get(cache_key) or _file_cache.get(url)
    if cached:
        if os.path.exists(cached) and os.path.isfile(cached):
            logger.info("[cache] file hit")
            return cached
        if isinstance(cached, str) and cached.startswith("http"):
            logger.info("[cache] url hit")
            return cached

    video_id = _extract_video_id(url)
    ext = "mp4" if video else "mp3"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")
    if video_id and os.path.exists(file_path):
        try:
            if os.path.getsize(file_path) > 0:
                _file_cache[cache_key] = file_path
                return file_path
        except Exception:
            pass

    # ── PRIMARY: NexGen stream only ─────────────────────────────────────────
    # Direct yt-dlp extraction is intentionally disabled in this variant.
    winner = await _nexgen_stream(video_id, video=video) if video_id else None

    # ── Last resort: full download (slow) ────────────────────────────────────
    logger.info(f"[download] fallback: {video_id}")
    if video:
        downloaded = await download_video(url)
    else:
        downloaded = await download_song(url)

    if downloaded:
        _file_cache[cache_key] = downloaded
        return downloaded

    raise Exception("Stream failed. Please try again.")


async def resolve_direct_stream(url: str, video: bool = False) -> str | None:
    """Get a temporary YouTube stream URL as fast as possible."""
    if os.path.exists(url) and os.path.isfile(url):
        return url

    try:
        def _extract():
            # Maximum speed options — android client only, skip heavy work
            fmt = (
                "best[height<=720][ext=mp4]/best[height<=720]/best"
                if video
                else "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best"
            )
            options = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "format": fmt,
                "skip_download": True,
                "socket_timeout": 3,
                "retries": 0,
                "fragment_retries": 0,
                "nocheckcertificate": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android"],
                        "player_skip": ["webpage", "configs", "js", "initial_data"],
                    }
                },
                "http_headers": {
                    "User-Agent": (
                        "com.google.android.youtube/19.09.37 "
                        "(Linux; U; Android 13) gzip"
                    ),
                },
            }
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None
                if info.get("url"):
                    return info["url"]
                formats = info.get("formats") or []
                # Prefer progressive / direct audio
                for f in formats:
                    if f.get("url") and f.get("acodec") not in (None, "none"):
                        if not video or f.get("vcodec") not in (None, "none"):
                            return f["url"]
                for f in formats:
                    if f.get("url"):
                        return f["url"]
                return None

        direct_url = await asyncio.wait_for(
            asyncio.to_thread(_extract),
            timeout=2.8,  # hard cap — don't let yt-dlp block longer
        )
        if direct_url:
            logger.info("[youtube] Direct stream OK")
            return direct_url
    except asyncio.TimeoutError:
        logger.warning("[youtube] Direct stream timeout (2.8s)")
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.warning(f"[youtube] Direct stream failed: {e}")

    return None


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — YOUTUBE SEARCH / METADATA
# ═════════════════════════════════════════════════════════════════════════════

async def search_yt(query: str):
    """
    Search YouTube for a video or playlist.

    Results are cached in memory so repeated requests don't hit
    YouTube search again.
    """

    query = str(query).strip()

    if not query:
        raise Exception("ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ")

    cache_key = query.lower()

    # ── Cached result ────────────────────────────────────────────────────────
    cached = _search_cache.get(cache_key)

    if cached is not None:
        logger.info(f"[youtube] Search cache hit: {query}")
        return cached

    # ── Playlist ─────────────────────────────────────────────────────────────
    if (
        "playlist?list=" in query
        or "&list=" in query
    ):
        playlist_cache_key = f"playlist:{cache_key}"

        cached_playlist = _playlist_cache.get(
            playlist_cache_key
        )

        if cached_playlist is not None:
            logger.info(
                f"[youtube] Playlist cache hit: {query}"
            )
            return cached_playlist

        pl = await Playlist.get(query)

        vids = pl.get("videos") or []

        if not vids:
            raise Exception("ᴩʟᴀʏʟɪsᴛ ɪs ᴇᴍᴩᴛʏ")

        items = []

        for v in vids:
            if not v:
                continue

            vid_id = v.get("id")

            if not vid_id:
                continue

            secs = _parse_duration(
                v.get("duration")
            )

            thumbs = v.get("thumbnails") or []

            thumb = ""

            if thumbs:
                thumb = (
                    thumbs[0].get("url", "")
                    .split("?", 1)[0]
                )

            items.append(
                {
                    "link": (
                        "https://www.youtube.com/watch?v="
                        + vid_id
                    ),
                    "title": v.get(
                        "title",
                        "Unknown",
                    ),
                    "duration": sec_to_iso(secs),
                    "thumbnail": thumb,
                }
            )

        result = {
            "playlist": items
        }

        _playlist_cache[playlist_cache_key] = result

        return result

    # ── Fast path: query is already a YouTube URL ────────────────────────────
    # Skip VideosSearch (slow) and extract metadata directly with yt-dlp.
    is_yt_url = (
        "youtube.com" in query
        or "youtu.be" in query
        or re.match(r"^[a-zA-Z0-9_-]{11}$", query)
    )

    if is_yt_url:
        try:
            def _meta():
                opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "skip_download": True,
                    "socket_timeout": 4,
                    "extractor_args": {
                        "youtube": {
                            "player_client": ["android"],
                            "player_skip": ["webpage", "configs", "js"],
                        }
                    },
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(query, download=False)
                    return info

            info = await asyncio.wait_for(
                asyncio.to_thread(_meta),
                timeout=2.5,
            )
            if info:
                vid = info.get("id") or _extract_video_id(query)
                url = f"https://www.youtube.com/watch?v={vid}"
                title = info.get("title") or "Unknown"
                secs = int(info.get("duration") or 0)
                thumb = (
                    info.get("thumbnail")
                    or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
                )
                result = (url, title, sec_to_iso(secs), thumb)
                _search_cache[cache_key] = result
                logger.info("[youtube] URL fast-path metadata OK")
                return result
        except Exception as e:
            logger.warning(f"[youtube] URL fast-path failed, falling to search: {e}")

    # ── Normal search (song name) ────────────────────────────────────────────
    logger.info(f"[youtube] Searching: {query}")

    try:
        search = VideosSearch(query, limit=1)
        results = await asyncio.wait_for(search.next(), timeout=3.5)
    except asyncio.TimeoutError:
        raise Exception("Search timeout — try again or use YouTube link")
    except Exception as e:
        logger.warning(f"[youtube] Search error: {e}")
        raise Exception("ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ")

    lst = results.get("result") or []

    if not lst:
        raise Exception("ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ")

    r = lst[0]
    video_id = r.get("id")
    if not video_id:
        raise Exception("ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ")

    url = r.get("link") or f"https://www.youtube.com/watch?v={video_id}"
    title = r.get("title", "Unknown")
    thumbs = r.get("thumbnails") or []
    thumb = ""
    if thumbs:
        thumb = thumbs[0].get("url", "").split("?", 1)[0]
    dur = r.get("duration", "0:00")
    secs = _parse_duration(dur)

    result = (url, title, sec_to_iso(secs), thumb)
    _search_cache[cache_key] = result
    return result


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — YouTubeAPI CLASS
# ═════════════════════════════════════════════════════════════════════════════

class YouTubeAPI:

    def __init__(self):
        self.base = (
            "https://www.youtube.com/watch?v="
        )

        self.regex = r"(?:youtube\.com|youtu\.be)"

        self.status = (
            "https://www.youtube.com/oembed?url="
        )

        self.listbase = (
            "https://youtube.com/playlist?list="
        )

        self.reg = re.compile(
            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_link(
        self,
        link: str,
        videoid,
    ) -> str:
        return (
            self.base + link
            if videoid
            else link
        )

    def _strip_extra(
        self,
        link: str,
    ) -> str:
        return (
            link.split("&", 1)[0]
            if "&" in link
            else link
        )

    # ── Public methods ───────────────────────────────────────────────────────

    async def exists(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ) -> bool:
        if videoid:
            link = self.base + link

        return bool(
            re.search(
                self.regex,
                link,
            )
        )

    async def url(
        self,
        message_1: Message,
    ) -> Union[str, None]:

        messages = [message_1]

        if message_1.reply_to_message:
            messages.append(
                message_1.reply_to_message
            )

        for message in messages:

            if message.entities:

                for entity in message.entities:

                    if entity.type == MessageEntityType.URL:

                        text = (
                            message.text
                            or message.caption
                            or ""
                        )

                        return text[
                            entity.offset:
                            entity.offset + entity.length
                        ]

            elif message.caption_entities:

                for entity in message.caption_entities:

                    if (
                        entity.type
                        == MessageEntityType.TEXT_LINK
                    ):
                        return entity.url

        return None

    async def details(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        link = self._strip_extra(
            self._build_link(
                link,
                videoid,
            )
        )

        results = VideosSearch(
            link,
            limit=1,
        )

        for result in (
            await results.next()
        )["result"]:

            title = result["title"]

            duration_min = result["duration"]

            thumbnail = (
                result["thumbnails"][0]["url"]
                .split("?", 1)[0]
            )

            vidid = result["id"]

            duration_sec = (
                int(time_to_seconds(duration_min))
                if duration_min
                else 0
            )

            return (
                title,
                duration_min,
                duration_sec,
                thumbnail,
                vidid,
            )

        return None

    async def title(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ) -> str:

        link = self._strip_extra(
            self._build_link(
                link,
                videoid,
            )
        )

        results = VideosSearch(
            link,
            limit=1,
        )

        for result in (
            await results.next()
        )["result"]:

            return result["title"]

        return None

    async def duration(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ) -> str:

        link = self._strip_extra(
            self._build_link(
                link,
                videoid,
            )
        )

        results = VideosSearch(
            link,
            limit=1,
        )

        for result in (
            await results.next()
        )["result"]:

            return result["duration"]

        return None

    async def thumbnail(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ) -> str:

        link = self._strip_extra(
            self._build_link(
                link,
                videoid,
            )
        )

        results = VideosSearch(
            link,
            limit=1,
        )

        for result in (
            await results.next()
        )["result"]:

            return (
                result["thumbnails"][0]["url"]
                .split("?", 1)[0]
            )

        return None

    async def video(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        link = self._strip_extra(
            self._build_link(
                link,
                videoid,
            )
        )

        try:
            downloaded_file = (
                await download_video(link)
            )

            if downloaded_file:
                return 1, downloaded_file

            return 0, "Video download failed"

        except Exception as e:
            return (
                0,
                f"Video download error: {e}",
            )

    async def playlist(
        self,
        link: str,
        limit: int,
        user_id,
        videoid: Union[bool, str] = None,
    ) -> list:

        if videoid:
            link = self.listbase + link

        link = self._strip_extra(link)

        try:
            plist = await Playlist.get(link)
        except Exception:
            return []

        videos = plist.get("videos") or []

        ids = []

        for data in videos[:limit]:

            if not data:
                continue

            vid = data.get("id")

            if not vid:
                continue

            ids.append(vid)

        return ids

    async def track(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        link = self._strip_extra(
            self._build_link(
                link,
                videoid,
            )
        )

        results = VideosSearch(
            link,
            limit=1,
        )

        data = (
            await results.next()
        ).get("result") or []

        if not data:
            return None, None

        result = data[0]

        title = result["title"]
        duration_min = result["duration"]
        vidid = result["id"]
        yturl = result["link"]

        thumbnail = (
            result["thumbnails"][0]["url"]
            .split("?", 1)[0]
        )

        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }

        return track_details, vidid

    async def formats(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        link = self._strip_extra(
            self._build_link(
                link,
                videoid,
            )
        )

        ytdl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }

        ydl = yt_dlp.YoutubeDL(
            ytdl_opts
        )

        with ydl:

            formats_available = []

            r = ydl.extract_info(
                link,
                download=False,
            )

            for fmt in r.get("formats", []):

                try:

                    if "dash" not in str(
                        fmt["format"]
                    ).lower():

                        formats_available.append(
                            {
                                "format": fmt["format"],
                                "filesize": fmt.get(
                                    "filesize"
                                ),
                                "format_id": fmt[
                                    "format_id"
                                ],
                                "ext": fmt["ext"],
                                "format_note": fmt.get(
                                    "format_note"
                                ),
                                "yturl": link,
                            }
                        )

                except Exception:
                    continue

        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):

        link = self._strip_extra(
            self._build_link(
                link,
                videoid,
            )
        )

        a = VideosSearch(
            link,
            limit=10,
        )

        result = (
            await a.next()
        ).get("result") or []

        if not result:
            return None

        item = result[query_type]

        title = item["title"]
        duration_min = item["duration"]
        vidid = item["id"]

        thumbnail = (
            item["thumbnails"][0]["url"]
            .split("?", 1)[0]
        )

        return (
            title,
            duration_min,
            thumbnail,
            vidid,
        )

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ):

        if videoid:
            link = self.base + link

        try:

            if video:
                downloaded_file = (
                    await download_video(link)
                )
            else:
                downloaded_file = (
                    await download_song(link)
                )

            if downloaded_file:
                return downloaded_file, True

            return None, False

        except Exception:
            return None, False
