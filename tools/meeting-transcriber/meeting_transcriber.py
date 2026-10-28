"""Meeting transcriber MCP server.

Transcribes local audio or video files with faster-whisper and returns the
text to Claude. Claude then writes the summary, decisions, and action items.
Transcripts are saved beside the recording as .transcript.txt and .vtt.

Environment variables (optional):
  TRANSCRIBER_MODEL    default model name (default: small.en)
  TRANSCRIBER_DEVICE   cpu or cuda (default: cpu)
  TRANSCRIBER_COMPUTE  compute type (default: int8 on cpu, float16 on cuda)
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel
from mcp.server.fastmcp import Context, FastMCP

# stdout carries the MCP protocol, so all logging goes to stderr.
logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("meeting-transcriber")

DEFAULT_MODEL = os.environ.get("TRANSCRIBER_MODEL", "small.en")
DEVICE = os.environ.get("TRANSCRIBER_DEVICE", "cpu")
COMPUTE = os.environ.get("TRANSCRIBER_COMPUTE",
                         "float16" if DEVICE == "cuda" else "int8")
MODELS = ("tiny.en", "base.en", "small.en", "medium.en",
          "tiny", "base", "small", "medium", "large-v3", "turbo")
MEDIA = {".mp3", ".mp4", ".m4a", ".wav", ".webm", ".mkv", ".mov",
         ".ogg", ".flac", ".aac", ".wma", ".avi"}

mcp = FastMCP("meeting-transcriber")
_loaded: dict[str, WhisperModel] = {}


def _model(name: str) -> WhisperModel:
    if name not in _loaded:
        log.info("loading model %s on %s (%s)", name, DEVICE, COMPUTE)
        _loaded[name] = WhisperModel(name, device=DEVICE, compute_type=COMPUTE)
    return _loaded[name]


def _ts(seconds: float, sep: str = ".") -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


@mcp.tool()
async def transcribe(path: str, model: str = DEFAULT_MODEL,
                     language: str | None = None,
                     ctx: Context | None = None) -> str:
    """Transcribe a local audio or video file.

    Args:
        path: Full path to the recording, e.g. C:\\Recordings\\standup.mp4.
        model: small.en (fast), medium.en (better names and technical terms),
            or large-v3 (non-English audio).
        language: Optional language code such as "es". Leave empty to detect.
            English-only models (.en) always use English.

    Returns the timestamped transcript and the paths of the saved files.
    After this returns, write the summary, decisions, and action items.
    """
    src = Path(path).expanduser()
    if not src.is_file():
        return f"Error: file not found: {src}"
    if src.suffix.lower() not in MEDIA:
        return f"Error: unsupported file type {src.suffix}. Supported: {', '.join(sorted(MEDIA))}"
    if model not in MODELS:
        return f"Error: unknown model {model}. Choose one of: {', '.join(MODELS)}"
    if model.endswith(".en"):
        language = "en"

    start = time.time()
    # Run the CPU-bound work in a thread so progress updates keep flowing
    # and the client does not time out on long recordings.
    segments, info = await asyncio.to_thread(
        lambda: _model(model).transcribe(
            str(src), language=language, vad_filter=True, beam_size=5))

    lines, vtt = [], ["WEBVTT", ""]
    it = iter(segments)
    while (seg := await asyncio.to_thread(next, it, None)) is not None:
        if ctx is not None:
            await ctx.report_progress(seg.end, info.duration)
        text = seg.text.strip()
        if not text:
            continue
        lines.append(f"[{_ts(seg.start)[:8]}] {text}")
        vtt += [f"{_ts(seg.start)} --> {_ts(seg.end)}", text, ""]

    txt_path = src.with_suffix(".transcript.txt")
    vtt_path = src.with_suffix(".vtt")
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    vtt_path.write_text("\n".join(vtt), encoding="utf-8")

    elapsed = time.time() - start
    log.info("transcribed %s (%.0fs audio) in %.0fs", src.name, info.duration, elapsed)
    header = (f"File: {src}\nModel: {model}\nLanguage: {info.language}\n"
              f"Audio length: {_ts(info.duration)[:8]}\n"
              f"Saved: {txt_path}\nSaved: {vtt_path}\n")
    if not lines:
        return header + "\nNo speech detected."
    return header + "\nTranscript:\n" + "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
