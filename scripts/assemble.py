"""Assemble video clips + audio layers into a final film using ffmpeg.

Usage:
    # Basic: concatenate clips + overlay narration + music
    python scripts/assemble.py \
        --videos scene_01.mp4 scene_02.mp4 scene_03.mp4 \
        --narration narration.mp3 \
        --music score.mp3 \
        --output final.mp4

    # With SFX layers (format: file:delay_ms:volume)
    python scripts/assemble.py \
        --videos scene_01.mp4 scene_02.mp4 \
        --narration narration.mp3 --narration-delay 1000 \
        --music score.mp3 --music-volume 0.15 \
        --sfx "tick.mp3:0:0.08" "shimmer.mp3:24000:0.10" "bird.mp3:82000:0.15" \
        --fade-in 2 --fade-out 3 \
        --output final.mp4

    # Videos from directory (sorted by name)
    python scripts/assemble.py \
        --videos-dir clips/ \
        --narration narration.mp3 \
        --music score.mp3 \
        --output final.mp4
"""
import os, sys, argparse, subprocess, glob, tempfile

def find_ffmpeg():
    """Find ffmpeg binary."""
    for path in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "ffmpeg"]:
        try:
            subprocess.run([path, "-version"], capture_output=True, check=True)
            return path
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    print("ERROR: ffmpeg not found. Install with: brew install ffmpeg")
    sys.exit(1)

def find_ffprobe():
    """Find ffprobe binary."""
    for path in ["/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe", "ffprobe"]:
        try:
            subprocess.run([path, "-version"], capture_output=True, check=True)
            return path
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return None

def get_duration(ffprobe, filepath):
    """Get duration of a media file."""
    if not ffprobe:
        return None
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", filepath],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None

def main():
    parser = argparse.ArgumentParser(description="Assemble film from clips + audio")
    video_group = parser.add_mutually_exclusive_group(required=True)
    video_group.add_argument("--videos", nargs="+", help="Video clip files in order")
    video_group.add_argument("--videos-dir", help="Directory of video clips (sorted by name)")
    parser.add_argument("--narration", default=None, help="Narration audio file")
    parser.add_argument("--narration-delay", type=int, default=1000, help="Narration delay in ms (default: 1000)")
    parser.add_argument("--music", default=None, help="Background music file")
    parser.add_argument("--music-volume", type=float, default=0.15, help="Music volume 0-1 (default: 0.15)")
    parser.add_argument("--music-fade-in", type=float, default=3, help="Music fade-in seconds")
    parser.add_argument("--music-fade-out", type=float, default=5, help="Music fade-out seconds")
    parser.add_argument("--sfx", nargs="*", default=[], help="SFX layers as 'file:delay_ms:volume'")
    parser.add_argument("--fade-in", type=float, default=2, help="Video fade-in seconds")
    parser.add_argument("--fade-out", type=float, default=3, help="Video fade-out seconds")
    parser.add_argument("--output", required=True, help="Output file (.mp4)")
    parser.add_argument("--crf", type=int, default=18, help="Video quality CRF (default: 18)")
    args = parser.parse_args()

    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe()

    # Collect video files
    if args.videos_dir:
        videos = sorted(glob.glob(os.path.join(args.videos_dir, "*.mp4")))
        if not videos:
            print(f"ERROR: No .mp4 files in {args.videos_dir}")
            sys.exit(1)
    else:
        videos = args.videos

    print(f"Videos: {len(videos)} clips")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    # Step 1: Concatenate videos (strip native audio)
    concat_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    for v in videos:
        concat_file.write(f"file '{os.path.abspath(v)}'\n")
    concat_file.close()

    concat_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    print("Step 1: Concatenating video clips...")
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file.name, "-an", "-c:v", "copy", concat_video,
    ], capture_output=True, check=True)

    total_dur = get_duration(ffprobe, concat_video) or 96.0
    print(f"  Total video duration: {total_dur:.1f}s")

    # Step 2: Build audio mix
    audio_inputs = []
    filter_parts = []
    stream_labels = []
    input_idx = 0  # 0 is the video

    has_audio = args.narration or args.music or args.sfx

    if not has_audio:
        # No audio — just add fades to video
        print("Step 2: No audio layers. Adding video fades only...")
        fade_out_start = max(0, total_dur - args.fade_out)
        subprocess.run([
            ffmpeg, "-y", "-i", concat_video,
            "-vf", f"fade=t=in:st=0:d={args.fade_in},fade=t=out:st={fade_out_start}:d={args.fade_out}",
            "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
            "-movflags", "+faststart", args.output,
        ], capture_output=True, check=True)
    else:
        print("Step 2: Mixing audio layers...")
        cmd = [ffmpeg, "-y", "-i", concat_video]

        if args.narration:
            cmd.extend(["-i", args.narration])
            input_idx += 1
            filter_parts.append(
                f"[{input_idx}:a]adelay={args.narration_delay}|{args.narration_delay},volume=1.0[vo]"
            )
            stream_labels.append("[vo]")

        if args.music:
            cmd.extend(["-i", args.music])
            input_idx += 1
            fade_out_start = max(0, total_dur - args.music_fade_out - 2)
            filter_parts.append(
                f"[{input_idx}:a]volume={args.music_volume},"
                f"afade=t=in:st=0:d={args.music_fade_in},"
                f"afade=t=out:st={fade_out_start}:d={args.music_fade_out}[music]"
            )
            stream_labels.append("[music]")

        for sfx_spec in args.sfx:
            parts = sfx_spec.split(":")
            if len(parts) != 3:
                print(f"  WARNING: Invalid SFX spec '{sfx_spec}', expected 'file:delay_ms:volume'")
                continue
            sfx_file, delay_ms, volume = parts[0], parts[1], parts[2]
            cmd.extend(["-i", sfx_file])
            input_idx += 1
            label = f"sfx{input_idx}"
            filter_parts.append(
                f"[{input_idx}:a]adelay={delay_ms}|{delay_ms},volume={volume}[{label}]"
            )
            stream_labels.append(f"[{label}]")

        # Build final mix
        n_streams = len(stream_labels)
        mix_input = "".join(stream_labels)
        fade_out_start = max(0, total_dur - args.fade_out)
        video_fade = f"fade=t=in:st=0:d={args.fade_in},fade=t=out:st={fade_out_start}:d={args.fade_out}"

        filter_complex = ";".join(filter_parts)
        filter_complex += f";{mix_input}amix=inputs={n_streams}:duration=longest:dropout_transition=3,alimiter=limit=0.95[mixed]"
        filter_complex += f";[0:v]{video_fade}[vout]"

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[mixed]",
            "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            args.output,
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ffmpeg error: {result.stderr[-500:]}")
            sys.exit(1)

    # Cleanup
    os.unlink(concat_file.name)
    os.unlink(concat_video)

    final_dur = get_duration(ffprobe, args.output) or 0
    final_size = os.path.getsize(args.output) / 1024 / 1024

    print(f"\nDONE!")
    print(f"  Output: {args.output}")
    print(f"  Duration: {final_dur:.1f}s")
    print(f"  Size: {final_size:.1f}MB")

if __name__ == "__main__":
    main()
