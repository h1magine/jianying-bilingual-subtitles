# Bilingual Subtitle Review Guide

Use this guide after transcription and before JianYing import.

## Curated JSON schema

```json
{
  "source": "input-video.webm",
  "notes": "Context-corrected English and natural Simplified Chinese.",
  "captions": [
    {
      "start": 12.34,
      "end": 15.67,
      "en": "Corrected English subtitle.",
      "zh": "自然的简体中文字幕。"
    }
  ]
}
```

Times are seconds. Cues must be chronological, non-overlapping, and have non-empty `en` and `zh` values.

## Review order

1. Read the full transcript once to identify the topic, setting, speaker roles, recurring names, and technical vocabulary.
2. Review in 30–90 second contextual blocks rather than isolated cues.
3. Repair sentence boundaries before word-level corrections. Join fragments that form one thought; split cues that contain two unrelated thoughts.
4. Resolve uncertain words using, in order: nearby dialogue, repeated terminology, visible action/title context, clearer later mentions, embedded/official captions, and targeted audio review.
5. Translate only after the English cue is coherent.
6. Read the Chinese alone as if it were an original subtitle track. Remove translationese, excessive pronouns, and needlessly formal constructions.

Do not silently replace an unclear proper noun with a plausible invention. If it remains unresolved after reasonable checks, preserve a neutral rendering or mark it briefly as unclear.

## Translation voice

- Host or announcer: concise, commanding, energetic.
- Judge or expert: technically exact, controlled, and confident.
- Contestant: conversational and idiomatic; keep humor, frustration, and rough edges without making the Chinese awkward.
- Narration: compact and explanatory.

Translate idioms by function. For example, “put up or shut up” should convey “拿出真本事” rather than a literal word-for-word version.

## Timing and readability

- Prefer one complete thought per cue.
- Merge sub-second filler fragments into adjacent speech when meaning and timing allow.
- Prefer roughly 1.2–7 seconds per cue; allow exceptions for rapid exchanges or isolated exclamations.
- The final SRT uses two visual lines: corrected English, then Simplified Chinese.
- Keep both lines concise enough for the available duration. Condense the Chinese without dropping factual content.
- Do not extend a caption across a long silence merely to make it longer.

## Common forging and weapon terms

| English | Simplified Chinese |
|---|---|
| spear | 长矛 |
| javelin | 标枪 |
| throwing knife | 投掷刀 |
| throwing spike | 投掷锥 |
| battle-axe | 战斧 |
| hatchet | 手斧 |
| mace | 钉头锤 / 战锤（按造型与语境） |
| war club | 战棍 |
| chain mail | 锁子甲 |
| plate armor | 板甲 |
| haft / shaft | 柄 / 长柄 / 杆（按武器类型） |
| spike | 尖刺 / 锥刺 |
| heat-treat | 热处理 |
| quench | 淬火 |
| forge out | 锻打成形 |
| press | 锻压机 |
| fit and finish | 装配与表面收尾 |
| confirmed kill | 确认击杀 |

This glossary is contextual guidance, not a forced mapping. Prefer the term that matches the visible weapon and the speaker's intent.

## Acceptance checklist

- English has been corrected before translation.
- Names, teams, quantities, and technical terms are consistent across the whole video.
- Chinese reads naturally without losing the speaker's attitude.
- No cue has missing text, reversed time, or overlap.
- Final SRT opens as UTF-8 and displays English above Chinese.
- JianYing draft, when requested, has one or more video segments and exactly the expected subtitle segment count.
