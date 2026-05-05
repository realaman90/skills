"""Generate video using Seedance 2.0 via BytePlus Ark direct API.

Endpoint: https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks

Usage:
    # Image-to-video (image must be a public URL; local files auto-upload to R2)
    python scripts/generate_video_seedance.py --prompt "..." --image scene.png --output clip.mp4

    # Text-to-video (no image)
    python scripts/generate_video_seedance.py --prompt "..." --output clip.mp4

    # Multiple reference images (up to 9)
    python scripts/generate_video_seedance.py --prompt "..." \
        --image img1.png --image img2.png --output clip.mp4

    # Reference video (for camera/motion replication)
    python scripts/generate_video_seedance.py --prompt "..." \
        --image img1.png --ref-video ref.mp4 --output clip.mp4

    # Reference audio (for BGM matching)
    python scripts/generate_video_seedance.py --prompt "..." \
        --image img1.png --ref-audio bgm.mp3 --output clip.mp4

    # Fast model (cheaper, quicker drafts)
    python scripts/generate_video_seedance.py --prompt "..." \
        --image scene.png --output clip.mp4 --model fast

    # Custom duration/ratio
    python scripts/generate_video_seedance.py --prompt "..." \
        --image scene.png --output clip.mp4 --duration 10 --ratio 9:16

Requires:
    ARK_API_KEY in environment (BytePlus Ark)
    R2_* env vars for auto-upload of local files (optional if using URLs)
"""
import os, sys, argparse, json, time, urllib.request


def upload_to_r2(local_path, prefix="seedance"):
    """Upload a local file to R2 and return the public URL."""
    try:
        import boto3
        account = os.environ.get("R2_ACCOUNT")
        access = os.environ.get("R2_ACCESS_KEY")
        secret = os.environ.get("R2_SECRET_KEY")
        bucket = os.environ.get("R2_BUCKET")
        public_url = os.environ.get("R2_PUBLIC_URL")
        if not all([account, access, secret, bucket, public_url]):
            return None
        s3 = boto3.client("s3",
            endpoint_url=f"https://{account}.r2.cloudflarestorage.com",
            aws_access_key_id=access,
            aws_secret_access_key=secret,
            region_name="auto",  # Cloudflare R2 requires one of: wnam, enam, weur, eeur, apac, oc, auto
        )
        basename = os.path.basename(local_path)
        key = f"{prefix}/{basename}"
        ext = os.path.splitext(local_path)[1].lower()
        content_types = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".mp4": "video/mp4", ".mov": "video/quicktime",
            ".mp3": "audio/mpeg", ".wav": "audio/wav",
        }
        content_type = content_types.get(ext, "application/octet-stream")
        s3.upload_file(local_path, bucket, key, ExtraArgs={"ContentType": content_type})
        return f"{public_url}/{key}"
    except Exception as e:
        print(f"R2 upload failed: {e}")
        return None


def resolve_url(local_path, url, label="file", prefix="seedance"):
    """Return url if provided, else upload local_path to R2 and return its URL."""
    if url:
        return url
    if not local_path:
        return None
    print(f"Uploading {label} {local_path} to R2...")
    result = upload_to_r2(local_path, prefix)
    if not result:
        print(f"ERROR: Could not upload {label}. Set R2_* env vars or use a URL flag.")
        sys.exit(1)
    print(f"  -> {result}")
    return result


ARK_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODELS = {
    "full": "dreamina-seedance-2-0-260128",
    "fast": "dreamina-seedance-2-0-fast-260128",
}


def ark_request(method, path, api_key, body=None):
    """Minimal HTTP helper for Ark API using urllib (no extra deps)."""
    url = f"{ARK_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {api_key}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = ""
        raise RuntimeError(f"Ark HTTP {e.code}: {err_body}") from e


def main():
    parser = argparse.ArgumentParser(
        description="Seedance 2.0 via BytePlus Ark direct API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--prompt", required=True, help="Video generation prompt")
    parser.add_argument("--output", required=True, help="Output file path (.mp4)")
    parser.add_argument("--model", default="full", choices=["full", "fast"],
                        help="full = dreamina-seedance-2-0-260128 (quality), fast = cheaper/faster")
    parser.add_argument("--image", action="append", default=[],
                        help="Local reference image (repeatable, up to 9; first is the opening frame)")
    parser.add_argument("--image-url", action="append", default=[],
                        help="Hosted reference image URL (repeatable)")
    parser.add_argument("--ref-video", default=None, help="Local reference video file")
    parser.add_argument("--ref-video-url", default=None, help="Hosted reference video URL")
    parser.add_argument("--ref-audio", default=None, help="Local reference audio file (BGM)")
    parser.add_argument("--ref-audio-url", default=None, help="Hosted reference audio URL")
    parser.add_argument("--duration", type=int, default=8,
                        help="Duration in seconds (default: 8)")
    parser.add_argument("--ratio", default="16:9",
                        help="Aspect ratio: 16:9, 9:16, 1:1, 4:3, 3:4, 21:9 (default: 16:9)")
    parser.add_argument("--generate-audio", action="store_true", default=True,
                        help="Generate synchronized audio (default: on)")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio generation")
    parser.add_argument("--watermark", action="store_true", default=False,
                        help="Include BytePlus watermark (default: off)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--poll-interval", type=float, default=5.0,
                        help="Seconds between status polls (default: 5)")
    parser.add_argument("--timeout", type=int, default=900,
                        help="Max seconds to wait for completion (default: 900)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if output exists")
    args = parser.parse_args()

    if args.skip_existing and os.path.exists(args.output):
        print(f"SKIP {args.output} (exists)")
        return

    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        print("ERROR: ARK_API_KEY not set. Run: source config.env")
        sys.exit(1)

    # Resolve all reference URLs
    image_urls = list(args.image_url)
    for img in args.image:
        url = resolve_url(img, None, "image")
        if url:
            image_urls.append(url)
    video_url = resolve_url(args.ref_video, args.ref_video_url, "reference video")
    audio_url = resolve_url(args.ref_audio, args.ref_audio_url, "reference audio")

    if len(image_urls) > 9:
        print(f"ERROR: Max 9 reference images allowed (got {len(image_urls)}).")
        sys.exit(1)

    # Build content array
    content = [{"type": "text", "text": args.prompt}]
    for url in image_urls:
        content.append({
            "type": "image_url",
            "image_url": {"url": url},
            "role": "reference_image",
        })
    if video_url:
        content.append({
            "type": "video_url",
            "video_url": {"url": video_url},
            "role": "reference_video",
        })
    if audio_url:
        content.append({
            "type": "audio_url",
            "audio_url": {"url": audio_url},
            "role": "reference_audio",
        })

    body = {
        "model": MODELS[args.model],
        "content": content,
        "generate_audio": (not args.no_audio) and args.generate_audio,
        "ratio": args.ratio,
        "duration": args.duration,
        "watermark": args.watermark,
    }
    if args.seed is not None:
        body["seed"] = args.seed

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    # Submit task
    print(f"Submitting Seedance 2.0 | model={args.model} | {args.duration}s | ratio={args.ratio}")
    print(f"  Prompt: {args.prompt[:100]}{'...' if len(args.prompt) > 100 else ''}")
    if image_urls:
        print(f"  Images: {len(image_urls)} reference(s)")
    if video_url:
        print(f"  Ref video: {video_url}")
    if audio_url:
        print(f"  Ref audio: {audio_url}")

    try:
        submit = ark_request("POST", "/contents/generations/tasks", api_key, body)
    except RuntimeError as e:
        print(f"ERROR submitting task: {e}")
        sys.exit(1)

    task_id = submit.get("id") or submit.get("task_id")
    if not task_id:
        print(f"ERROR: No task id in response:\n{json.dumps(submit, indent=2)}")
        sys.exit(1)

    print(f"Task ID: {task_id}")
    print(f"Polling every {args.poll_interval}s (timeout {args.timeout}s)...")

    # Poll for completion
    start = time.time()
    last_status = None
    while True:
        elapsed = time.time() - start
        if elapsed > args.timeout:
            print(f"\nERROR: Timeout after {args.timeout}s. Task {task_id} still pending.")
            sys.exit(1)
        try:
            status_resp = ark_request("GET", f"/contents/generations/tasks/{task_id}", api_key)
        except RuntimeError as e:
            print(f"\nERROR polling: {e}")
            sys.exit(1)

        status = status_resp.get("status", "unknown")
        if status != last_status:
            print(f"  [{int(elapsed)}s] status={status}")
            last_status = status

        if status in ("succeeded", "success", "completed"):
            # Extract video URL from response
            dl_url = None
            cnt = status_resp.get("content") or {}
            if isinstance(cnt, dict):
                dl_url = cnt.get("video_url") or cnt.get("url")
            if not dl_url:
                # some responses nest under "result" / "output"
                for key in ("result", "output", "data"):
                    val = status_resp.get(key) or {}
                    if isinstance(val, dict):
                        dl_url = val.get("video_url") or val.get("url")
                        if dl_url:
                            break
            if not dl_url:
                print(f"ERROR: Task succeeded but no video URL found:\n{json.dumps(status_resp, indent=2)}")
                sys.exit(1)

            print(f"Downloading video from {dl_url[:80]}...")
            urllib.request.urlretrieve(dl_url, args.output)
            size_mb = os.path.getsize(args.output) / (1024 * 1024)
            print(f"SAVED {args.output} ({size_mb:.1f} MB)")
            return

        if status in ("failed", "error", "cancelled"):
            err = status_resp.get("error") or status_resp.get("message") or status_resp
            print(f"\nTASK FAILED: {json.dumps(err, indent=2) if isinstance(err, dict) else err}")
            # Content policy hint
            err_str = json.dumps(status_resp).lower()
            if "policy" in err_str or "likeness" in err_str or "unsafe" in err_str:
                print("\nLikely content policy block. Workarounds:")
                print("  1. Use 3D/Pixar-style characters instead of photorealistic faces")
                print("  2. Use product-only shots")
                print("  3. Switch to LTX: python scripts/generate_video_ltx.py ...")
            sys.exit(1)

        time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
