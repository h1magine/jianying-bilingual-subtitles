#!/usr/bin/env python3
"""Reusable transcription, bilingual SRT, and JianYing draft pipeline."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_PROMPT = (
    "Transcribe natural spoken English accurately. Preserve names, quantities, proper nouns, "
    "technical terms, and sentence meaning. Avoid inventing speech during music or silence."
)


def add_dependency_paths(explicit: str | None) -> None:
    candidates = [
        explicit,
        os.getenv("BILINGUAL_SUB_DEPS", "").strip(),
        str(Path.cwd() / ".subtitle-deps"),
        str(Path.cwd() / ".deps"),
    ]
    for value in candidates:
        if not value:
            continue
        path = Path(value).expanduser().resolve()
        if path.is_dir() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def srt_time(seconds: float) -> str:
    total_ms = max(0, int(round(float(seconds) * 1000)))
    hours, remain = divmod(total_ms, 3_600_000)
    minutes, remain = divmod(remain, 60_000)
    secs, millis = divmod(remain, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def load_curated(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    captions = data.get("captions") if isinstance(data, dict) else data
    if not isinstance(captions, list):
        raise ValueError("curated JSON must be a list or contain a 'captions' list")
    return data if isinstance(data, dict) else {}, captions


def validate_captions(captions: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    previous_end = 0.0
    for index, item in enumerate(captions, 1):
        if not isinstance(item, dict):
            errors.append(f"caption {index}: expected an object")
            continue
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"caption {index}: invalid start/end")
            continue
        if start < 0 or end <= start:
            errors.append(f"caption {index}: invalid range {start}..{end}")
        if start < previous_end - 0.001:
            errors.append(f"caption {index}: overlaps the previous cue")
        if not str(item.get("en", "")).strip():
            errors.append(f"caption {index}: missing corrected English")
        if not str(item.get("zh", "")).strip():
            errors.append(f"caption {index}: missing Simplified Chinese")
        previous_end = max(previous_end, end)
    if not captions:
        errors.append("no captions found")
    return errors


def write_srt(path: Path, captions: list[dict[str, Any]], bilingual: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks: list[str] = []
    for index, item in enumerate(captions, 1):
        content = str(item["en"]).strip()
        if bilingual:
            content += "\n" + str(item["zh"]).strip()
        blocks.append(
            f"{index}\n{srt_time(item['start'])} --> {srt_time(item['end'])}\n{content}"
        )
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8-sig")


def cmd_transcribe(args: argparse.Namespace) -> None:
    add_dependency_paths(args.deps_dir)
    video = Path(args.video).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Missing faster-whisper. Install it into a workspace-local directory and pass --deps-dir."
        ) from exc

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    segments, info = model.transcribe(
        str(video),
        language=args.language,
        beam_size=args.beam_size,
        best_of=args.best_of,
        vad_filter=True,
        word_timestamps=True,
        initial_prompt=args.prompt or DEFAULT_PROMPT,
        condition_on_previous_text=True,
    )
    captions: list[dict[str, Any]] = []
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        item = {
            "start": round(float(segment.start), 3),
            "end": round(float(segment.end), 3),
            "en": text,
            "avg_logprob": round(float(segment.avg_logprob), 4),
            "no_speech_prob": round(float(segment.no_speech_prob), 4),
        }
        captions.append(item)
        print(f"[{item['start']:8.2f} - {item['end']:8.2f}] {text}", flush=True)

    raw_json = output_dir / "raw_transcript.json"
    raw_srt = output_dir / "raw_english.srt"
    raw_json.write_text(
        json.dumps(
            {
                "source": video.name,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "captions": captions,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    write_srt(raw_srt, captions, bilingual=False)
    emit({"ok": True, "captions": len(captions), "raw_json": str(raw_json), "raw_srt": str(raw_srt)})


def cmd_validate(args: argparse.Namespace) -> None:
    path = Path(args.curated_json).expanduser().resolve()
    _, captions = load_curated(path)
    errors = validate_captions(captions)
    emit({"ok": not errors, "captions": len(captions), "errors": errors})
    if errors:
        raise SystemExit(2)


def cmd_srt(args: argparse.Namespace) -> None:
    curated = Path(args.curated_json).expanduser().resolve()
    output = Path(args.output_srt).expanduser().resolve()
    _, captions = load_curated(curated)
    errors = validate_captions(captions)
    if errors:
        raise ValueError("; ".join(errors))
    write_srt(output, captions, bilingual=True)
    emit({"ok": True, "captions": len(captions), "output_srt": str(output)})


def discover_jianying_root(explicit: str | None) -> Path:
    user_profile = os.getenv("USERPROFILE", "")
    candidates = [
        explicit,
        os.getenv("JY_SKILL_ROOT", "").strip(),
        str(Path(user_profile) / ".codex" / "skills" / "jianying-editor") if user_profile else "",
        str(Path.cwd() / ".agent" / "skills" / "jianying-editor"),
        str(Path.cwd() / "skills" / "jianying-editor"),
    ]
    for value in candidates:
        if not value:
            continue
        root = Path(value).expanduser().resolve()
        if (root / "scripts" / "jy_wrapper.py").is_file():
            return root
    raise FileNotFoundError("Could not find the installed jianying-editor skill")


def probe_video(video: Path) -> tuple[int, int, float]:
    try:
        import av
    except ImportError:
        return 1920, 1080, 0.0
    container = av.open(str(video))
    try:
        stream = next((stream for stream in container.streams if stream.type == "video"), None)
        width = int(getattr(stream.codec_context, "width", 0) or 1920) if stream else 1920
        height = int(getattr(stream.codec_context, "height", 0) or 1080) if stream else 1080
        duration = float(container.duration / 1_000_000) if container.duration else 0.0
        return width, height, duration
    finally:
        container.close()


def configure_ffmpeg(tool_dir: Path) -> None:
    if shutil.which("ffmpeg"):
        return
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "FFmpeg is unavailable. Install imageio-ffmpeg into the workspace dependency directory."
        ) from exc
    source = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
    bin_dir = tool_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target = bin_dir / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if not target.exists() or target.stat().st_size != source.stat().st_size:
        shutil.copy2(source, target)
    os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def default_draft_root() -> Path:
    local = os.getenv("LOCALAPPDATA", "")
    if os.name == "nt" and local:
        return Path(local) / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft"
    return Path.home() / "Movies" / "JianyingPro Drafts"


def inspect_draft(draft_path: Path, expected_captions: int) -> dict[str, Any]:
    content = draft_path / "draft_info.json"
    if not content.is_file():
        content = draft_path / "draft_content.json"
    data = json.loads(content.read_text(encoding="utf-8-sig"))
    tracks = data.get("tracks", [])
    video_segments = sum(len(track.get("segments", [])) for track in tracks if track.get("type") == "video")
    text_segments = sum(len(track.get("segments", [])) for track in tracks if track.get("type") == "text")
    result = {
        "draft_path": str(draft_path),
        "video_segments": video_segments,
        "text_segments": text_segments,
        "expected_text_segments": expected_captions,
        "duration_us": data.get("duration"),
        "width": data.get("canvas_config", {}).get("width"),
        "height": data.get("canvas_config", {}).get("height"),
    }
    if video_segments < 1 or text_segments != expected_captions:
        raise RuntimeError(f"JianYing acceptance check failed: {result}")
    return result


def cmd_build(args: argparse.Namespace) -> None:
    add_dependency_paths(args.deps_dir)
    video = Path(args.video).expanduser().resolve()
    curated = Path(args.curated_json).expanduser().resolve()
    output_srt = Path(args.output_srt).expanduser().resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    _, captions = load_curated(curated)
    errors = validate_captions(captions)
    if errors:
        raise ValueError("; ".join(errors))
    write_srt(output_srt, captions, bilingual=True)

    width, height, source_duration = probe_video(video)
    configure_ffmpeg(output_srt.parent / ".jianying-subtitle-tools")
    skill_root = discover_jianying_root(args.jianying_skill_root)
    scripts_path = skill_root / "scripts"
    sys.path.insert(0, str(scripts_path))
    from jy_wrapper import JyProject
    import pyJianYingDraft as draft

    draft_root = Path(args.draft_root).expanduser().resolve() if args.draft_root else default_draft_root()
    target = draft_root / args.project_name
    if target.exists():
        raise FileExistsError(
            f"Refusing to modify existing JianYing draft: {target}. Choose a new --project-name."
        )

    project = JyProject(
        args.project_name,
        width=width,
        height=height,
        drafts_root=str(draft_root),
        overwrite=False,
    )
    segment = project.add_media_safe(str(video), start_time="0s", track_name="Main Video")
    if segment is None:
        raise RuntimeError("Video import failed")
    project.script.import_srt(
        str(output_srt),
        "中英双语字幕",
        text_style=draft.TextStyle(size=args.font_size, align=1, auto_wrapping=True),
        clip_settings=draft.ClipSettings(transform_y=args.transform_y),
    )
    save_result = project.save()
    audit = inspect_draft(Path(save_result["draft_path"]), len(captions))
    emit(
        {
            "ok": True,
            "project": args.project_name,
            "source_duration_s": source_duration,
            "output_srt": str(output_srt),
            **audit,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    transcribe = sub.add_parser("transcribe", help="Transcribe a local English video")
    transcribe.add_argument("--video", required=True)
    transcribe.add_argument("--output-dir", required=True)
    transcribe.add_argument("--deps-dir")
    transcribe.add_argument("--model", default="small")
    transcribe.add_argument("--device", default="cpu")
    transcribe.add_argument("--compute-type", default="int8")
    transcribe.add_argument("--language", default="en")
    transcribe.add_argument("--beam-size", type=int, default=5)
    transcribe.add_argument("--best-of", type=int, default=5)
    transcribe.add_argument("--prompt")
    transcribe.set_defaults(func=cmd_transcribe)

    validate = sub.add_parser("validate", help="Validate curated bilingual JSON")
    validate.add_argument("--curated-json", required=True)
    validate.set_defaults(func=cmd_validate)

    srt = sub.add_parser("srt", help="Create bilingual SRT from curated JSON")
    srt.add_argument("--curated-json", required=True)
    srt.add_argument("--output-srt", required=True)
    srt.set_defaults(func=cmd_srt)

    build = sub.add_parser("build", help="Create a new JianYing draft")
    build.add_argument("--video", required=True)
    build.add_argument("--curated-json", required=True)
    build.add_argument("--output-srt", required=True)
    build.add_argument("--project-name", required=True)
    build.add_argument("--draft-root")
    build.add_argument("--deps-dir")
    build.add_argument("--jianying-skill-root")
    build.add_argument("--font-size", type=float, default=5.0)
    build.add_argument("--transform-y", type=float, default=-0.78)
    build.set_defaults(func=cmd_build)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except SystemExit:
        raise
    except Exception as exc:
        emit({"ok": False, "error": type(exc).__name__, "reason": str(exc)})
        raise SystemExit(1)


if __name__ == "__main__":
    main()
