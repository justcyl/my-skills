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
<title>🎨 Image Gallery</title>
<style>
:root {
  --bg:#0f0f13; --card:#1a1a24; --border:#2a2a3a;
  --text:#e0e0f0; --sub:#70708a; --accent:#7c6af7;
  --approve:#22c55e; --reject:#ef4444; --pending:#f59e0b;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:system-ui,sans-serif;padding:24px}

/* ── Toolbar ─────────────────────────────────── */
h1{font-size:1.35rem;margin-bottom:18px;color:var(--accent);letter-spacing:.03em}
.toolbar{display:flex;gap:10px;align-items:center;margin-bottom:20px;flex-wrap:wrap}
.toolbar select,.toolbar input{
  background:var(--card);border:1px solid var(--border);color:var(--text);
  padding:6px 11px;border-radius:7px;font-size:.85rem;outline:none
}
.toolbar select:focus,.toolbar input:focus{border-color:var(--accent)}
.stats{margin-left:auto;font-size:.78rem;color:var(--sub)}

/* ── Grid ────────────────────────────────────── */
.grid{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
  gap:12px
}

/* ── Card ────────────────────────────────────── */
.card{
  background:var(--card);border:1px solid var(--border);border-radius:10px;
  overflow:hidden;cursor:pointer;transition:transform .15s,box-shadow .15s
}
.card:hover{transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,0,0,.55)}
.card.approved{border-color:var(--approve)}
.card.rejected{border-color:var(--reject);opacity:.45}

.card-img{position:relative;background:#0d0d11;aspect-ratio:1/1;overflow:hidden}
.card-img img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .2s}
.card:hover .card-img img{transform:scale(1.03)}

/* Badge */
.badge{
  position:absolute;top:7px;right:7px;font-size:.6rem;font-weight:700;
  padding:2px 7px;border-radius:20px;text-transform:uppercase;letter-spacing:.07em;pointer-events:none
}
.badge-approved{background:var(--approve);color:#000}
.badge-rejected{background:var(--reject);color:#fff}
.badge-pending{background:rgba(245,158,11,.12);color:var(--pending);border:1px solid rgba(245,158,11,.35)}

/* Card footer */
.card-foot{
  padding:8px 10px;display:flex;align-items:center;gap:7px;
  border-top:1px solid var(--border)
}
.card-name{font-size:.72rem;color:var(--text);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-model{
  font-size:.62rem;background:rgba(124,106,247,.14);border:1px solid rgba(124,106,247,.28);
  color:var(--accent);padding:1px 6px;border-radius:8px;white-space:nowrap;flex-shrink:0
}
.card-actions{
  display:flex;gap:5px;padding:6px 8px 8px;border-top:1px solid var(--border)
}
.ca-btn{
  flex:1;padding:5px 0;border-radius:6px;border:1px solid transparent;
  cursor:pointer;font-size:.75rem;font-weight:600;transition:opacity .12s,background .12s
}
.ca-btn:hover{opacity:.8}
.ca-approve{background:rgba(34,197,94,.1);color:var(--approve);border-color:rgba(34,197,94,.25)}
.ca-approve.ca-on{background:var(--approve);color:#000;border-color:var(--approve)}
.ca-reject{background:rgba(239,68,68,.08);color:var(--reject);border-color:rgba(239,68,68,.22)}
.ca-reject.ca-on{background:var(--reject);color:#fff;border-color:var(--reject)}

/* ── Modal overlay ───────────────────────────── */
#modal{
  display:none;position:fixed;inset:0;background:rgba(6,6,10,.92);
  z-index:9999;align-items:stretch
}
#modal.open{display:flex}

/* Image pane */
.m-img-pane{
  flex:1;display:flex;align-items:center;justify-content:center;
  background:#080810;position:relative;overflow:hidden;min-width:0
}
.m-img-pane img{
  max-width:100%;max-height:100vh;object-fit:contain;display:block;
  border-radius:2px;user-select:none
}

/* Nav arrows */
.nav{
  position:absolute;top:50%;transform:translateY(-50%);
  background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);
  color:#fff;width:42px;height:42px;border-radius:50%;font-size:1.1rem;
  cursor:pointer;transition:background .15s;display:flex;align-items:center;justify-content:center;
  z-index:2;user-select:none
}
.nav:hover{background:rgba(255,255,255,.18)}
.nav:disabled{opacity:.18;cursor:default;pointer-events:none}
#nav-prev{left:14px}
#nav-next{right:14px}

/* Info pane */
.m-info{
  width:340px;flex-shrink:0;background:var(--card);
  border-left:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden
}

.m-header{
  padding:15px 16px 13px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:10px
}
.m-title{flex:1;font-size:.88rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.m-close{
  background:none;border:none;color:var(--sub);font-size:1.2rem;cursor:pointer;
  padding:2px 5px;border-radius:5px;flex-shrink:0;transition:color .15s
}
.m-close:hover{color:var(--text)}

.m-body{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:16px}
.m-body::-webkit-scrollbar{width:4px}
.m-body::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}

/* Status row */
.m-status-row{display:flex;align-items:center;gap:8px}
.sdot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.sdot-approved{background:var(--approve)}
.sdot-rejected{background:var(--reject)}
.sdot-pending{background:var(--pending)}
.stxt{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em}

/* Section label */
.sec-label{font-size:.67rem;text-transform:uppercase;letter-spacing:.09em;color:var(--sub);margin-bottom:5px}

/* Prompt box */
.m-prompt{
  font-size:.84rem;line-height:1.6;color:var(--text);
  background:rgba(255,255,255,.03);border:1px solid var(--border);
  border-radius:8px;padding:10px 12px
}

/* Meta table */
.m-meta{display:flex;flex-direction:column;gap:6px}
.m-row{display:flex;align-items:baseline;gap:8px}
.m-key{font-size:.7rem;color:var(--sub);width:82px;flex-shrink:0}
.m-val{font-size:.78rem;color:var(--text)}
.m-tag{
  font-size:.7rem;background:rgba(124,106,247,.14);border:1px solid rgba(124,106,247,.28);
  color:var(--accent);padding:1px 7px;border-radius:8px
}

/* Action buttons */
.m-actions{display:flex;gap:9px}
.m-btn{
  flex:1;padding:9px 0;border-radius:8px;border:none;cursor:pointer;
  font-size:.84rem;font-weight:600;transition:opacity .15s,transform .1s
}
.m-btn:hover{opacity:.85}
.m-btn:active{transform:scale(.97)}
.m-approve{background:var(--approve);color:#000}
.m-approve.active{box-shadow:0 0 0 2px var(--card),0 0 0 4px var(--approve)}
.m-reject{background:rgba(239,68,68,.13);color:var(--reject);border:1px solid var(--reject)}
.m-reject.active{background:rgba(239,68,68,.3);box-shadow:0 0 0 2px var(--card),0 0 0 4px var(--reject)}

/* Counter + hint */
.m-counter{font-size:.72rem;color:var(--sub);text-align:center;padding-top:3px}
.m-hint{font-size:.66rem;color:#44445a;text-align:center}
</style>
</head>
<body>
<h1>🎨 Image Review Gallery</h1>
<div class="toolbar">
  <select id="filterModel" onchange="render()">
    <option value="">All models</option>
    MODELOPTIONS
  </select>
  <select id="filterStatus" onchange="render()">
    <option value="">All statuses</option>
    <option value="pending">Pending</option>
    <option value="approved">Approved</option>
    <option value="rejected">Rejected</option>
  </select>
  <input id="search" type="text" placeholder="Search prompt…" oninput="render()">
  <span class="stats" id="stats"></span>
</div>
<div class="grid" id="grid"></div>

<!-- Modal -->
<div id="modal">
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
        <div class="m-status-row">
          <div class="sdot" id="m-sdot"></div>
          <span class="stxt" id="m-stxt"></span>
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
          <button class="m-btn m-approve" id="m-approve" onclick="modalToggle('approved')">&#10003; Approve</button>
          <button class="m-btn m-reject"  id="m-reject"  onclick="modalToggle('rejected')">&#10007; Reject</button>
        </div>
        <div class="m-counter" id="m-counter"></div>
        <div class="m-hint">&#8592; &#8594; navigate &nbsp;·&nbsp; A approve &nbsp;·&nbsp; R reject &nbsp;·&nbsp; Esc close</div>
      </div>
    </div>
  </div>
</div>

<script>
const RAW = JSONDATA;
let vis = [];   // currently visible (filtered) items
let midx = -1; // modal index into vis

/* ── persistence ── */
const stKey = id => 'img-status-' + id;
const getSt  = id => localStorage.getItem(stKey(id)) || 'pending';
const setSt  = (id, s) => localStorage.setItem(stKey(id), s);

/* Toggle: same button → back to pending */
function toggleSt(id, target) {
  setSt(id, getSt(id) === target ? 'pending' : target);
  render();
  if (midx >= 0) renderModal();
}

/* Card-level toggle — stops click from bubbling to openModal */
function cardToggle(e, btn) {
  e.stopPropagation();
  toggleSt(btn.dataset.id, btn.dataset.tgt);
}

/* ── short model label ── */
function shortM(m) {
  return m.replace('gemini-3.1-flash-image-preview','gemini-flash')
          .replace('gemini-3-pro-image-preview','gemini-pro')
          .replace('gpt-image-2','gpt-img-2')
          .replace('grok-4.2-image','grok-img');
}

/* ── render grid ── */
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
  document.getElementById('stats').textContent = vis.length + ' / ' + RAW.length + ' images';
  document.getElementById('grid').innerHTML = vis.map((item, i) => {
    const s  = getSt(item.id);
    const bc = s === 'approved' ? 'badge-approved' : s === 'rejected' ? 'badge-rejected' : 'badge-pending';
    const cc = s === 'approved' ? 'approved'       : s === 'rejected' ? 'rejected'       : '';
    const aOn = s === 'approved' ? ' ca-on' : '';
    const rOn = s === 'rejected' ? ' ca-on' : '';
    const fn = item.filename.length > 24 ? item.filename.slice(0,21)+'...' : item.filename;
    return '<div class="card '+cc+'" onclick="openModal('+i+')">' +
      '<div class="card-img">' +
        '<img src="'+item.src+'" alt="'+item.filename+'" loading="lazy">' +
        '<span class="badge '+bc+'">'+s+'</span>' +
      '</div>' +
      '<div class="card-foot">' +
        '<span class="card-name" title="'+item.filename+'">'+fn+'</span>' +
        '<span class="card-model" title="'+item.model+'">'+shortM(item.model)+'</span>' +
      '</div>' +
      '<div class="card-actions">' +
        '<button class="ca-btn ca-approve'+aOn+'" data-id="'+item.id+'" data-tgt="approved" onclick="cardToggle(event,this)">&#10003; Approve</button>' +
        '<button class="ca-btn ca-reject' +rOn+'" data-id="'+item.id+'" data-tgt="rejected" onclick="cardToggle(event,this)">&#10007; Reject</button>' +
      '</div></div>';
  }).join('');
}

/* ── modal ── */
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

  const dot  = document.getElementById('m-sdot');
  const stxt = document.getElementById('m-stxt');
  dot.className  = 'sdot sdot-' + s;
  stxt.textContent = s;
  stxt.style.color = s === 'approved' ? 'var(--approve)' : s === 'rejected' ? 'var(--reject)' : 'var(--pending)';

  document.getElementById('m-prompt').textContent = item.prompt;

  document.getElementById('m-meta').innerHTML =
    row('Model',      '<span class="m-tag">'+item.model+'</span>') +
    row('Resolution', item.resolution) +
    row('Size',       item.actual_size) +
    row('File',       item.filename) +
    row('Time',       item.timestamp.slice(0,16).replace('T',' '));

  document.getElementById('m-approve').className = 'm-btn m-approve' + (s === 'approved' ? ' active' : '');
  document.getElementById('m-reject' ).className = 'm-btn m-reject'  + (s === 'rejected' ? ' active' : '');

  document.getElementById('m-counter').textContent = (midx+1) + ' / ' + vis.length;
  document.getElementById('nav-prev').disabled = midx <= 0;
  document.getElementById('nav-next').disabled = midx >= vis.length - 1;
}

function row(k, v) {
  return '<div class="m-row"><span class="m-key">'+k+'</span><span class="m-val">'+v+'</span></div>';
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

/* click dark bg to close */
document.getElementById('m-img-pane').addEventListener('click', e => {
  if (e.target === document.getElementById('m-img-pane')) closeModal();
});

/* keyboard */
document.addEventListener('keydown', e => {
  if (!document.getElementById('modal').classList.contains('open')) return;
  if (e.key === 'Escape')      closeModal();
  if (e.key === 'ArrowLeft')   navModal(-1);
  if (e.key === 'ArrowRight')  navModal(1);
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
