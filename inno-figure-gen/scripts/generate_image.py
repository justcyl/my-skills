#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pillow>=10.0.0",
# ]
# ///
"""
Generate or edit images with Gemini-compatible providers.

Usage:
    uv run generate_image.py --prompt "your image description" --filename "output.png" [--resolution 1K|2K|4K] [--model MODEL] [--api-key KEY] [--base-url URL] [--provider auto|gemini-native|openai-chat-compat]
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path


CONFIG_PATH = Path.home() / ".config" / "inno-figure-gen" / "config.env"


def load_config() -> dict[str, str]:
    """Load key=value pairs from ~/.config/inno-figure-gen/config.env."""
    cfg: dict[str, str] = {}
    if not CONFIG_PATH.is_file():
        return cfg
    for line in CONFIG_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


class RetryableRequestError(RuntimeError):
    """Transient upstream error that can be retried."""


class NoImageReturnedError(RuntimeError):
    """Provider returned a response without image payload."""


def is_retryable_text(text: str) -> bool:
    """Best-effort check for transient upstream failures."""
    lowered = text.lower()
    markers = (
        "system_cpu_overloaded",
        "error code: 524",
        "timeout",
        "temporarily unavailable",
        "rate limit",
        "gateway timeout",
        "upstream",
    )
    return any(marker in lowered for marker in markers)


def get_api_key(provided_key: str | None, cfg: dict[str, str] | None = None) -> str | None:
    """Get API key: CLI arg > config.env > GEMINI_API_KEY env var."""
    if provided_key:
        return provided_key
    if cfg and cfg.get("INNO_FIGURE_GEN_API_KEY"):
        return cfg["INNO_FIGURE_GEN_API_KEY"]
    return os.environ.get("GEMINI_API_KEY")


def retry_call(fn, *, label: str, max_retries: int, retry_backoff_ms: int):
    """Run an operation with exponential backoff for transient errors."""
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except RetryableRequestError:
            if attempt >= max_retries:
                raise
            wait_seconds = (retry_backoff_ms * (2 ** (attempt - 1))) / 1000
            print(
                f"Retrying {label} ({attempt}/{max_retries}) after transient error...",
                file=sys.stderr,
            )
            time.sleep(wait_seconds)


def get_gemini_parts(response) -> list:
    """Extract all response parts from Gemini SDK response object."""
    if getattr(response, "parts", None):
        return response.parts

    parts = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        candidate_parts = getattr(content, "parts", None)
        if candidate_parts:
            parts.extend(candidate_parts)
    return parts


def extract_image_from_gemini_response(response) -> tuple[bytes, str]:
    """Return image bytes and mime type from Gemini SDK response."""
    parts = get_gemini_parts(response)
    text_preview = []

    for part in parts:
        text_value = getattr(part, "text", None)
        if text_value:
            text_preview.append(text_value)

        inline_data = getattr(part, "inline_data", None)
        if inline_data is None:
            continue

        image_data = getattr(inline_data, "data", None)
        if image_data is None:
            continue

        if isinstance(image_data, str):
            image_data = base64.b64decode(image_data)

        mime_type = getattr(inline_data, "mime_type", None) or "image/png"
        return image_data, mime_type

    preview = " ".join(text_preview).strip()
    if preview:
        raise NoImageReturnedError(f"No image in response. Preview: {preview[:200]}")
    raise NoImageReturnedError("No image in response.")


def parse_data_url(text: str) -> tuple[bytes, str] | None:
    """Parse image data URL and return decoded bytes."""
    match = re.search(
        r"data:(image/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=\s]+)",
        text,
        re.DOTALL,
    )
    if not match:
        return None

    mime_type = match.group(1)
    encoded = re.sub(r"\s+", "", match.group(2))
    try:
        decoded = base64.b64decode(encoded)
    except Exception as exc:
        raise NoImageReturnedError(f"Invalid base64 image payload: {exc}") from exc
    return decoded, mime_type


def extract_image_from_openai_content(content) -> tuple[bytes, str]:
    """Extract image bytes from OpenAI-compatible chat content."""
    if isinstance(content, str):
        parsed = parse_data_url(content)
        if parsed:
            return parsed
        raise NoImageReturnedError(f"No image payload in content: {content[:200]}")

    if isinstance(content, list):
        text_fragments = []
        for item in content:
            if not isinstance(item, dict):
                continue

            image_url = item.get("image_url")
            if isinstance(image_url, dict) and isinstance(image_url.get("url"), str):
                parsed = parse_data_url(image_url["url"])
                if parsed:
                    return parsed

            if isinstance(item.get("text"), str):
                text_fragments.append(item["text"])

        preview = " ".join(text_fragments).strip()
        if preview:
            raise NoImageReturnedError(f"No image payload in content: {preview[:200]}")
        raise NoImageReturnedError("No image payload in content list.")

    raise NoImageReturnedError("Unsupported content format from chat response.")


def post_openai_chat_json(
    *,
    url: str,
    api_key: str,
    payload: dict,
    timeout_ms: int,
) -> dict:
    """POST JSON to OpenAI-compatible endpoint and return parsed body."""
    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "curl/8.7.1",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_ms / 1000) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except urllib.error.URLError as exc:
        message = str(exc)
        if is_retryable_text(message):
            raise RetryableRequestError(message) from exc
        raise RuntimeError(f"Network error: {message}") from exc

    parsed_json = None
    try:
        parsed_json = json.loads(body)
    except json.JSONDecodeError:
        if is_retryable_text(body):
            raise RetryableRequestError(body)
        raise RuntimeError(f"Non-JSON response (HTTP {status}): {body[:200]}")

    if isinstance(parsed_json, dict) and isinstance(parsed_json.get("error"), dict):
        error = parsed_json["error"]
        code = str(error.get("code", ""))
        message = str(error.get("message", ""))
        combined = f"{code} {message}".strip()
        if is_retryable_text(combined):
            raise RetryableRequestError(combined)
        raise RuntimeError(f"API error: {combined}")

    if status >= 500:
        if is_retryable_text(body):
            raise RetryableRequestError(f"HTTP {status}")
        raise RuntimeError(f"Server error (HTTP {status}): {body[:200]}")

    if status >= 400:
        raise RuntimeError(f"Request failed (HTTP {status}): {body[:200]}")

    if not isinstance(parsed_json, dict):
        raise RuntimeError("Unexpected response type from chat endpoint.")
    return parsed_json


def file_to_data_url(file_path: str) -> str:
    """Encode local file as data URL for OpenAI-compatible multimodal input."""
    path = Path(file_path)
    raw = path.read_bytes()
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        mime_type = "image/png"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def generate_with_gemini_native(
    *,
    prompt: str,
    model: str,
    output_resolution: str,
    input_image,
    api_key: str,
    base_url: str | None,
    timeout_ms: int,
    max_retries: int,
    retry_backoff_ms: int,
) -> tuple[bytes, str]:
    """Generate image with Gemini SDK native API."""
    from google import genai
    from google.genai import types

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["http_options"] = types.HttpOptions(
            base_url=base_url,
            timeout=timeout_ms,
        )
    client = genai.Client(**client_kwargs)

    if input_image is not None:
        contents = [input_image, prompt]
    else:
        contents = prompt

    def _request():
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=types.ImageConfig(image_size=output_resolution),
                ),
            )
        except Exception as exc:
            message = str(exc)
            if is_retryable_text(message):
                raise RetryableRequestError(message) from exc
            raise

    response = retry_call(
        _request,
        label="gemini-native",
        max_retries=max_retries,
        retry_backoff_ms=retry_backoff_ms,
    )
    return extract_image_from_gemini_response(response)


def generate_with_openai_chat_compat(
    *,
    prompt: str,
    model: str,
    output_resolution: str,
    input_image_path: str | None,
    api_key: str,
    base_url: str,
    timeout_ms: int,
    max_retries: int,
    retry_backoff_ms: int,
) -> tuple[bytes, str]:
    """Generate image with OpenAI-compatible /v1/chat/completions endpoint."""
    endpoint = base_url.rstrip("/") + "/v1/chat/completions"
    prompt_suffix = (
        "\n\nReturn only one image and no text explanation. "
        f"Preferred resolution: {output_resolution}."
    )

    if input_image_path:
        data_url = file_to_data_url(input_image_path)
        user_content = [
            {"type": "text", "text": prompt + prompt_suffix},
            {"type": "image_url", "image_url": {"url": data_url}},
        ]
    else:
        user_content = prompt + prompt_suffix

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_content}],
        "temperature": 0,
    }

    response_json = retry_call(
        lambda: post_openai_chat_json(
            url=endpoint,
            api_key=api_key,
            payload=payload,
            timeout_ms=timeout_ms,
        ),
        label="openai-chat-compat",
        max_retries=max_retries,
        retry_backoff_ms=retry_backoff_ms,
    )

    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise NoImageReturnedError("No choices in chat response.")

    first_choice = choices[0]
    message = first_choice.get("message", {})
    content = message.get("content")
    return extract_image_from_openai_content(content)


def save_png(image_data: bytes, output_path: Path) -> None:
    """Save decoded image bytes as PNG file."""
    from PIL import Image as PILImage

    output_path.parent.mkdir(parents=True, exist_ok=True)

    image = PILImage.open(BytesIO(image_data))
    if image.mode == "RGBA":
        rgb_image = PILImage.new("RGB", image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[3])
        rgb_image.save(str(output_path), "PNG")
    elif image.mode == "RGB":
        image.save(str(output_path), "PNG")
    else:
        image.convert("RGB").save(str(output_path), "PNG")


def resolve_provider_order(provider: str, base_url: str | None) -> list[str]:
    """Resolve runtime provider order."""
    if provider == "auto":
        if base_url:
            return ["gemini-native", "openai-chat-compat"]
        return ["gemini-native"]
    return [provider]


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Gemini native API or OpenAI-compatible chat API"
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Image description/prompt"
    )
    parser.add_argument(
        "--filename", "-f",
        required=True,
        help="Output filename (e.g., sunset-mountains.png)"
    )
    parser.add_argument(
        "--input-image", "-i",
        help="Optional input image path for editing/modification"
    )
    parser.add_argument(
        "--resolution", "-r",
        choices=["1K", "2K", "4K"],
        default="1K",
        help="Output resolution: 1K (default), 2K, or 4K"
    )
    parser.add_argument(
        "--api-key", "-k",
        help="Gemini API key (overrides GEMINI_API_KEY env var)"
    )
    parser.add_argument(
        "--model", "-m",
        default="gemini-3.1-flash-image-preview",
        help="Model to use for image generation (default: gemini-3.1-flash-image-preview)"
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "gemini-native", "openai-chat-compat"],
        default="auto",
        help="Provider mode: auto (default), gemini-native, openai-chat-compat"
    )
    parser.add_argument(
        "--base-url",
        help="Optional base URL for API gateway, e.g. https://api.ikuncode.cc"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Max retry attempts for transient upstream errors (default: 3)"
    )
    parser.add_argument(
        "--retry-backoff-ms",
        type=int,
        default=1200,
        help="Initial retry backoff in milliseconds (default: 1200)"
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=60000,
        help="Request timeout in milliseconds (default: 60000)"
    )

    args = parser.parse_args()

    # Load config file
    cfg = load_config()

    # Apply config defaults (CLI args take priority)
    if not args.api_key and cfg.get("INNO_FIGURE_GEN_API_KEY"):
        pass  # handled in get_api_key
    if not args.base_url and cfg.get("INNO_FIGURE_GEN_BASE_URL"):
        args.base_url = cfg["INNO_FIGURE_GEN_BASE_URL"]
    if args.model == "gemini-3.1-flash-image-preview" and cfg.get("INNO_FIGURE_GEN_DEFAULT_MODEL"):
        args.model = cfg["INNO_FIGURE_GEN_DEFAULT_MODEL"]

    # Get API key
    api_key = get_api_key(args.api_key, cfg)
    if not api_key:
        print("Error: No API key provided.", file=sys.stderr)
        print("Please either:", file=sys.stderr)
        print("  1. Provide --api-key argument", file=sys.stderr)
        print("  2. Set GEMINI_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    # Import here after checking API key to avoid slow import on error
    from PIL import Image as PILImage

    # Set up output path
    output_path = Path(args.filename)

    # Load input image if provided
    input_image = None
    output_resolution = args.resolution
    if args.input_image:
        try:
            input_image = PILImage.open(args.input_image)
            print(f"Loaded input image: {args.input_image}")

            # Auto-detect resolution if not explicitly set by user
            if args.resolution == "1K":  # Default value
                # Map input image size to resolution
                width, height = input_image.size
                max_dim = max(width, height)
                if max_dim >= 3000:
                    output_resolution = "4K"
                elif max_dim >= 1500:
                    output_resolution = "2K"
                else:
                    output_resolution = "1K"
                print(f"Auto-detected resolution: {output_resolution} (from input {width}x{height})")
        except Exception as e:
            print(f"Error loading input image: {e}", file=sys.stderr)
            sys.exit(1)

    provider_order = resolve_provider_order(args.provider, args.base_url)

    if input_image:
        print(f"Editing image with resolution {output_resolution}...")
    else:
        print(f"Generating image with resolution {output_resolution}...")

    errors = []
    for provider in provider_order:
        try:
            if provider == "gemini-native":
                image_data, mime_type = generate_with_gemini_native(
                    prompt=args.prompt,
                    model=args.model,
                    output_resolution=output_resolution,
                    input_image=input_image,
                    api_key=api_key,
                    base_url=args.base_url,
                    timeout_ms=args.timeout_ms,
                    max_retries=args.max_retries,
                    retry_backoff_ms=args.retry_backoff_ms,
                )
            else:
                if not args.base_url:
                    raise RuntimeError("--base-url is required for openai-chat-compat")
                image_data, mime_type = generate_with_openai_chat_compat(
                    prompt=args.prompt,
                    model=args.model,
                    output_resolution=output_resolution,
                    input_image_path=args.input_image,
                    api_key=api_key,
                    base_url=args.base_url,
                    timeout_ms=args.timeout_ms,
                    max_retries=args.max_retries,
                    retry_backoff_ms=args.retry_backoff_ms,
                )

            save_png(image_data, output_path)
            full_path = output_path.resolve()
            print(f"Provider used: {provider}")
            print(f"Image mime type: {mime_type}")
            print(f"\nImage saved: {full_path}")
            return
        except Exception as e:
            error_text = str(e)
            errors.append(f"{provider}: {error_text}")
            print(f"Provider {provider} failed: {error_text}", file=sys.stderr)
            if args.provider != "auto":
                break

    print("Error: failed to generate image.", file=sys.stderr)
    for item in errors:
        print(f"  - {item}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
