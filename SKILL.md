---
name: ai-film-studio
description: |
  AI film production studio with pre-built scripts. Generates images (Nano Banana 2), video (Veo 3.1, Seedance 2.0, LTX 2.3), audio (ElevenLabs), and assembles final films via ffmpeg or Remotion.
  Use when: creating short films, storyboards, video scenes, voiceovers, music, sound effects, or any AI-powered media creation.
  Trigger words: film, movie, video, storyboard, animate, scene, voiceover, narration, soundtrack, clip, short film.
user-invocable: true
metadata:
  author: realaman90
  version: "1.0.0"
  homepage: "https://github.com/realaman90/skills"
---

# AI Film Studio

End-to-end AI film production. The agent handles creative decisions (prompts, story, pacing). Pre-built scripts handle API plumbing.

## Quick Reference

| Task | Tool |
|------|------|
| Check available models | `python scripts/list_models.py` |
| Generate storyboard still | `python scripts/generate_image.py --prompt "..." --output scene.png` |
| Generate with character ref | `python scripts/generate_image.py --prompt "..." --ref char.png --output scene.png` |
| Generate video from still | `python scripts/generate_video.py --prompt "..." --image scene.png --output scene.mp4` |
| First + last frame video | `python scripts/generate_video.py --prompt "..." --image start.png --last-frame end.png --output scene.mp4` |
| Generate voiceover | `python scripts/generate_tts.py --text "..." --output vo.mp3` |
| Generate music | `python scripts/generate_music.py --prompt "..." --duration 120 --output score.mp3` |
| Generate sound effect | `python scripts/generate_sfx.py --text "..." --duration 8 --output sfx.mp3` |
| Probe media files | `python scripts/probe.py clips/` |
| Assemble (ffmpeg, fast) | `python scripts/assemble.py --videos-dir clips/ --narration vo.mp3 --music score.mp3 --output film.mp4` |
| Scaffold Remotion project | `scripts/new_remotion_project.sh /tmp/my-film` |
| Build scenes.json (Remotion) | `python scripts/build_remotion_timeline.py --project /tmp/my-film --clip clips/a.mp4:10 --image hero.png:4 --title "Intro\|3" --music bgmusic.mp3 --voiceover vo.mp3 --logo logo.png` |
| Render Remotion film | `scripts/render_remotion.sh /tmp/my-film out/film.mp4` |
| Render single thumbnail (PNG) | `scripts/render_remotion.sh /tmp/my-film out/thumb.png --frames=0` |
| Prompting guide: images | Read [reference/nano-banana.md](reference/nano-banana.md) |
| Prompting guide: video | Read [reference/veo.md](reference/veo.md) |
| Voice selection & audio | Read [reference/elevenlabs.md](reference/elevenlabs.md) |
| Remotion patterns & APIs | Read [reference/remotion.md](reference/remotion.md) |
| Generate video (Seedance 2.0) | `python scripts/generate_video_seedance.py --prompt "..." --image scene.png --output clip.mp4` |
| Generate video (LTX 2.3) | `python scripts/generate_video_ltx.py --prompt "..." --image scene.png --output clip.mp4` |
| LTX: extend a clip | `python scripts/generate_video_ltx.py --prompt "..." --video clip.mp4 --output ext.mp4 --endpoint extend-video` |
| LTX: retake a section | `python scripts/generate_video_ltx.py --prompt "..." --video clip.mp4 --output fix.mp4 --endpoint retake-video --start-time 2 --duration 3` |
| LTX: audio-to-video | `python scripts/generate_video_ltx.py --prompt "..." --audio music.mp3 --image scene.png --output mv.mp4 --endpoint audio-to-video` |
| LTX reference (all endpoints) | Read [reference/ltx.md](reference/ltx.md) |
| Seedance reference | Read [reference/seedance.md](reference/seedance.md) |
| Hard-learned lessons | Read [reference/learnings.md](reference/learnings.md) |

**All scripts require `source ~/config.env` first.** If not found, ask the user where it is.

---

## Setup

```bash
source ~/config.env  # MUST run before any API call
pip install google-genai pillow requests
brew install ffmpeg  # macOS
```

`config.env` must define:
- `GEMINI_API_KEY` -- Google AI Studio (images + video)
- `ELEVENLABS_KEY` -- ElevenLabs (voice, music, SFX)
- `ELEVENLABS_VOICE` -- Default voice ID
- `ARK_API_KEY` -- BytePlus Ark (Seedance 2.0 direct API)
- `LTXV_API_KEY` -- LTX direct API (Lightricks)
- `R2_*` -- Cloudflare R2 (optional; used to host local images as URLs for Seedance)

---

## Scripts Reference

All scripts live in `scripts/` and are invoked via CLI. Run any with `--help` for full options.

### generate_image.py -- Nano Banana 2

```bash
# Text-to-image
python scripts/generate_image.py --prompt "A narrow Kyoto street at dusk" --output scene_01.png --aspect 16:9

# With character reference (for consistency across scenes)
python scripts/generate_image.py \
    --prompt "Use the attached reference. Keep facial features identical. [SCENE PROMPT]" \
    --ref refs/character.png \
    --output scene_02.png --aspect 16:9

# Edit existing image (inpainting)
python scripts/generate_image.py --prompt "Remove the person" --edit source.png --output clean.png

# Multiple references
python scripts/generate_image.py --prompt "..." --ref char.png --ref location.png --output scene.png

# Skip if already exists (for batch scripts)
python scripts/generate_image.py --prompt "..." --output scene.png --skip-existing
```

**Model names change frequently.** If "model not found", run:
```bash
python scripts/list_models.py --filter image
```

### generate_video.py -- Veo 3.1

```bash
# Image-to-video (most common for films — storyboard still as first frame)
python scripts/generate_video.py \
    --prompt "Slow dolly forward. Cherry blossoms drift. Ambient: evening crickets, flowing water." \
    --image storyboard/scene_01.png \
    --output clips/scene_01.mp4

# First + last frame interpolation (for transitions with clear start/end states)
python scripts/generate_video.py \
    --prompt "Bird unfolds wings, lifts off workbench" \
    --image storyboard/bird_folded.png \
    --last-frame storyboard/bird_flying.png \
    --output clips/bird.mp4
    # NOTE: automatically switches to full model, duration=8s

# Text-to-video (no reference image)
python scripts/generate_video.py --prompt "A sunset over mountains" --output sunset.mp4

# Higher resolution
python scripts/generate_video.py --prompt "..." --image s.png --output clip.mp4 --resolution 1080p
```

**Two models:**
| Model | Flag | Cost | Features |
|-------|------|------|----------|
| Lite | `--model lite` (default) | Cheap, fast | Image-to-video, text-to-video |
| Full | `--model full` | Expensive | + first+last frame, extensions, refs |

**Constraints:** `--last-frame` requires full model + duration=8. 1080p/4K require duration=8. Extensions are 720p only.

### generate_video_seedance.py -- Seedance 2.0 (BytePlus Ark direct)

```bash
# Image-to-video (image auto-uploaded to R2, or pass an already-hosted URL)
python scripts/generate_video_seedance.py \
    --prompt "Camera slowly dollies forward, gentle movement" \
    --image storyboard/scene_01.png \
    --output clips/scene_01.mp4

# Already-hosted image URL
python scripts/generate_video_seedance.py \
    --prompt "..." --image-url https://example.com/img.png --output clip.mp4

# Multiple reference images (up to 9, first is opening frame)
python scripts/generate_video_seedance.py --prompt "..." \
    --image start.png --image end.png --output clip.mp4

# With reference video (replicate camera/motion) + reference audio (BGM)
python scripts/generate_video_seedance.py --prompt "..." \
    --image scene.png --ref-video ref.mp4 --ref-audio bgm.mp3 --output clip.mp4

# Fast model (draft, cheaper)
python scripts/generate_video_seedance.py --prompt "..." --image scene.png --output clip.mp4 --model fast

# Portrait aspect ratio, longer clip
python scripts/generate_video_seedance.py --prompt "..." --image scene.png --output clip.mp4 \
    --duration 11 --ratio 9:16
```

**Models:** `full` = `dreamina-seedance-2-0-260128` (quality). `fast` = `dreamina-seedance-2-0-fast-260128` (drafts).
**API:** POST to `https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks`, then poll `/tasks/{id}` until `status=succeeded`. Script handles polling automatically.

**⚠️ CRITICAL: Seedance blocks photorealistic human faces.** Error: content policy violation. Workarounds:
- Use 3D / Pixar-style characters (these pass the filter)
- Use product-only shots (no faces)
- Use texture/detail close-ups
- Switch to LTX 2.3 or Veo for photorealistic face shots

### generate_video_ltx.py -- LTX 2.3 (direct API)

Full docs: [reference/ltx.md](reference/ltx.md). API: `https://api.ltx.video/v1` — binary video returned directly in the POST response, no polling.

```bash
# Image-to-video (fast model, default) — storyboard-to-clip
python scripts/generate_video_ltx.py \
    --prompt "Camera slowly pushes in, ambient city sounds" \
    --image storyboard/scene_01.png \
    --output clips/scene_01.mp4

# Pro quality
python scripts/generate_video_ltx.py --prompt "..." --image scene.png --output clip.mp4 \
    --ltx-model ltx-2-3-pro

# Text-to-video (no image)
python scripts/generate_video_ltx.py --prompt "A sunset over mountains" \
    --output sunset.mp4 --endpoint text-to-video

# End frame transition (ltx-2-3 only)
python scripts/generate_video_ltx.py --prompt "..." --image start.png --end-image end.png \
    --output transition.mp4

# Extend an existing clip
python scripts/generate_video_ltx.py \
    --prompt "She continues walking and turns the corner" \
    --video clips/scene_01.mp4 \
    --output clips/scene_01_extended.mp4 \
    --endpoint extend --duration 5 --extend-mode end

# Retake a section (fix distortions without regenerating whole clip)
python scripts/generate_video_ltx.py \
    --prompt "She smiles warmly" \
    --video clips/scene_01.mp4 \
    --output clips/scene_01_fixed.mp4 \
    --endpoint retake --start-time 2 --duration 3

# Retake audio only (keep video)
python scripts/generate_video_ltx.py \
    --prompt "Gentle rain and footsteps" \
    --video clip.mp4 --output clip_audio.mp4 \
    --endpoint retake --start-time 0 --duration 5 --retake-mode replace_audio

# Audio-to-video (sync video to music)
python scripts/generate_video_ltx.py \
    --prompt "Woman dancing in a modern studio" \
    --audio music.mp3 --image dancer.png \
    --output music_video.mp4 --endpoint audio-to-video

# Predefined camera motion
python scripts/generate_video_ltx.py --prompt "..." --image scene.png --output clip.mp4 \
    --camera-motion dolly_in
```

| Endpoint | Flag | LTX Path | Notes |
|----------|------|----------|-------|
| Image-to-video | `--endpoint image-to-video` (default) | `/image-to-video` | Storyboard-to-clip |
| Text-to-video | `--endpoint text-to-video` | `/text-to-video` | No reference image needed |
| Extend | `--endpoint extend` | `/extend` | Extend start or end (2-20s) |
| Retake | `--endpoint retake` | `/retake` | Fix sections in-place |
| Audio-to-video | `--endpoint audio-to-video` | `/audio-to-video` | Sync to audio input |

**Models:** `ltx-2-fast`, `ltx-2-pro`, `ltx-2-3-fast` (default), `ltx-2-3-pro`. End-frame interpolation requires `ltx-2-3`.
**Resolution:** `1920x1080`, `1080x1920`, `3840x2160`.
**Uploads:** Local files auto-uploaded via LTX `/upload` endpoint (pre-signed URL -> storage_uri). No R2 needed for LTX.
**No face blocking** — unlike Seedance, LTX works with photorealistic faces.

### Video Model Comparison

| Feature | Veo 3.1 | Seedance 2.0 | LTX 2.3 |
|---------|---------|-------------|---------|
| Provider | Google | BytePlus Ark (ByteDance) | Lightricks (direct) |
| Human faces | ✅ Works | ❌ Blocked | ✅ Works |
| Duration | 4-8s | up to ~12s | 2-20s |
| Max resolution | 4K | ~720p | 2160p |
| First+last frame | ✅ (full model) | ✅ | ✅ (ltx-2-3) |
| Audio generation | Built-in | `generate_audio` flag | `generate_audio` flag |
| Best for | Quality, faces | Products, 3D chars, motion refs | Cheap, long clips, faces |

### generate_tts.py -- ElevenLabs Voice

```bash
# Narration with default voice
python scripts/generate_tts.py --text "In a quiet corner of Kyoto..." --output vo_01.mp3

# Specific voice (see reference/elevenlabs.md for voice IDs)
python scripts/generate_tts.py --text "..." --voice onwK4e9ZLuTAKqWW03F9 --output vo.mp3

# Dramatic delivery
python scripts/generate_tts.py --text "..." --output vo.mp3 --stability 0.3 --style 0.15 --speed 0.9

# From text file
python scripts/generate_tts.py --file script.txt --output narration.mp3

# With word-level timestamps (for subtitles)
python scripts/generate_tts.py --text "..." --output vo.mp3 --timestamps subs.json
```

**Voice presets:** Audiobook: `--stability 0.50 --speed 0.95`. Dramatic: `--stability 0.30 --style 0.15`. News: `--stability 0.70`.

### generate_music.py -- ElevenLabs Music

```bash
python scripts/generate_music.py \
    --prompt "Gentle piano and strings, atmospheric, emotional, building to crescendo, bittersweet resolution" \
    --duration 120 \
    --output music/score.mp3
```

**Do NOT mention artist names** -- triggers TOS violation. Describe the style instead.

### generate_sfx.py -- ElevenLabs Sound Effects

```bash
python scripts/generate_sfx.py --text "Old clock ticking rhythmically" --duration 10 --output sfx/ticking.mp3
python scripts/generate_sfx.py --text "Gentle rain on window" --duration 15 --loop --output sfx/rain.mp3
```

### assemble.py -- Final Film Assembly (ffmpeg)

```bash
# Basic: concat clips + narration + music
python scripts/assemble.py \
    --videos-dir clips/ \
    --narration audio/narration.mp3 \
    --music audio/score.mp3 \
    --output final/film.mp4

# Full control with SFX layers
python scripts/assemble.py \
    --videos-dir clips/ \
    --narration audio/narration.mp3 --narration-delay 1000 \
    --music audio/score.mp3 --music-volume 0.15 \
    --sfx "audio/sfx/ticking.mp3:0:0.08" "audio/sfx/shimmer.mp3:24000:0.10" \
    --fade-in 2 --fade-out 3 \
    --output final/film.mp4
```

SFX format: `file:delay_ms:volume` -- delay is when the effect starts (in milliseconds).

### probe.py -- Media File Inspector

```bash
python scripts/probe.py clips/              # Full info for all clips
python scripts/probe.py clips/ --format table   # Compact table
python scripts/probe.py clips/ --format duration # Just durations
python scripts/probe.py final/film.mp4       # Single file
```

---

## Film Production Workflow

### Step 1: Script & Scene Breakdown

Write the narration script. Break into scenes with timestamps, camera directions, and VO lines.

Define **two types of lock blocks** -- identical text descriptions copy-pasted into every relevant prompt:

**Character Lock Block** -- one per recurring character:
```
TAKESHI (old) -- Elderly Japanese man, late 70s, thin white hair swept back,
wire-rimmed round spectacles, gentle weathered face. Worn dark brown wool vest
over cream linen shirt, leather work apron with tool pockets.
```

**Set Lock Block** -- one per recurring location:
```
WORKSHOP -- Traditional Japanese clock repair workshop. Wooden workbench against
back wall, single oil lamp on left side of bench. Walls floor-to-ceiling with
clocks: 3 grandfather clocks on the left, rows of pendulum clocks above the bench,
pocket watches on hooks to the right. Wooden stool. Scattered brass gears, tweezers,
magnifying loupe on the bench surface. Small mechanical brass bird near the right
edge of the workbench.
```

### Step 2: Reference Images (Characters + Sets)

Generate references for BOTH characters AND locations. This is how you maintain visual consistency across scenes.

**Character references** -- 1:1 portraits, clean background:
```bash
python scripts/generate_image.py \
    --prompt "Character reference sheet. Front-facing portrait of: [CHARACTER LOCK BLOCK]. Simple neutral background. Clear lighting. Keep facial features exactly the same." \
    --output refs/character.png --aspect 1:1
```

**Set references** -- the key locations from specific angles:
```bash
# Wide reference of the full set
python scripts/generate_image.py \
    --prompt "[STYLE BLOCK] [SET LOCK BLOCK]. Wide establishing shot showing the full room layout. Clear lighting to show all details. This is a set reference for animation -- every object position must be remembered." \
    --output refs/workshop_wide.png --aspect 16:9

# Close-up reference of important surfaces (tables, desks, dashboards)
python scripts/generate_image.py \
    --prompt "[STYLE BLOCK] Close-up of the workbench surface from [SET LOCK BLOCK]. Show exact tool layout: oil lamp on left, scattered gears in center, magnifying loupe, tweezers, small brass bird near right edge. This is a prop reference -- object positions must stay consistent." \
    --output refs/workbench_closeup.png --aspect 16:9
```

**Review and approve ALL references before generating any scene stills.**

### Step 3: Storyboard Stills

Generate a still for each scene, passing BOTH character ref AND set ref:
```bash
# Scene in workshop with character -- pass BOTH refs
python scripts/generate_image.py \
    --prompt "Use the attached references for character and set. Keep character features and room layout identical to the references. [STYLE BLOCK] [CHARACTER LOCK BLOCK] [SET LOCK BLOCK] [SCENE DESCRIPTION]" \
    --ref refs/character.png \
    --ref refs/workshop_wide.png \
    --output storyboard/scene_02.png --aspect 16:9

# Close-up scene -- pass workbench ref
python scripts/generate_image.py \
    --prompt "Use the attached reference for the workbench layout. Keep all object positions identical. [STYLE BLOCK] [SET LOCK BLOCK] [SCENE DESCRIPTION]" \
    --ref refs/workbench_closeup.png \
    --output storyboard/scene_03.png --aspect 16:9

# Scene in a different location (no set ref needed, just character)
python scripts/generate_image.py \
    --prompt "Use the attached reference for the character. [STYLE BLOCK] [CHARACTER LOCK BLOCK] [SCENE DESCRIPTION]" \
    --ref refs/character.png \
    --output storyboard/scene_06.png --aspect 16:9
```

**Consistency checklist before approving stills:**
- Same face across all scenes with that character?
- Same room layout in all workshop scenes?
- Same objects on the workbench in every close-up?
- Props introduced in earlier scenes still present in later ones?
- Lighting consistent within the same time-of-day?

**Do not generate video until ALL stills are reviewed and approved.**

### Step 4: Video Clips

For each scene, choose the right method:

| Scene Type | Method | Command |
|-----------|--------|---------|
| Single continuous action | Image-to-video | `--image scene.png` |
| Clear start/end transformation | First+last frame | `--image start.png --last-frame end.png` |
| No reference needed | Text-to-video | Just `--prompt` |

```bash
# Most scenes: image-to-video
python scripts/generate_video.py \
    --prompt "[CAMERA] + [ACTION] + [LIGHTING] + [AUDIO DIRECTION]" \
    --image storyboard/scene_01.png \
    --output clips/scene_01.mp4

# Transformation scenes: first+last frame
python scripts/generate_video.py \
    --prompt "Smooth transition, wings unfold..." \
    --image storyboard/bird_start.png \
    --last-frame storyboard/bird_end.png \
    --output clips/bird.mp4
```

### Step 5: Audio

Generate voiceover, music, and SFX as separate files:
```bash
# Voiceover (full narration or per-scene segments)
python scripts/generate_tts.py --file script.txt --output audio/narration.mp3 --speed 0.9

# Background music
python scripts/generate_music.py --prompt "..." --duration 120 --output audio/score.mp3

# SFX per scene
python scripts/generate_sfx.py --text "Clock ticking" --duration 10 --output audio/sfx/ticking.mp3
```

### Step 6: Assemble

```bash
python scripts/assemble.py \
    --videos-dir clips/ \
    --narration audio/narration.mp3 \
    --music audio/score.mp3 \
    --sfx "audio/sfx/ticking.mp3:0:0.08" \
    --output final/film.mp4
```

### Step 7: Review & Iterate

Watch the film. Identify gaps:
- **Missing transitions** -- generate additional clips or extend scenes
- **Pacing issues** -- re-generate VO segments with different speed
- **Audio mix** -- adjust volumes in assemble.py
- **Character drift** -- regenerate stills with character reference images
- **Set drift** -- regenerate stills with set reference images
- **Prop continuity** -- check objects don't appear/disappear between scenes

---

## Visual Consistency Rules

These are hard-learned lessons. Follow them or the film will look like unrelated images stitched together.

### Three Layers of Consistency

| Layer | What it means | How to enforce |
|-------|--------------|----------------|
| **Character** | Same face, hair, clothes, build across all scenes | Character ref image + Character Lock Block in every prompt |
| **Set/Location** | Same room layout, wall decorations, furniture positions | Set ref image + Set Lock Block in every prompt |
| **Props** | Objects don't teleport, appear, or vanish between shots | Workbench ref image + explicit prop descriptions |

### Reference Image Strategy

For a film with one main location and one character, you need at minimum:
```
refs/
  character_front.png      # 1:1 portrait, clean background
  location_wide.png        # 16:9 wide shot of the full set
  location_detail.png      # 16:9 close-up of key surface (desk, workbench)
```

For each scene, pass ALL relevant refs:
```bash
# Workshop scene with character = character ref + location ref (up to 4 refs total)
python scripts/generate_image.py \
    --ref refs/character.png --ref refs/location_wide.png \
    --prompt "..." --output scene.png

# Close-up of table/hands = workbench detail ref
python scripts/generate_image.py \
    --ref refs/location_detail.png \
    --prompt "..." --output scene.png
```

### Common Continuity Mistakes

| Mistake | Example | Fix |
|---------|---------|-----|
| Table changes between shots | Scene 2 has cluttered bench, scene 3 has clean bench | Use same workbench reference for both |
| Object appears from nowhere | Mechanical bird wasn't on table in earlier scenes | Include the bird in the Set Lock Block from scene 1 |
| Room layout changes | Clocks on left wall in one shot, right wall in next | Use same wide room reference for all workshop scenes |
| Lighting direction flips | Window on left in scene 2, on right in scene 4 | Specify window position in Set Lock Block |
| Character outfit changes | Vest in one scene, no vest in next | Always include full outfit in Character Lock Block |
| Color palette drifts | Scene 2 is blue-cool, scene 4 is warm-amber for same room | Specify the palette in the Set Lock Block |

### The Set Lock Block Pattern

A Set Lock Block works exactly like a Character Lock Block -- identical text copy-pasted into every prompt for that location:

```
WORKSHOP -- Traditional Japanese clock repair workshop interior. Single room.
LAYOUT: Wooden workbench against the back wall, centered. Single oil lamp on
the LEFT side of the workbench. Wooden stool in front of the bench.
WALLS: Floor-to-ceiling clocks -- three tall grandfather clocks on the LEFT wall,
rows of smaller pendulum clocks ABOVE the workbench, pocket watches on hooks
to the RIGHT of the bench. Wooden shelves with tools on the far right.
WORKBENCH SURFACE: Scattered brass gears, fine tweezers, small screwdrivers,
a magnifying loupe, a small mechanical brass bird sitting near the RIGHT edge.
WINDOW: Single window on the LEFT wall, above the grandfather clocks.
LIGHTING: Single oil lamp on workbench provides the only warm light.
Rest of the room in cool shadows.
```

**Key details to lock:**
- LEFT/RIGHT positions of major objects (window, lamp, door)
- What's on surfaces (specific props, their positions)
- What's on walls (arrangement of decorations)
- Light source positions
- Floor material, ceiling height, room shape

---

## Prompting Cheat Sheet

### Images (Nano Banana 2)
```
[Subject + Adjectives] + [Action] + [Location] + [Composition/Camera] + [Style]
```
Write like briefing an artist. Full sentences, not keywords. Be specific about materials and lighting. See [reference/nano-banana.md](reference/nano-banana.md).

### Video (Veo 3.1)
```
[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]
[Audio direction: Ambient/SFX/Dialogue]
```
**ONE camera movement per clip.** Name physical light sources. Front-load what matters most. Keep under 175 words. See [reference/veo.md](reference/veo.md).

### Video (LTX 2.3)
```
[Shot Establishment] + [Scene Setting] + [Action Sequence] + [Character Definition] + [Camera Movement] + [Audio Description]
```
Write as **single flowing paragraph in present tense**. LTX responds best to **long, detailed prompts** — match prompt length to clip duration. For image-to-video, focus on **motion not appearance** (image defines the look). Break dialogue into short phrases with acting directions. Include audio descriptions ("sound of rain," "soft piano"). See [reference/ltx.md](reference/ltx.md).

**Key differences from Veo:**
- Longer prompts = better (Veo: under 175 words. LTX: more = better)
- Duration up to 20s (Veo: max 8s)
- Describe audio explicitly (Veo: built-in)
- No face blocking (Seedance blocks faces)
- Use physical emotion cues, never abstract labels ("sad" -> "eyes downcast, shoulders slumped")

### Lock Blocks (copy-paste into EVERY relevant prompt)

**Character Lock Block:**
```
MAREN -- Nordic woman, early 30s, blonde hair in low messy bun, fair complexion,
high cheekbones, light blue-grey eyes. Dark charcoal wool cardigan over cream shirt,
dark indigo jeans, brown leather boots. Gold locket necklace.
```

**Set Lock Block:**
```
CABIN -- Small wooden cabin interior. Stone fireplace on LEFT wall, crackling fire.
Oak desk CENTERED against back wall with typewriter, stack of letters, oil lamp.
Window on RIGHT wall showing snowy forest. Braided rug on wooden floor.
Bookshelves flanking the fireplace.
```

---

## Error Recovery

| Problem | Fix |
|---------|-----|
| Model not found | `python scripts/list_models.py` -- names change frequently |
| No image in response | Check prompt isn't triggering safety filter |
| Character drifts between scenes | Use `--ref` with same character ref image every time |
| Set/room changes between scenes | Use `--ref` with same location ref image every time |
| Props appear/disappear | Include all props in Set Lock Block from the first scene |
| Veo audio sounds random | Always include `Ambient:` or `SFX:` in video prompt |
| Video jitter | Convert VFR to CFR: `ffmpeg -i in.mp4 -r 24 -vsync cfr out.mp4` |
| ElevenLabs music TOS error | Remove artist/brand names, describe style only |
| `generate_audio` not supported | AI Studio doesn't support this param -- audio is always on |
| first+last frame fails on lite | Script auto-switches to full model |
| Color palette drifts across scenes | Specify exact palette in each prompt, say "NOT orange" etc |
