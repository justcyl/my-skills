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
<title>Image Gallery</title>
<style>
  :root {{
    --bg: #0f0f13; --card: #1a1a24; --border: #2e2e42;
    --text: #e0e0f0; --sub: #8080a0; --accent: #7c6af7;
    --approve: #22c55e; --reject: #ef4444; --pending: #f59e0b;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; padding: 24px; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 20px; color: var(--accent); letter-spacing: .03em; }}
  .toolbar {{ display: flex; gap: 12px; align-items: center; margin-bottom: 20px; flex-wrap: wrap; }}
  .toolbar select, .toolbar input {{
    background: var(--card); border: 1px solid var(--border); color: var(--text);
    padding: 6px 12px; border-radius: 6px; font-size: .875rem;
  }}
  .stats {{ margin-left: auto; font-size: .8rem; color: var(--sub); }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }}
  .card {{
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    overflow: hidden; transition: transform .15s, box-shadow .15s;
    display: flex; flex-direction: column;
  }}
  .card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.4); }}
  .card.approved {{ border-color: var(--approve); }}
  .card.rejected {{ border-color: var(--reject); opacity: .55; }}
  .img-wrap {{
    position: relative; cursor: zoom-in; background: #111;
    aspect-ratio: 1 / 1; overflow: hidden;
  }}
  .img-wrap img {{ width: 100%; height: 100%; object-fit: contain; display: block; }}
  .status-badge {{
    position: absolute; top: 8px; right: 8px;
    font-size: .7rem; font-weight: 700; padding: 3px 8px; border-radius: 20px;
    text-transform: uppercase; letter-spacing: .05em;
  }}
  .badge-approved {{ background: var(--approve); color: #000; }}
  .badge-rejected {{ background: var(--reject); color: #fff; }}
  .badge-pending {{ background: var(--pending); color: #000; }}
  .info {{ padding: 12px 14px; flex: 1; display: flex; flex-direction: column; gap: 6px; }}
  .prompt {{ font-size: .85rem; line-height: 1.45; color: var(--text); }}
  .prompt.clamped {{ display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
  .meta {{ font-size: .75rem; color: var(--sub); display: flex; flex-wrap: wrap; gap: 6px; }}
  .tag {{
    background: rgba(124,106,247,.15); border: 1px solid rgba(124,106,247,.3);
    padding: 2px 7px; border-radius: 10px; font-size: .7rem;
  }}
  .actions {{ padding: 10px 14px; display: flex; gap: 8px; border-top: 1px solid var(--border); }}
  .btn {{
    flex: 1; padding: 7px 0; border-radius: 7px; border: none; cursor: pointer;
    font-size: .8rem; font-weight: 600; transition: opacity .15s;
  }}
  .btn:hover {{ opacity: .85; }}
  .btn-approve {{ background: var(--approve); color: #000; }}
  .btn-reject {{ background: #2a1515; color: var(--reject); border: 1px solid var(--reject); }}
  .btn-expand {{ background: var(--border); color: var(--text); font-size: .72rem; }}
  /* Lightbox */
  #lb {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.9);
    z-index:9999; align-items:center; justify-content:center; }}
  #lb.open {{ display:flex; }}
  #lb img {{ max-width:90vw; max-height:90vh; border-radius:8px; }}
  #lb-close {{
    position:absolute; top:16px; right:24px; font-size:2rem; cursor:pointer;
    color:#fff; background:none; border:none;
  }}
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
  <input type="text" id="search" placeholder="Search prompt…" oninput="render()" style="min-width:180px">
  <span class="stats" id="stats"></span>
</div>
<div class="grid" id="grid"></div>
<div id="lb"><button id="lb-close" onclick="closeLb()">✕</button><img id="lb-img" src="" alt=""></div>

<script>
const RAW = JSONDATA;

function getStatus(id) {{
  return localStorage.getItem('img-status-' + id) || 'pending';
}}
function setStatus(id, s) {{
  localStorage.setItem('img-status-' + id, s);
  render();
}}

function render() {{
  const filterModel  = document.getElementById('filterModel').value;
  const filterStatus = document.getElementById('filterStatus').value;
  const search       = document.getElementById('search').value.toLowerCase();
  const grid = document.getElementById('grid');
  const items = RAW.filter(item => {{
    if (filterModel && item.model !== filterModel) return false;
    const st = getStatus(item.id);
    if (filterStatus && st !== filterStatus) return false;
    if (search && !item.prompt.toLowerCase().includes(search)) return false;
    return true;
  }});
  document.getElementById('stats').textContent =
    `${{items.length}} / ${{RAW.length}} images`;
  grid.innerHTML = items.map(item => {{
    const st = getStatus(item.id);
    const badgeCls = st === 'approved' ? 'badge-approved' : st === 'rejected' ? 'badge-rejected' : 'badge-pending';
    const cardCls  = st === 'approved' ? 'approved' : st === 'rejected' ? 'rejected' : '';
    return `
<div class="card ${{cardCls}}" id="card-${{item.id}}">
  <div class="img-wrap" onclick="openLb('${{item.src}}')">
    <img src="${{item.src}}" alt="${{item.filename}}" loading="lazy">
    <span class="status-badge ${{badgeCls}}">${{st}}</span>
  </div>
  <div class="info">
    <div class="prompt clamped" id="p-${{item.id}}">${{item.prompt}}</div>
    <div class="meta">
      <span class="tag">${{item.model}}</span>
      <span class="tag">${{item.resolution}}</span>
      <span class="tag">${{item.actual_size}}</span>
      <span title="${{item.timestamp}}">${{item.timestamp.slice(0,16).replace('T',' ')}}</span>
    </div>
    <div class="meta" style="margin-top:2px;color:#606080;font-size:.7rem">${{item.filename}}</div>
  </div>
  <div class="actions">
    <button class="btn btn-approve" onclick="setStatus('${{item.id}}','approved')">✓ Approve</button>
    <button class="btn btn-reject"  onclick="setStatus('${{item.id}}','rejected')">✗ Reject</button>
    <button class="btn btn-expand"  onclick="toggleExpand('${{item.id}}')">···</button>
  </div>
</div>`;
  }}).join('');
}}

function toggleExpand(id) {{
  const el = document.getElementById('p-' + id);
  el.classList.toggle('clamped');
}}

function openLb(src) {{
  document.getElementById('lb-img').src = src;
  document.getElementById('lb').classList.add('open');
}}
function closeLb() {{
  document.getElementById('lb').classList.remove('open');
}}
document.getElementById('lb').addEventListener('click', e => {{
  if (e.target === document.getElementById('lb')) closeLb();
}});

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


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate images via local proxy (gemini / gpt-image-2 / grok)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--prompt", "-p", help="Image description / editing instructions")
    parser.add_argument("--filename", "-f", help="Output PNG filename")
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
    parser.add_argument(
        "--gallery", "-g",
        metavar="GALLERY.HTML",
        help=(
            "Path to gallery HTML file.\n"
            "  If generating an image: add it to the gallery after saving.\n"
            "  If used alone (no --prompt/--filename): rebuild HTML from metadata."
        ),
    )
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--retry-backoff-ms", type=int, default=1200)
    parser.add_argument("--timeout-ms", type=int, default=120000)
    args = parser.parse_args()

    # Gallery-only mode
    if args.gallery and not args.prompt and not args.filename:
        rebuild_gallery(Path(args.gallery))
        return

    if not args.prompt:
        parser.error("--prompt is required for image generation")
    if not args.filename:
        parser.error("--filename is required for image generation")

    # Resolve size string
    size_str = _RESOLUTION_TO_SIZE.get(args.resolution, "1024x1024")
    # gpt-image-2 4K is not supported → downgrade to 2K
    if args.model == "gpt-image-2" and args.resolution == "4K":
        print("  gpt-image-2 does not support 4K; using 2K instead.", file=sys.stderr)
        size_str = "2048x2048"

    output_path = Path(args.filename)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    print(f"Model:      {args.model}")
    print(f"Resolution: {args.resolution} ({size_str})")
    if args.input_image:
        print(f"Input img:  {args.input_image}")
    print(f"Output:     {output_path}")
    print()

    common_kwargs = dict(
        prompt=args.prompt,
        model=args.model,
        size_str=size_str,
        input_image_path=args.input_image,
        max_retries=args.max_retries,
        backoff_ms=args.retry_backoff_ms,
        timeout_ms=args.timeout_ms,
    )

    if args.model in _IMAGES_GENERATIONS_MODELS:
        image_data, mime_type = _generate_images_generations(**common_kwargs)
    else:
        image_data, mime_type = _generate_chat_completions(**common_kwargs)

    w, h = _save_png(image_data, output_path)
    full_path = output_path.resolve()
    print(f"Saved: {full_path}  ({w}×{h}px, {len(image_data)//1024}KB)")

    if args.gallery:
        add_to_gallery(
            Path(args.gallery),
            image_path=output_path,
            model=args.model,
            prompt=args.prompt,
            resolution=args.resolution,
            actual_size=(w, h),
            timestamp=timestamp,
        )


if __name__ == "__main__":
    main()
