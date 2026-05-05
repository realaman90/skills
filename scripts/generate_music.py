"""Generate instrumental music using ElevenLabs.

Usage:
    # Basic music generation
    python scripts/generate_music.py --prompt "Soft piano, atmospheric, cinematic" --duration 60 --output score.mp3

    # Longer track
    python scripts/generate_music.py --prompt "..." --duration 130 --output bgm.mp3

NOTE: Do NOT mention artist names in prompts — triggers TOS violation. Describe the style instead.
"""
import os, sys, argparse, requests

def main():
    parser = argparse.ArgumentParser(description="Generate music with ElevenLabs")
    parser.add_argument("--prompt", required=True, help="Music description (NO artist names)")
    parser.add_argument("--output", required=True, help="Output file (.mp3)")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds (default: 60)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if output exists")
    args = parser.parse_args()

    if args.skip_existing and os.path.exists(args.output):
        print(f"SKIP {args.output} (exists)")
        return

    api_key = os.environ["ELEVENLABS_KEY"]
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}

    payload = {
        "prompt": args.prompt,
        "music_length_ms": args.duration * 1000,
        "model_id": "music_v1",
        "force_instrumental": True,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    print(f"Generating {args.duration}s music track...")
    response = requests.post(
        "https://api.elevenlabs.io/v1/music",
        headers=headers, json=payload, timeout=300,
    )

    if response.status_code == 200:
        with open(args.output, "wb") as f:
            f.write(response.content)
        print(f"SAVED {args.output} ({len(response.content)/1024/1024:.1f}MB)")
    else:
        print(f"ERROR {response.status_code}: {response.text[:300]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
