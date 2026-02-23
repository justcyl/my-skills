#!/usr/bin/env python3
"""ASR transcription with SiliconFlow primary + Qwen fallback."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import pathlib
import sys
import tempfile
from typing import Optional

import requests


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def guess_mime(path: pathlib.Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "audio/mpeg"


def download_audio(url: str) -> pathlib.Path:
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    suffix = pathlib.Path(url.split("?")[0]).suffix or ".audio"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(r.content)
    tmp.flush()
    tmp.close()
    return pathlib.Path(tmp.name)


def siliconflow_transcribe(
    audio_path: pathlib.Path,
    api_key: str,
    model: str = "FunAudioLLM/SenseVoiceSmall",
    timeout: int = 300,
) -> str:
    url = "https://api.siliconflow.cn/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    with audio_path.open("rb") as f:
        files = {"file": (audio_path.name, f, guess_mime(audio_path))}
        data = {"model": model}
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=timeout)

    if resp.status_code >= 400:
        raise RuntimeError(f"SiliconFlow HTTP {resp.status_code}: {resp.text[:500]}")

    payload = resp.json()
    text = payload.get("text")
    if not text:
        raise RuntimeError(f"SiliconFlow返回缺少text字段: {json.dumps(payload, ensure_ascii=False)[:500]}")
    return text


def qwen_transcribe(
    audio_input: str,
    api_key: str,
    region: str = "cn",
    model: str = "qwen3-asr-flash",
    language: Optional[str] = None,
    enable_itn: bool = False,
    timeout: int = 300,
) -> str:
    base_url = (
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
        if region == "cn"
        else "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
    endpoint = f"{base_url}/chat/completions"

    if is_url(audio_input):
        data_value = audio_input
    else:
        path = pathlib.Path(audio_input)
        raw = path.read_bytes()
        data_value = f"data:{guess_mime(path)};base64,{base64.b64encode(raw).decode()}"

    asr_options = {"enable_itn": enable_itn}
    if language:
        asr_options["language"] = language

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "input_audio", "input_audio": {"data": data_value}}],
            }
        ],
        "stream": False,
        "extra_body": {"asr_options": asr_options},
    }

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
    if resp.status_code >= 400:
        raise RuntimeError(f"Qwen HTTP {resp.status_code}: {resp.text[:500]}")

    body = resp.json()
    choices = body.get("choices") or []
    if not choices:
        raise RuntimeError(f"Qwen返回缺少choices: {json.dumps(body, ensure_ascii=False)[:500]}")

    msg = choices[0].get("message", {})
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(item.get("text", "") for item in content if isinstance(item, dict))
    raise RuntimeError(f"Qwen返回结构异常: {json.dumps(body, ensure_ascii=False)[:500]}")


def main():
    parser = argparse.ArgumentParser(description="ASR: SiliconFlow primary, Qwen fallback")
    parser.add_argument("audio", help="Local audio path or public URL")
    parser.add_argument("--provider", choices=["auto", "siliconflow", "qwen"], default="auto")

    parser.add_argument("--sf-api-key", default=os.getenv("SILICONFLOW_API_KEY"))
    parser.add_argument("--sf-model", default="FunAudioLLM/SenseVoiceSmall")

    parser.add_argument("--qwen-api-key", default=os.getenv("DASHSCOPE_API_KEY"))
    parser.add_argument("--qwen-model", default="qwen3-asr-flash")
    parser.add_argument("--qwen-region", choices=["cn", "intl"], default="cn")
    parser.add_argument("--language", default=None)
    parser.add_argument("--enable-itn", action="store_true")

    args = parser.parse_args()

    cleanup_path = None
    local_audio_path = None

    try:
        if is_url(args.audio):
            # SiliconFlow needs file upload; download once and reuse.
            cleanup_path = download_audio(args.audio)
            local_audio_path = cleanup_path
        else:
            local_audio_path = pathlib.Path(args.audio)
            if not local_audio_path.exists():
                raise FileNotFoundError(f"音频文件不存在: {local_audio_path}")

        if args.provider == "siliconflow":
            if not args.sf_api_key:
                raise RuntimeError("缺少 SILICONFLOW_API_KEY（或 --sf-api-key）")
            text = siliconflow_transcribe(local_audio_path, api_key=args.sf_api_key, model=args.sf_model)
            print(text)
            return

        if args.provider == "qwen":
            if not args.qwen_api_key:
                raise RuntimeError("缺少 DASHSCOPE_API_KEY（或 --qwen-api-key）")
            qwen_input = args.audio if is_url(args.audio) else str(local_audio_path)
            text = qwen_transcribe(
                qwen_input,
                api_key=args.qwen_api_key,
                region=args.qwen_region,
                model=args.qwen_model,
                language=args.language,
                enable_itn=args.enable_itn,
            )
            print(text)
            return

        # auto mode
        sf_err = None
        if args.sf_api_key:
            try:
                text = siliconflow_transcribe(local_audio_path, api_key=args.sf_api_key, model=args.sf_model)
                print(text)
                return
            except Exception as err:  # noqa: BLE001
                sf_err = err
                eprint(f"[WARN] SiliconFlow失败，准备fallback到Qwen: {err}")
        else:
            eprint("[WARN] 未配置SILICONFLOW_API_KEY，跳过SiliconFlow")

        if not args.qwen_api_key:
            raise RuntimeError(f"SiliconFlow不可用，且缺少Qwen密钥。SiliconFlow错误: {sf_err}")

        qwen_input = args.audio if is_url(args.audio) else str(local_audio_path)
        text = qwen_transcribe(
            qwen_input,
            api_key=args.qwen_api_key,
            region=args.qwen_region,
            model=args.qwen_model,
            language=args.language,
            enable_itn=args.enable_itn,
        )
        print(text)

    finally:
        if cleanup_path and cleanup_path.exists():
            cleanup_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
