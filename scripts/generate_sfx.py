"""Generate sound effects using ElevenLabs.

Usage:
    python scripts/generate_sfx.py --text "Old wooden door creaking open" --output door.mp3
    python scripts/generate_sfx.py --text "Thunder crack" --duration 5 --output thunder.mp3
    python scripts/generate_sfx.py --text "Gentle rain on window" --duration 15 --loop --output rain.mp3
"""
import os, sys, argparse, requests

def main():
    parser = argparse.ArgumentParser(description="Generate SFX with ElevenLabs")
    parser.add_argument("--text", required=True, help="Description of the sound effect")
    parser.add_argument("--output", required=True, help="Output file (.mp3)")
    parser.add_argument("--duration", type=float, default=None, help="Duration in seconds (0.5-30, auto if omitted)")
    parser.add_argument("--influence", type=float, default=0.5, help="Prompt influence 0-1 (default: 0.5)")
    parser.add_argument("--loop", action="store_true", help="Generate seamless loop")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if output exists")
    args = parser.parse_args()

    if args.skip_existing and os.path.exists(args.output):
        print(f"SKIP {args.output} (exists)")
        return

    api_key = os.environ["ELEVENLABS_KEY"]
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}

    payload = {
        "text": args.text,
        "prompt_influence": args.influence,
    }
    if args.duration:
        payload["duration_seconds"] = args.duration
    if args.loop:
        payload["loop"] = True

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    print(f"Generating SFX: {args.text[:60]}...")
    response = requests.post(
        "https://api.elevenlabs.io/v1/sound-generation",
        headers=headers, json=payload,
    )

    if response.status_code == 200:
        with open(args.output, "wb") as f:
            f.write(response.content)
        print(f"SAVED {args.output} ({len(response.content)/1024:.0f}KB)")
    else:
        print(f"ERROR {response.status_code}: {response.text[:200]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
