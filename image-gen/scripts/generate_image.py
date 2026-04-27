#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pillow>=10.0.0",
# ]
# ///
"""
Image generation tool supporting multiple providers via local proxy.

Supported models:
  gemini-3.1-flash-image-preview  — fast, auto resolution
  gpt-image-2                     — OpenAI images API, controllable size
  grok-4.2-image                  — returns remote URL, ~2K fixed

Usage:
  uv run generate_image.py --prompt "..." --filename "out.png" [--model MODEL] [--resolution 1K|2K|4K]
  uv run generate_image.py --prompt "..." --filename "out.png" --input-image in.png
  uv run generate_image.py --gallery gallery.html  # gallery-only (rebuild from metadata)
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from io import BytesIO
from pathlib import Path

# ── Hardcoded proxy config ────────────────────────────────────────────────────
_BASE_URL = "http://localhost:8090"
_API_KEY = "ah-c9ddc8a3e4879254db216db4266fcfddbe3c35a3ea37ddcdfb6df07c8ee745a4"

# ── Resolution → pixel size mapping ──────────────────────────────────────────
# Used for gpt-image-2 (which actually honours the size param).
# gemini and grok don't support server-side size control through this proxy.
_RESOLUTION_TO_SIZE = {
    "1K": "1024x1024",
    "2K": "2048x2048",
    "4K": "4096x4096",  # gpt-image-2 may not support this; falls back to 2K
}

# ── Model routing ─────────────────────────────────────────────────────────────
_IMAGES_GENERATIONS_MODELS = {"gpt-image-2"}
_CHAT_COMPLETIONS_MODELS = {"gemini-3.1-flash-image-preview", "grok-4.2-image"}
_ALL_KNOWN_MODELS = _IMAGES_GENERATIONS_MODELS | _CHAT_COMPLETIONS_MODELS


# ── Error types ───────────────────────────────────────────────────────────────
class RetryableError(RuntimeError):
    pass


class NoImageError(RuntimeError):
    pass


# ── HTTP helpers ──────────────────────────────────────────────────────────────
def _is_retryable(text: str) -> bool:
    markers = (
        "overloaded", "524", "timeout", "temporarily unavailable",
        "rate limit", "gateway timeout", "upstream",
    )
    return any(m in text.lower() for m in markers)


# Per-model timeout floor (ms).  gpt-image-2 2K can take >2 min.
_MODEL_TIMEOUT_FLOOR_MS: dict[str, int] = {
    "gpt-image-2": 300_000,          # 5 min
    "grok-4.2-image": 180_000,       # 3 min
    "gemini-3.1-flash-image-preview": 120_000,  # 2 min
}
_DEFAULT_TIMEOUT_MS = 300_000  # conservative global default


def _effective_timeout_ms(requested_ms: int, model: str) -> int:
    """Return max(requested, model floor) so callers can't accidentally set too low."""
    floor = _MODEL_TIMEOUT_FLOOR_MS.get(model, _DEFAULT_TIMEOUT_MS)
    return max(requested_ms, floor)


def _post_json(url: str, payload: dict, timeout_ms: int) -> dict:
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "curl/8.7.1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_ms / 1000) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except (TimeoutError, OSError) as exc:
        # TimeoutError is a subclass of OSError, NOT urllib.error.URLError.
        # Without this explicit branch it propagates uncaught and skips retry.
        msg = str(exc)
        if isinstance(exc, TimeoutError) or _is_retryable(msg):
            raise RetryableError(f"Request timed out after {timeout_ms/1000:.0f}s") from exc
        raise RuntimeError(f"OS/network error: {msg}") from exc
    except urllib.error.URLError as exc:
        msg = str(exc)
        if _is_retryable(msg):
            raise RetryableError(msg) from exc
        raise RuntimeError(f"Network error: {msg}") from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        if _is_retryable(body):
            raise RetryableError(body)
        raise RuntimeError(f"Non-JSON (HTTP {status}): {body[:300]}")

    if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
        err = parsed["error"]
        msg = f"{err.get('code', '')} {err.get('message', '')}".strip()
        if _is_retryable(msg):
            raise RetryableError(msg)
        raise RuntimeError(f"API error: {msg}")

    if status >= 500:
        if _is_retryable(body):
            raise RetryableError(f"HTTP {status}")
        raise RuntimeError(f"Server error (HTTP {status}): {body[:200]}")
    if status >= 400:
        raise RuntimeError(f"Request failed (HTTP {status}): {body[:200]}")
    return parsed


def _retry(fn, *, label: str, max_retries: int, backoff_ms: int):
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except RetryableError:
            if attempt >= max_retries:
                raise
            wait = (backoff_ms * (2 ** (attempt - 1))) / 1000
            print(f"  Retrying {label} ({attempt}/{max_retries})…", file=sys.stderr)
            time.sleep(wait)


def _download_url(url: str, timeout_ms: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.7.1"})
    with urllib.request.urlopen(req, timeout=timeout_ms / 1000) as resp:
        return resp.read()


# ── Image extraction helpers ──────────────────────────────────────────────────
def _parse_data_url(text: str) -> tuple[bytes, str] | None:
    m = re.search(r"data:(image/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=\s]+)", text, re.DOTALL)
    if not m:
        return None
    mime = m.group(1)
    try:
        data = base64.b64decode(re.sub(r"\s+", "", m.group(2)))
    except Exception as exc:
        raise NoImageError(f"Invalid base64: {exc}") from exc
    return data, mime


def _extract_from_chat_content(content) -> tuple[bytes, str]:
    """Parse image from chat/completions message content.

    Handles:
    - string with data:image URL   (gemini)
    - string with markdown URL     (grok → download)
    - list of content blocks
    """
    if isinstance(content, str):
        # Try inline data URL
        parsed = _parse_data_url(content)
        if parsed:
            return parsed

        # Try markdown image URL: ![...](https://...)
        m = re.search(r"!\[.*?\]\((https?://[^\s\)]+)\)", content)
        if m:
            url = m.group(1)
            print(f"  Downloading image from remote URL: {url[:80]}…")
            raw = _download_url(url, timeout_ms=60000)
            return raw, "image/png"

        # Try bare URL
        m = re.search(r"(https?://\S+\.(?:png|jpg|jpeg|webp))", content, re.IGNORECASE)
        if m:
            url = m.group(1)
            print(f"  Downloading image from URL: {url[:80]}…")
            raw = _download_url(url, timeout_ms=60000)
            return raw, "image/png"

        raise NoImageError(f"No image payload in content string: {content[:200]}")

    if isinstance(content, list):
        texts = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if "image_url" in item:
                url_obj = item["image_url"]
                if isinstance(url_obj, dict):
                    url_str = url_obj.get("url", "")
                else:
                    url_str = str(url_obj)
                parsed = _parse_data_url(url_str)
                if parsed:
                    return parsed
            if isinstance(item.get("text"), str):
                texts.append(item["text"])
        preview = " ".join(texts).strip()
        raise NoImageError(f"No image in content list. Text: {preview[:200]}")

    raise NoImageError("Unsupported content format.")


# ── Provider implementations ──────────────────────────────────────────────────
def _generate_chat_completions(
    *,
    prompt: str,
    model: str,
    size_str: str,
    input_image_path: str | None,
    max_retries: int,
    backoff_ms: int,
    timeout_ms: int,
) -> tuple[bytes, str]:
    """Generic /v1/chat/completions handler (gemini, grok)."""
    endpoint = _BASE_URL.rstrip("/") + "/v1/chat/completions"
    suffix = f" Return only the image, no text. Target resolution: {size_str}."

    if input_image_path:
        path = Path(input_image_path)
        raw = path.read_bytes()
        import mimetypes
        mime, _ = mimetypes.guess_type(str(path))
        if not mime:
            mime = "image/png"
        enc = base64.b64encode(raw).decode()
        user_content = [
            {"type": "text", "text": prompt + suffix},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{enc}"}},
        ]
    else:
        user_content = prompt + suffix

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_content}],
        "temperature": 0,
    }

    resp = _retry(
        lambda: _post_json(endpoint, payload, timeout_ms),
        label=model,
        max_retries=max_retries,
        backoff_ms=backoff_ms,
    )
    choices = resp.get("choices")
    if not isinstance(choices, list) or not choices:
        raise NoImageError("No choices in response.")
    content = choices[0].get("message", {}).get("content")
    return _extract_from_chat_content(content)


def _generate_images_generations(
    *,
    prompt: str,
    model: str,
    size_str: str,
    input_image_path: str | None,
    max_retries: int,
    backoff_ms: int,
    timeout_ms: int,
) -> tuple[bytes, str]:
    """OpenAI /v1/images/generations handler (gpt-image-2)."""
    endpoint = _BASE_URL.rstrip("/") + "/v1/images/generations"

    if input_image_path:
        # images/generations doesn't support image editing — fall back to chat/completions
        print(f"  Note: {model} editing uses chat/completions fallback.")
        return _generate_chat_completions(
            prompt=prompt,
            model=model,
            size_str=size_str,
            input_image_path=input_image_path,
            max_retries=max_retries,
            backoff_ms=backoff_ms,
            timeout_ms=timeout_ms,
        )

    payload = {
        "model": model,
        "prompt": prompt,
        "size": size_str,
        "response_format": "b64_json",
        "n": 1,
    }

    resp = _retry(
        lambda: _post_json(endpoint, payload, timeout_ms),
        label=model,
        max_retries=max_retries,
        backoff_ms=backoff_ms,
    )

    data = resp.get("data")
    if not isinstance(data, list) or not data:
        raise NoImageError("No data in images/generations response.")
    item = data[0]
    if "b64_json" in item:
        return base64.b64decode(item["b64_json"]), "image/png"
    if "url" in item:
        print(f"  Downloading from URL: {item['url'][:80]}…")
        raw = _download_url(item["url"], timeout_ms=timeout_ms)
        return raw, "image/png"
    raise NoImageError(f"Unexpected item keys: {list(item.keys())}")


# ── Image saving ──────────────────────────────────────────────────────────────
def _save_png(image_data: bytes, output_path: Path) -> tuple[int, int]:
    """Save image as PNG, return actual (width, height)."""
    from PIL import Image as PILImage

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = PILImage.open(BytesIO(image_data))
    w, h = img.size
    if img.mode == "RGBA":
        bg = PILImage.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        bg.save(str(output_path), "PNG")
    elif img.mode == "RGB":
        img.save(str(output_path), "PNG")
    else:
        img.convert("RGB").save(str(output_path), "PNG")
    return w, h


# ── Gallery HTML ──────────────────────────────────────────────────────────────
_GALLERY_META_SUFFIX = ".meta.json"

_GALLERY_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Image Review</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:        #f0eee6;
  --surface:   #ffffff;
  --border:    #e8e6dc;
  --border-md: #ccc9be;
  --text:      #131314;
  --sub:       #87867f;
  --muted:     #b0aea5;
  --accent:    #d97757;
  --approve:   #2d7a4f;
  --reject:    #b54040;
  --pending-dot: #d97757;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
  min-height: 100vh;
  padding: 48px 40px 80px;
}

/* ── Header ─────────────────────── */
.header {
  display: flex; align-items: baseline; gap: 16px;
  margin-bottom: 36px; border-bottom: 1px solid var(--border); padding-bottom: 20px;
}
.header h1 {
  font-size: 1.05rem; font-weight: 600; letter-spacing: -.01em; color: var(--text);
}
.header-stats { font-size: .8rem; color: var(--sub); margin-left: auto; }

/* ── Toolbar ────────────────────── */
.toolbar {
  display: flex; gap: 10px; align-items: center;
  margin-bottom: 28px; flex-wrap: wrap;
}
.tb-select, .tb-input {
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text); padding: 7px 12px; border-radius: 6px;
  font-size: .8rem; font-family: inherit; outline: none;
  transition: border-color .15s;
}
.tb-select:focus, .tb-input:focus { border-color: var(--border-md); }
.tb-input { min-width: 200px; }
.tb-input::placeholder { color: var(--muted); }

/* ── Grid ───────────────────────── */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

/* ── Card ───────────────────────── */
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; overflow: hidden; cursor: pointer;
  transition: box-shadow .18s, border-color .18s;
}
.card:hover { box-shadow: 0 4px 20px rgba(0,0,0,.09); border-color: var(--border-md); }
.card.approved { border-color: #a3c9b0; }
.card.rejected  { border-color: #d9aaaa; opacity: .6; }

.card-img {
  position: relative; background: var(--bg);
  aspect-ratio: 1/1; overflow: hidden;
}
.card-img img {
  width: 100%; height: 100%; object-fit: cover; display: block;
  transition: transform .22s;
}
.card:hover .card-img img { transform: scale(1.04); }

/* Status pill on image */
.st-pill {
  position: absolute; bottom: 8px; left: 8px;
  font-size: .62rem; font-weight: 600; letter-spacing: .05em;
  text-transform: uppercase; padding: 2px 8px; border-radius: 20px;
  pointer-events: none;
}
.st-pill.pending  { background: rgba(240,238,230,.88); color: var(--sub);   border: 1px solid var(--border); }
.st-pill.approved { background: rgba(45,122,79,.1);    color: var(--approve); border: 1px solid rgba(45,122,79,.3); }
.st-pill.rejected { background: rgba(181,64,64,.1);    color: var(--reject);  border: 1px solid rgba(181,64,64,.28); }

/* Card footer */
.card-foot {
  padding: 10px 12px 8px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 8px;
}
.card-name {
  font-size: .75rem; color: var(--text); flex: 1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.card-model {
  font-size: .65rem; color: var(--sub); background: var(--bg);
  border: 1px solid var(--border); padding: 1px 6px; border-radius: 4px;
  white-space: nowrap; flex-shrink: 0;
}

/* Card actions */
.card-actions { display: flex; }
.ca-btn {
  flex: 1; padding: 8px 4px; border: none; background: none;
  font-size: .75rem; font-weight: 500; cursor: pointer; font-family: inherit;
  color: var(--sub); transition: background .12s, color .12s;
}
.ca-btn:first-child { border-right: 1px solid var(--border); }
.ca-btn:hover { background: var(--bg); }
.ca-btn.ca-on.ca-approve { color: var(--approve); background: rgba(45,122,79,.06); }
.ca-btn.ca-on.ca-reject  { color: var(--reject);  background: rgba(181,64,64,.06); }

/* ── Modal overlay ──────────────── */
#modal {
  display: none; position: fixed; inset: 0;
  background: rgba(19,19,20,.55); z-index: 9999;
  align-items: center; justify-content: center;
  padding: 24px;
}
#modal.open { display: flex; }

.m-box {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; overflow: hidden;
  display: flex; width: min(980px, 100%); max-height: 92vh;
  box-shadow: 0 24px 64px rgba(0,0,0,.18);
}

/* Image pane */
.m-img-pane {
  flex: 1; background: var(--bg); display: flex;
  align-items: center; justify-content: center;
  position: relative; overflow: hidden; min-width: 0;
}
.m-img-pane img {
  max-width: 100%; max-height: 92vh; object-fit: contain;
  display: block; user-select: none;
}

.nav {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 34px; height: 34px; border-radius: 50%;
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text); font-size: .85rem; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: box-shadow .14s, border-color .14s; z-index: 2;
}
.nav:hover { box-shadow: 0 2px 8px rgba(0,0,0,.12); border-color: var(--border-md); }
.nav:disabled { opacity: .25; cursor: default; pointer-events: none; }
#nav-prev { left: 12px; }
#nav-next { right: 12px; }

/* Info pane */
.m-info {
  width: 300px; flex-shrink: 0; border-left: 1px solid var(--border);
  display: flex; flex-direction: column; overflow: hidden;
}

.m-header {
  padding: 16px 18px 14px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 10px;
}
.m-title {
  flex: 1; font-size: .85rem; font-weight: 600;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text);
}
.m-close {
  background: none; border: none; color: var(--muted); font-size: 1rem;
  cursor: pointer; padding: 3px 5px; border-radius: 4px;
  transition: color .12s; flex-shrink: 0;
}
.m-close:hover { color: var(--text); }

.m-body {
  flex: 1; overflow-y: auto; padding: 18px;
  display: flex; flex-direction: column; gap: 18px;
}
.m-body::-webkit-scrollbar { width: 4px; }
.m-body::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* Status in modal */
.m-st-row { display: flex; align-items: center; gap: 7px; }
.m-st-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.m-st-dot.pending  { background: var(--pending-dot); }
.m-st-dot.approved { background: var(--approve); }
.m-st-dot.rejected { background: var(--reject); }
.m-st-label { font-size: .78rem; text-transform: capitalize; color: var(--sub); }

/* Section */
.sec-label {
  font-size: .67rem; text-transform: uppercase; letter-spacing: .08em;
  color: var(--muted); margin-bottom: 6px;
}
.m-prompt {
  font-size: .82rem; line-height: 1.65; color: var(--text);
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 6px; padding: 10px 12px;
}

/* Meta */
.m-meta { display: flex; flex-direction: column; gap: 5px; }
.m-row  { display: flex; gap: 8px; align-items: baseline; }
.m-key  { font-size: .7rem; color: var(--muted); width: 78px; flex-shrink: 0; }
.m-val  { font-size: .78rem; color: var(--sub); }
.m-tag  {
  font-size: .68rem; background: var(--bg); border: 1px solid var(--border);
  color: var(--text); padding: 1px 6px; border-radius: 4px;
}

/* Modal actions */
.m-actions { display: flex; gap: 8px; }
.m-btn {
  flex: 1; padding: 8px 0; border-radius: 6px; border: 1px solid var(--border);
  background: var(--surface); font-size: .8rem; font-weight: 500;
  cursor: pointer; font-family: inherit; color: var(--sub);
  transition: background .12s, border-color .12s, color .12s;
}
.m-btn:hover { background: var(--bg); }
.m-btn.m-approve.active { background: rgba(45,122,79,.08); border-color: rgba(45,122,79,.4); color: var(--approve); }
.m-btn.m-reject.active  { background: rgba(181,64,64,.07); border-color: rgba(181,64,64,.35); color: var(--reject); }

.m-counter { font-size: .72rem; color: var(--muted); text-align: center; padding-top: 2px; }
.m-hint    { font-size: .65rem; color: #c8c4bc; text-align: center; line-height: 1.8; }
</style>
</head>
<body>

<div class="header">
  <h1>Image Review</h1>
  <span class="header-stats" id="stats"></span>
</div>

<div class="toolbar">
  <select class="tb-select" id="filterModel" onchange="render()">
    <option value="">All models</option>
    MODELOPTIONS
  </select>
  <select class="tb-select" id="filterStatus" onchange="render()">
    <option value="">All statuses</option>
    <option value="pending">Pending</option>
    <option value="approved">Approved</option>
    <option value="rejected">Rejected</option>
  </select>
  <input class="tb-input" id="search" type="text" placeholder="Search prompt…" oninput="render()">
</div>

<div class="grid" id="grid"></div>

<!-- Modal -->
<div id="modal" onclick="handleOverlayClick(event)">
  <div class="m-box">
    <div class="m-img-pane" id="m-img-pane">
      <img id="m-img" src="" alt="">
      <button class="nav" id="nav-prev" onclick="navModal(-1);event.stopPropagation()">&#8592;</button>
      <button class="nav" id="nav-next" onclick="navModal( 1);event.stopPropagation()">&#8594;</button>
    </div>
    <div class="m-info">
      <div class="m-header">
        <span class="m-title" id="m-title"></span>
        <button class="m-close" onclick="closeModal()">&#10005;</button>
      </div>
      <div class="m-body">
        <div>
          <div class="sec-label">Status</div>
          <div class="m-st-row">
            <div class="m-st-dot" id="m-st-dot"></div>
            <span class="m-st-label" id="m-st-label"></span>
          </div>
        </div>
        <div>
          <div class="sec-label">Prompt</div>
          <div class="m-prompt" id="m-prompt"></div>
        </div>
        <div>
          <div class="sec-label">Details</div>
          <div class="m-meta" id="m-meta"></div>
        </div>
        <div>
          <div class="m-actions">
            <button class="m-btn m-approve" id="m-approve" onclick="modalToggle('approved')">Approve</button>
            <button class="m-btn m-reject"  id="m-reject"  onclick="modalToggle('rejected')">Reject</button>
          </div>
          <div class="m-counter" id="m-counter"></div>
          <div class="m-hint">&#8592; &#8594; &nbsp;navigate &nbsp;&nbsp; A &nbsp;approve &nbsp;&nbsp; R &nbsp;reject &nbsp;&nbsp; Esc &nbsp;close</div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const RAW = JSONDATA;
let vis  = [];
let midx = -1;

const stKey = id => 'img-st-' + id;
const getSt  = id => localStorage.getItem(stKey(id)) || 'pending';
const setSt  = (id, v) => localStorage.setItem(stKey(id), v);

function toggleSt(id, target) {
  setSt(id, getSt(id) === target ? 'pending' : target);
  render();
  if (midx >= 0) renderModal();
}

function cardToggle(e, btn) {
  e.stopPropagation();
  toggleSt(btn.dataset.id, btn.dataset.tgt);
}

function shortM(m) {
  return m.replace('gemini-3.1-flash-image-preview', 'gemini-flash')
          .replace('gemini-3-pro-image-preview', 'gemini-pro')
          .replace('gpt-image-2', 'gpt-image-2')
          .replace('grok-4.2-image', 'grok');
}

function render() {
  const fm = document.getElementById('filterModel').value;
  const fs = document.getElementById('filterStatus').value;
  const sq = document.getElementById('search').value.toLowerCase();
  vis = RAW.filter(item => {
    if (fm && item.model !== fm) return false;
    const s = getSt(item.id);
    if (fs && s !== fs) return false;
    if (sq && !item.prompt.toLowerCase().includes(sq)) return false;
    return true;
  });
  const total = RAW.length;
  const shown = vis.length;
  document.getElementById('stats').textContent =
    shown === total ? total + ' images' : shown + ' of ' + total + ' images';

  document.getElementById('grid').innerHTML = vis.map((item, i) => {
    const s   = getSt(item.id);
    const cc  = s !== 'pending' ? s : '';
    const aOn = s === 'approved' ? ' ca-on ca-approve' : '';
    const rOn = s === 'rejected' ? ' ca-on ca-reject'  : '';
    const fn  = item.filename.length > 26 ? item.filename.slice(0, 23) + '...' : item.filename;
    return '<div class="card ' + cc + '" onclick="openModal(' + i + ')">' +
      '<div class="card-img">' +
        '<img src="' + item.src + '" alt="' + item.filename + '" loading="lazy">' +
        '<span class="st-pill ' + s + '">' + s + '</span>' +
      '</div>' +
      '<div class="card-foot">' +
        '<span class="card-name" title="' + item.filename + '">' + fn + '</span>' +
        '<span class="card-model">' + shortM(item.model) + '</span>' +
      '</div>' +
      '<div class="card-actions">' +
        '<button class="ca-btn' + aOn + '" data-id="' + item.id + '" data-tgt="approved" onclick="cardToggle(event,this)">Approve</button>' +
        '<button class="ca-btn' + rOn + '" data-id="' + item.id + '" data-tgt="rejected" onclick="cardToggle(event,this)">Reject</button>' +
      '</div></div>';
  }).join('');
}

function openModal(i) {
  midx = i;
  renderModal();
  document.getElementById('modal').classList.add('open');
}

function renderModal() {
  const item = vis[midx];
  const s    = getSt(item.id);
  document.getElementById('m-img').src = item.src;
  document.getElementById('m-title').textContent = item.filename;
  const dot = document.getElementById('m-st-dot');
  dot.className = 'm-st-dot ' + s;
  document.getElementById('m-st-label').textContent = s;
  document.getElementById('m-prompt').textContent = item.prompt;
  document.getElementById('m-meta').innerHTML =
    row('Model',      '<span class="m-tag">' + item.model + '</span>') +
    row('Resolution', item.resolution) +
    row('Size',       item.actual_size) +
    row('File',       item.filename) +
    row('Time',       item.timestamp.slice(0, 16).replace('T', ' '));
  document.getElementById('m-approve').className = 'm-btn m-approve' + (s === 'approved' ? ' active' : '');
  document.getElementById('m-reject' ).className = 'm-btn m-reject'  + (s === 'rejected' ? ' active' : '');
  document.getElementById('m-counter').textContent = (midx + 1) + ' / ' + vis.length;
  document.getElementById('nav-prev').disabled = midx <= 0;
  document.getElementById('nav-next').disabled = midx >= vis.length - 1;
}

function row(k, v) {
  return '<div class="m-row"><span class="m-key">' + k + '</span><span class="m-val">' + v + '</span></div>';
}

function modalToggle(target) {
  if (midx < 0) return;
  toggleSt(vis[midx].id, target);
}

function navModal(d) {
  const n = midx + d;
  if (n < 0 || n >= vis.length) return;
  midx = n;
  renderModal();
}

function closeModal() {
  document.getElementById('modal').classList.remove('open');
  midx = -1;
}

function handleOverlayClick(e) {
  if (e.target === document.getElementById('modal')) closeModal();
}

document.addEventListener('keydown', e => {
  if (!document.getElementById('modal').classList.contains('open')) return;
  if (e.key === 'Escape')     closeModal();
  if (e.key === 'ArrowLeft')  navModal(-1);
  if (e.key === 'ArrowRight') navModal(1);
  if (e.key === 'a' || e.key === 'A') modalToggle('approved');
  if (e.key === 'r' || e.key === 'R') modalToggle('rejected');
});

render();
</script>
</body>
</html>
"""


def _gallery_meta_path(gallery_path: Path) -> Path:
    return gallery_path.with_suffix("").with_name(gallery_path.stem + _GALLERY_META_SUFFIX)


def _load_gallery_meta(gallery_path: Path) -> list[dict]:
    meta_path = _gallery_meta_path(gallery_path)
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text())
        except Exception:
            pass
    return []


def _save_gallery(gallery_path: Path, items: list[dict]) -> None:
    """Write the gallery HTML and metadata JSON."""
    meta_path = _gallery_meta_path(gallery_path)
    meta_path.write_text(json.dumps(items, indent=2, ensure_ascii=False))

    # Build model options
    models = sorted({i["model"] for i in items})
    model_opts = "\n    ".join(
        f'<option value="{m}">{m}</option>' for m in models
    )

    html = _GALLERY_HTML_TEMPLATE.replace("MODELOPTIONS", model_opts).replace(
        "JSONDATA", json.dumps(items, ensure_ascii=False)
    )
    gallery_path.write_text(html, encoding="utf-8")
    print(f"Gallery updated: {gallery_path.resolve()}  ({len(items)} images)")


def add_to_gallery(
    gallery_path: Path,
    *,
    image_path: Path,
    model: str,
    prompt: str,
    resolution: str,
    actual_size: tuple[int, int],
    timestamp: str,
) -> None:
    items = _load_gallery_meta(gallery_path)

    # Use relative path from gallery directory
    try:
        rel = os.path.relpath(str(image_path.resolve()), str(gallery_path.parent.resolve()))
    except ValueError:
        rel = str(image_path.resolve())

    item_id = f"{timestamp.replace(':','').replace('-','').replace('T','')}_{image_path.stem}"
    # Check if already present (idempotent)
    if any(i["id"] == item_id for i in items):
        return

    items.append({
        "id": item_id,
        "filename": image_path.name,
        "src": rel.replace("\\", "/"),
        "model": model,
        "prompt": prompt,
        "resolution": resolution,
        "actual_size": f"{actual_size[0]}×{actual_size[1]}",
        "timestamp": timestamp,
    })
    _save_gallery(gallery_path, items)


def rebuild_gallery(gallery_path: Path) -> None:
    """Rebuild HTML from existing metadata (no new image)."""
    items = _load_gallery_meta(gallery_path)
    if not items:
        print(f"No metadata found for {gallery_path}", file=sys.stderr)
        sys.exit(1)
    _save_gallery(gallery_path, items)


# ── Output directory resolution ──────────────────────────────────────────────
_DEFAULT_OUTPUT_DIR = Path.home() / ".local" / "share" / "image-gen"


def _resolve_output_dir(output_dir: str | None, session: str | None) -> Path:
    """Return the effective output directory.

    Priority: --output-dir > --session (under default dir) > default dir.
    """
    if output_dir:
        return Path(output_dir).expanduser()
    if session:
        return _DEFAULT_OUTPUT_DIR / session
    return _DEFAULT_OUTPUT_DIR


def _resolve_output_path(filename: str, out_dir: Path) -> Path:
    """Resolve the output image path.

    If filename is a bare name (no path separator), place it under out_dir.
    If filename contains path separators, treat as CWD-relative / absolute
    (lets callers like academic-paper write directly to figures/).
    """
    p = Path(filename)
    if p.parent == Path("."):  # bare filename, no directory component
        return out_dir / p
    return p  # caller-specified path, honour as-is


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate images via local proxy (gemini / gpt-image-2 / grok)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--prompt", "-p", help="Image description / editing instructions")
    parser.add_argument("--filename", "-f", help="Output PNG filename (bare name → output-dir; path → CWD-relative)")
    parser.add_argument("--input-image", "-i", help="Input image path (for editing)")
    parser.add_argument(
        "--resolution", "-r",
        choices=["1K", "2K", "4K"], default="1K",
        help="Target resolution: 1K≈1024, 2K≈2048, 4K≈4096 (gpt-image-2 only fully supports 1K/2K)",
    )
    parser.add_argument(
        "--model", "-m",
        default="gemini-3.1-flash-image-preview",
        choices=sorted(_ALL_KNOWN_MODELS),
        help="Model to use",
    )
    # ── Output location ──────────────────────────────────────────────────────
    out_group = parser.add_argument_group(
        "output location",
        "By default all generated files (images + gallery) go to\n"
        f"  {_DEFAULT_OUTPUT_DIR}/\n"
        "Use --session for a named subdirectory, or --output-dir for a custom path.\n"
        "If --filename contains a path separator (e.g. figures/foo.png) the image\n"
        "is written there directly (CWD-relative), bypassing output-dir.",
    )
    out_group.add_argument(
        "--session", "-s",
        metavar="NAME",
        help=f"Named sub-directory under {_DEFAULT_OUTPUT_DIR}/NAME/",
    )
    out_group.add_argument(
        "--output-dir",
        metavar="DIR",
        help="Explicit output directory (overrides --session and default)",
    )
    # ── Gallery ──────────────────────────────────────────────────────────────
    gallery_group = parser.add_argument_group(
        "gallery",
        "Gallery HTML is auto-created at <output-dir>/gallery.html unless\n"
        "overridden with --gallery or disabled with --no-gallery.",
    )
    gallery_group.add_argument(
        "--gallery", "-g",
        metavar="PATH",
        const="AUTO",
        nargs="?",
        help=(
            "Gallery HTML path (omit value → <output-dir>/gallery.html).\n"
            "Without --prompt/--filename: rebuild HTML from existing metadata."
        ),
    )
    gallery_group.add_argument(
        "--no-gallery",
        action="store_true",
        help="Disable automatic gallery creation / update.",
    )
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--retry-backoff-ms", type=int, default=1200)
    parser.add_argument(
        "--timeout-ms", type=int, default=_DEFAULT_TIMEOUT_MS,
        help=(
            f"HTTP timeout in ms (default: {_DEFAULT_TIMEOUT_MS}).\n"
            "Per-model floors are enforced even if this value is lower:\n"
            + "\n".join(f"  {m}: {v}ms" for m, v in _MODEL_TIMEOUT_FLOOR_MS.items())
        ),
    )
    args = parser.parse_args()

    # ── Resolve output dir ───────────────────────────────────────────────────
    out_dir = _resolve_output_dir(args.output_dir, args.session)

    # ── Resolve gallery path ─────────────────────────────────────────────────
    def _effective_gallery() -> Path | None:
        if args.no_gallery:
            return None
        if args.gallery is None or args.gallery == "AUTO":
            # Default: auto gallery in output dir
            return out_dir / "gallery.html"
        g = Path(args.gallery)
        if g.parent == Path("."):  # bare filename → put in output dir
            return out_dir / g
        return g

    # ── Gallery-only mode (rebuild without generating) ────────────────────────
    gallery_path = _effective_gallery()
    if not args.prompt and not args.filename:
        if gallery_path:
            rebuild_gallery(gallery_path)
        else:
            parser.error("Nothing to do: provide --prompt/--filename or a gallery path.")
        return

    if not args.prompt:
        parser.error("--prompt is required for image generation")
    if not args.filename:
        parser.error("--filename is required for image generation")

    # ── Resolve size string ──────────────────────────────────────────────────
    size_str = _RESOLUTION_TO_SIZE.get(args.resolution, "1024x1024")
    if args.model == "gpt-image-2" and args.resolution == "4K":
        print("  gpt-image-2 does not support 4K; using 2K instead.", file=sys.stderr)
        size_str = "2048x2048"

    output_path = _resolve_output_path(args.filename, out_dir)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    print(f"Model:      {args.model}")
    print(f"Resolution: {args.resolution} ({size_str})")
    print(f"Output dir: {out_dir}")
    if args.input_image:
        print(f"Input img:  {args.input_image}")
    print(f"Output:     {output_path}")
    if gallery_path:
        print(f"Gallery:    {gallery_path}")
    print()

    common_kwargs = dict(
        prompt=args.prompt,
        model=args.model,
        size_str=size_str,
        input_image_path=args.input_image,
        max_retries=args.max_retries,
        backoff_ms=args.retry_backoff_ms,
        timeout_ms=_effective_timeout_ms(args.timeout_ms, args.model),
    )

    if args.model in _IMAGES_GENERATIONS_MODELS:
        image_data, mime_type = _generate_images_generations(**common_kwargs)
    else:
        image_data, mime_type = _generate_chat_completions(**common_kwargs)

    w, h = _save_png(image_data, output_path)
    print(f"Saved: {output_path.resolve()}  ({w}\xd7{h}px, {len(image_data)//1024}KB)")

    if gallery_path:
        add_to_gallery(
            gallery_path,
            image_path=output_path,
            model=args.model,
            prompt=args.prompt,
            resolution=args.resolution,
            actual_size=(w, h),
            timestamp=timestamp,
        )


if __name__ == "__main__":
    main()
