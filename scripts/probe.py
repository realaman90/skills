"""Probe media files for duration, resolution, codec info.

Usage:
    # Single file
    python scripts/probe.py video.mp4

    # Directory of files
    python scripts/probe.py clips/

    # Just durations
    python scripts/probe.py clips/ --format duration
"""
import os, sys, argparse, subprocess, glob

def find_ffprobe():
    for path in ["/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe", "ffprobe"]:
        try:
            subprocess.run([path, "-version"], capture_output=True, check=True)
            return path
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    print("ERROR: ffprobe not found")
    sys.exit(1)

def probe_file(ffprobe, filepath):
    """Get file info."""
    info = {"file": os.path.basename(filepath)}

    # Duration
    r = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", filepath],
        capture_output=True, text=True,
    )
    info["duration"] = float(r.stdout.strip()) if r.stdout.strip() else 0

    # Video stream
    r = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,codec_name",
         "-of", "csv=p=0", filepath],
        capture_output=True, text=True,
    )
    if r.stdout.strip():
        parts = r.stdout.strip().split(",")
        if len(parts) >= 4:
            info["codec"] = parts[0]
            info["width"] = parts[1]
            info["height"] = parts[2]
            info["fps"] = parts[3]

    # Audio stream
    r = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=codec_name",
         "-of", "default=noprint_wrappers=1:nokey=1", filepath],
        capture_output=True, text=True,
    )
    info["audio"] = r.stdout.strip() if r.stdout.strip() else "none"

    # File size
    info["size_mb"] = os.path.getsize(filepath) / 1024 / 1024

    return info

def main():
    parser = argparse.ArgumentParser(description="Probe media files")
    parser.add_argument("path", help="File or directory to probe")
    parser.add_argument("--format", default="full", choices=["full", "duration", "table"],
                        help="Output format")
    args = parser.parse_args()

    ffprobe = find_ffprobe()

    if os.path.isdir(args.path):
        files = sorted(
            glob.glob(os.path.join(args.path, "*.mp4")) +
            glob.glob(os.path.join(args.path, "*.mp3")) +
            glob.glob(os.path.join(args.path, "*.wav"))
        )
    else:
        files = [args.path]

    total_dur = 0
    for f in files:
        info = probe_file(ffprobe, f)
        total_dur += info["duration"]

        if args.format == "duration":
            print(f"{info['file']}: {info['duration']:.1f}s")
        elif args.format == "table":
            res = f"{info.get('width','?')}x{info.get('height','?')}" if 'width' in info else "audio"
            print(f"{info['file']:30} {info['duration']:6.1f}s  {res:12}  {info['size_mb']:.1f}MB")
        else:
            print(f"\n{info['file']}:")
            print(f"  Duration: {info['duration']:.1f}s")
            if 'width' in info:
                print(f"  Video: {info['codec']} {info['width']}x{info['height']} @ {info['fps']}")
            print(f"  Audio: {info['audio']}")
            print(f"  Size: {info['size_mb']:.1f}MB")

    if len(files) > 1:
        print(f"\nTotal: {len(files)} files, {total_dur:.1f}s")

if __name__ == "__main__":
    main()
