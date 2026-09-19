# --------------------------------------------------------------------------------
# AI provider helpers for ShizuMusic.
# Gemini is attempted first; Groq is used as a fallback.
# --------------------------------------------------------------------------------
import aiohttp
import config

async def _post_json(url, payload, headers=None):
    timeout = aiohttp.ClientTimeout(total=config.AI_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload, headers=headers or {}) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                detail = data.get("error", data) if isinstance(data, dict) else data
                raise RuntimeError(f"HTTP {resp.status}: {detail}")
            return data

async def ask_gemini(prompt: str) -> str:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
    )
    payload = {
        "system_instruction": {
            "parts": [{"text": config.AI_SYSTEM_PROMPT}]
        },
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "maxOutputTokens": config.AI_MAX_TOKENS,
            "temperature": 0.7,
        },
    }
    data = await _post_json(url, payload)
    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {data}") from exc
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text

async def ask_groq(prompt: str) -> str:
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    url = f"{config.GROQ_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": config.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": config.AI_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": config.AI_MAX_TOKENS,
        "temperature": 0.7,
    }
    data = await _post_json(
        url,
        payload,
        headers={
            "Authorization": f"Bearer {config.GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        text = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Groq response: {data}") from exc
    if not text:
        raise RuntimeError("Groq returned an empty response.")
    return text

async def ask_ai(prompt: str):
    """Return (answer, provider). Gemini first, Groq fallback."""
    errors = []
    if config.GEMINI_API_KEY:
        try:
            return await ask_gemini(prompt), "Gemini"
        except Exception as exc:
            errors.append(f"Gemini: {exc}")
    if config.GROQ_API_KEY:
        try:
            return await ask_groq(prompt), "Groq"
        except Exception as exc:
            errors.append(f"Groq: {exc}")
    if not errors:
        raise RuntimeError("No AI API key is configured.")
    raise RuntimeError(" | ".join(errors))
