"""List available Gemini models for image/video generation.

Usage:
    python scripts/list_models.py
    python scripts/list_models.py --filter image
    python scripts/list_models.py --filter video
"""
import os, sys, argparse

def main():
    parser = argparse.ArgumentParser(description="List available Gemini models")
    parser.add_argument("--filter", default="", help="Filter by keyword (image, video, flash, pro)")
    args = parser.parse_args()

    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    keyword = args.filter.lower()
    for m in client.models.list():
        name = m.name.lower()
        if keyword and keyword not in name:
            continue
        if any(k in name for k in ["image", "flash", "pro", "veo", "banana", "imagen"]):
            print(m.name)

if __name__ == "__main__":
    main()
