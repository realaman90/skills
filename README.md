# AI Film Studio

End-to-end AI film production for Claude Code. The agent handles creative decisions (story, prompts, pacing); pre-built scripts handle the API plumbing across image, video, audio, and final assembly.

> Installable via the [skills.sh](https://skills.sh) CLI: `npx skills add realaman90/skills`

## What it does

| Stage | Tool | Backed by |
|---|---|---|
| Storyboard stills | `generate_image.py` | Google Nano Banana 2 (Gemini) |
| Cinematic video | `generate_video.py`, `generate_video_seedance.py`, `generate_video_ltx.py` | Veo 3.1, Seedance 2.0, LTX 2.3 |
| Voiceover / music / SFX | `generate_tts.py`, `generate_music.py`, `generate_sfx.py` | ElevenLabs |
| Asset hosting | auto-upload to Cloudflare R2 | R2 (optional, only for Seedance) |
| Assembly (fast) | `assemble.py` | ffmpeg |
| Assembly (programmable) | `build_remotion_timeline.py` + `render_remotion.sh` | Remotion |

Character consistency, first/last-frame interpolation, clip extension, audio-to-video, retakes, and prompt guides for each model are documented in [`SKILL.md`](SKILL.md) and [`reference/`](reference/).

## Install

Via the [skills.sh](https://skills.sh) CLI (recommended — works for Claude Code, OpenCode, Codex, Cursor, and 50+ other agents):

```bash
npx skills add realaman90/skills          # interactive
npx skills add realaman90/skills -g -y    # global, non-interactive
```

Or clone directly into Claude Code's skills directory:

```bash
git clone https://github.com/realaman90/skills.git ~/.claude/skills/ai-film-studio
```

Either way, install the Python deps:

```bash
pip install -r requirements.txt
brew install ffmpeg          # macOS
```

Trigger words: *film, movie, video, storyboard, animate, scene, voiceover, narration, soundtrack, clip, short film*.

## Setup

```bash
cp config.env.example config.env
# fill in your keys, then:
source config.env
```

Required keys (free tiers exist for most):

| Key | Provider | Used by |
|---|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) | images, Veo video |
| `ELEVENLABS_KEY`, `ELEVENLABS_VOICE` | [ElevenLabs](https://elevenlabs.io) | voice, music, SFX |
| `ARK_API_KEY` | [BytePlus Ark](https://console.byteplus.com/ark) | Seedance 2.0 |
| `LTXV_API_KEY` | [LTX Video](https://docs.ltx.video/authentication) | LTX 2.3 |
| `R2_*` | [Cloudflare R2](https://developers.cloudflare.com/r2/) | optional — hosts local images for Seedance |

## Quick start

```bash
# 1. Storyboard still
python scripts/generate_image.py \
  --prompt "A narrow Kyoto street at dusk, lanterns lit, light rain" \
  --output scene_01.png --aspect 16:9

# 2. Animate it
python scripts/generate_video.py \
  --prompt "Slow dolly forward, ambient evening sounds" \
  --image scene_01.png --output clip_01.mp4

# 3. Voiceover
python scripts/generate_tts.py --text "The street remembers." --output vo.mp3

# 4. Score
python scripts/generate_music.py --prompt "Cinematic ambient strings, slow build" \
  --duration 30 --output score.mp3

# 5. Assemble
python scripts/assemble.py --videos-dir clips/ \
  --narration vo.mp3 --music score.mp3 --output film.mp4
```

For multi-scene films with title cards, b-roll inserts, and synced audio, scaffold a Remotion project instead — see [`SKILL.md`](SKILL.md#remotion).

## Reference docs

| Topic | File |
|---|---|
| Nano Banana prompting | [`reference/nano-banana.md`](reference/nano-banana.md) |
| Veo 3.1 prompting | [`reference/veo.md`](reference/veo.md) |
| Seedance 2.0 (incl. content policy gotchas) | [`reference/seedance.md`](reference/seedance.md) |
| LTX 2.3 (every endpoint) | [`reference/ltx.md`](reference/ltx.md) |
| ElevenLabs voice / music / SFX | [`reference/elevenlabs.md`](reference/elevenlabs.md) |
| Remotion patterns | [`reference/remotion.md`](reference/remotion.md) |
| Hard-learned lessons | [`reference/learnings.md`](reference/learnings.md) |

## Notes

- **Seedance blocks photorealistic human faces.** Use 3D/Pixar-style characters, product shots, or fall back to Veo / LTX. See [`reference/seedance.md`](reference/seedance.md).
- **Models change frequently.** If a script reports "model not found", run `python scripts/list_models.py` to discover current names.
- **Costs are real.** Veo "full" and Seedance generate paid jobs — drafts go through `--model lite` (Veo) or `--model fast` (Seedance).

## License

MIT — see [`LICENSE`](LICENSE).
