# 剪映中英双语字幕

把本地英文视频整理为经过语境校正的中英双语字幕，并可选创建剪映草稿。

这个 skill 的重点是：先结合上下文修正英文误识别，再翻译成自然的简体中文。默认英文在上、中文在下，保留中间文件，方便后续修改。

## 能做什么

- 使用 faster-whisper 在本地转写英文视频。
- 由 AI 根据上下文校正误听、人名和术语，再完成中文翻译。
- 校验字幕时间顺序、重叠和缺失文本，生成 UTF-8-BOM 双语 SRT。
- 配合独立的 `jianying-editor` skill 创建新剪映草稿，检查视频片段和字幕片段数量。

Python 脚本本身**不调用翻译 API，也不会自动完成语义校审**。校审和翻译需要支持 skill 的 AI 工具执行指令，或由你手工完成。AI 工具可能涉及订阅或模型调用费用；首次转写需要联网下载模型，之后使用已缓存模型可在本地转写。交给 AI 校审的字幕内容由所使用的 AI 工具处理。

## 安装为 Codex skill

可以将本仓库链接交给 Codex：

```text
请使用 $skill-installer 安装这个仓库中的 skill：
https://github.com/h1magine/jianying-bilingual-subtitles
skill 的 SKILL.md 位于仓库根目录。
```

也可以按 [Codex 官方 skill 文档](https://learn.chatgpt.com/docs/build-skills) 手动安装：将整个仓库文件夹放到用户目录的 `.agents/skills/jianying-bilingual-subtitles`，或项目的 `.agents/skills/jianying-bilingual-subtitles`。请勿覆盖已有的同名 skill；如果已经安装，请先比较版本。新安装后没有显示时，重启 Codex。

然后在存放视频的工作区使用：

```text
使用 $jianying-bilingual-subtitles 处理当前文件夹里的英文视频。
结合语境校正英文，再翻译成自然的简体中文，生成英文在上、中文在下的双语 SRT。
```

需要剪映草稿时，再加上“同时创建一个新的剪映草稿”，并按下文配置额外依赖。

## 先试一个不需要视频的例子

示例是专门编写的两条演示字幕，不含影视原片或真实会议内容。需要 Python 3.10+；下面命令在仓库根目录的 Windows PowerShell 中运行，校验和 SRT 生成无需安装第三方包。

```powershell
py -3 scripts/bilingual_pipeline.py validate --curated-json examples/curated_bilingual.json
py -3 scripts/bilingual_pipeline.py srt --curated-json examples/curated_bilingual.json --output-srt output/demo.srt
```

预期返回 `"ok": true`、`"captions": 2`。生成的字幕应与 [示例 SRT](examples/bilingual.srt) 一致：

```text
1
00:00:00,000 --> 00:00:03,000
Let's check the sound before we start.
开始之前，我们先检查一下声音。
```

## 处理自己的视频

以下命令同样从仓库根目录运行；其他系统可将 `py -3` 替换为相应的 Python 3 命令。

### 1. 安装本地转写依赖

```powershell
py -3 -m pip install --target .subtitle-deps -r requirements-transcribe.txt
```

依赖只装到工作目录。默认使用 CPU 和 `small` 模型，显卡不是必需条件。模型与依赖占用的空间、下载耗时取决于环境。GPU 配置请参考 [faster-whisper 官方说明](https://github.com/SYSTRAN/faster-whisper)。

### 2. 转写

```powershell
py -3 scripts/bilingual_pipeline.py transcribe --video "input.mp4" --output-dir subtitle-work --deps-dir .subtitle-deps
```

将 `input.mp4` 换成实际视频路径。输出 `raw_transcript.json` 和 `raw_english.srt`。已有可信的官方或内嵌英文字幕时，可跳过重新转写，整理为下述数据结构。

### 3. 校正英文并翻译

让 AI 阅读 [校审指南](references/review-guide.md) 和完整转写结果，再生成 `subtitle-work/curated_bilingual.json`。语音不清楚时应回听或标注不确定，不能凭上下文编造事实。

```json
{
  "source": "input.mp4",
  "captions": [
    {
      "start": 0.0,
      "end": 3.0,
      "en": "Let's check the sound before we start.",
      "zh": "开始之前，我们先检查一下声音。"
    }
  ]
}
```

时间单位为秒，每条字幕必须有英文、中文和有效时间范围，按时间排序且不重叠。

### 4. 校验并生成双语字幕

```powershell
py -3 scripts/bilingual_pipeline.py validate --curated-json subtitle-work/curated_bilingual.json
py -3 scripts/bilingual_pipeline.py srt --curated-json subtitle-work/curated_bilingual.json --output-srt output/bilingual.srt
```

可以将 SRT 手动导入支持字幕导入的剪辑软件。请为输出选择新的路径；同名 SRT 和转写输出文件会被覆盖。

## 可选：创建剪映草稿

需要本机剪映、[jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill) 及其依赖。本仓库没有打包该项目的源码，请按上游说明安装到独立目录，并将依赖放入同一个工作区依赖目录。

额外需要 `av` 读取视频信息，以及系统 FFmpeg 或 `imageio-ffmpeg`：

```powershell
py -3 -m pip install --target .subtitle-deps av imageio-ffmpeg
```

安装好上游及其依赖后，使用实际的 skill 路径和剪映草稿目录：

```powershell
py -3 scripts/bilingual_pipeline.py build --video "input.mp4" --curated-json subtitle-work/curated_bilingual.json --output-srt output/bilingual.srt --project-name "MyVideo_Bilingual" --deps-dir .subtitle-deps --jianying-skill-root "D:/tools/jianying-editor" --draft-root "D:/JianyingDrafts"
```

示例中的两个目录需要替换；`--draft-root` 应指向你希望使用的草稿根目录。脚本拒绝覆盖同名草稿。剪映版本可能影响草稿兼容性；生成后请在剪映中打开检查画面、字幕位置和音画同步，再手动导出成片。此命令不负责烧录字幕或导出 MP4。

## 验证范围与限制

- 发布准备阶段在 Windows / Python 3.11 下验证命令入口、演示字幕校验和 SRT 生成。
- 原有工作流曾在本机生成包含 118 条字幕的剪映草稿；这不代表所有剪映版本兼容。
- 本次发布准备未重新下载转写模型、运行真实视频转写或验证剪映界面。
- 其他系统、GPU 配置和不同剪映版本尚未逐一验证。
- 字幕数量检查无法证明翻译准确；最终仍需抽查音频、专有名词和时间轴。

常见问题：缺少 `faster_whisper` 时检查依赖目录；找不到剪映 skill 时显式传入 `--jianying-skill-root`；同名草稿存在时改用新名字；字幕重叠时先修正 JSON 时间轴。

## 项目文件

| 文件 | 用途 |
| --- | --- |
| `SKILL.md` | AI 的触发条件和工作流程 |
| `scripts/bilingual_pipeline.py` | 转写、校验、SRT 和草稿命令 |
| `references/review-guide.md` | 英文校正与中文翻译准则 |
| `agents/openai.yaml` | Codex 显示信息 |
| `examples/` | 可复现的演示输入与输出 |

## 许可与致谢

本项目采用 [MIT License](LICENSE)。第三方依赖及剪映软件分别遵循各自的许可证和使用条款；MIT 许可不包含视频素材或第三方软件的授权。

感谢 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)、[PyAV](https://github.com/PyAV-Org/PyAV) 和 [jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill)。本项目是个人整理的字幕工作流，与剪映官方无隶属关系。
