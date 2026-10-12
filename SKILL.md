---
name: jianying-bilingual-subtitles
description: Generate context-corrected English–Simplified Chinese subtitles for local English videos and optionally create a new JianYing draft. Use when a user wants transcription plus semantic correction, natural Chinese localization, bilingual SRT delivery, or a JianYing project with bilingual captions. Do not use for simple subtitle-format conversion when no transcription, correction, or translation is needed.
---

# JianYing Bilingual Subtitles

Turn a local English video into a reviewed bilingual subtitle package and, when requested, a new JianYing draft. The quality-critical step is editorial: recover the speaker's intended English from context before translating it.

## Workflow

1. Resolve the source video. If the user says “the video in this folder,” inspect only the current folder first and choose the single plausible long-form video; ask only if multiple candidates are genuinely ambiguous.
2. Inspect duration, dimensions, audio presence, and existing subtitle streams. Reuse trustworthy embedded or official English subtitles when available; otherwise transcribe locally.
3. Run `scripts/bilingual_pipeline.py transcribe` to create `raw_transcript.json` and `raw_english.srt`. Use a workspace-local dependency directory rather than modifying global Python.
4. Read [references/review-guide.md](references/review-guide.md), then review the transcript in chronological context. Correct mistranscriptions, names, homophones, sentence boundaries, and domain terms before translating.
5. Create `curated_bilingual.json` using the schema in the review guide. Merge choppy fragments when this improves meaning and readability without changing timing coverage.
6. Run `scripts/bilingual_pipeline.py validate`, then `srt` to emit a UTF-8-BOM bilingual SRT with English above Simplified Chinese.
7. If the user wants JianYing, read and follow the installed `jianying-editor` skill before running `build`. Keep scripts and outputs in the user's workspace, not in either skill directory.
8. Verify the saved draft contains at least one video segment, the expected number of text segments, the source aspect ratio, and the expected duration. Report the project name and delivery files.

## Non-negotiable quality rules

- Infer the intended English from the full scene and subject matter; do not translate obvious ASR errors literally.
- Preserve uncertainty instead of inventing proper nouns or technical terms. Use audio/visual context or authoritative captions to resolve important ambiguities.
- Translate for the speaker's role and personality: hosts should sound decisive, judges technically precise, and contestants natural and conversational.
- Preserve factual meaning, quantities, names, team identities, jokes, and technical distinctions. Localize idioms rather than translating them word for word.
- Keep English first and Simplified Chinese second in each bilingual cue unless the user specifies another layout.
- Do not burn subtitles into the video unless explicitly requested.

## Safety and repeatability

- Never overwrite an existing JianYing draft by default. If the requested project name already exists, stop and choose a new name or obtain explicit permission for a separately designed replacement workflow.
- Creating or reading the JianYing user draft directory may require approval. Request it immediately before that operation, not during transcription or review.
- Install missing Python packages only into a workspace-local directory such as `.subtitle-deps`; do not alter global packages.
- Keep raw transcription, curated JSON, final SRT, and the reusable command/script so the result can be revised without retranscribing.

## Commands

```powershell
py -3 <SKILL_ROOT>\scripts\bilingual_pipeline.py transcribe --video "input.webm" --output-dir ".\subtitle-work"
py -3 <SKILL_ROOT>\scripts\bilingual_pipeline.py validate --curated-json ".\subtitle-work\curated_bilingual.json"
py -3 <SKILL_ROOT>\scripts\bilingual_pipeline.py srt --curated-json ".\subtitle-work\curated_bilingual.json" --output-srt ".\subtitle-work\bilingual_corrected.srt"
py -3 <SKILL_ROOT>\scripts\bilingual_pipeline.py build --video "input.webm" --curated-json ".\subtitle-work\curated_bilingual.json" --output-srt ".\subtitle-work\bilingual_corrected.srt" --project-name "Video_中英双语字幕"
```

Use `--deps-dir` when dependencies live somewhere other than `.subtitle-deps` or `.deps`. Use `--jianying-skill-root` only when automatic discovery fails.
