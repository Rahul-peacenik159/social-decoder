"""
Run Claude social decode on the generated report.
Reads prompts/social_decode.md + social-report.md → saves social-decode.md
"""

import os
import re
from pathlib import Path

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "social_decode.md"


def run(report_path: Path, slug: str, output_dir: Path) -> Path:
    """
    Run Claude social decode. Returns path to social-decode.md.
    Falls back to a stub file if no API key.
    """
    decode_path = output_dir / "social-decode.md"
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    report_text = report_path.read_text(encoding="utf-8")
    prompt_template = PROMPT_FILE.read_text(encoding="utf-8") if PROMPT_FILE.exists() else ""

    if not api_key or not ANTHROPIC_AVAILABLE:
        decode_path.write_text(
            f"# Social Decode: {slug}\n\n"
            "_Claude decode skipped — ANTHROPIC_API_KEY not set._\n\n"
            "Run `ANTHROPIC_API_KEY=sk-... python analyze.py {slug}` to generate.\n",
            encoding="utf-8",
        )
        print("  [skip] ANTHROPIC_API_KEY not set — wrote stub social-decode.md")
        return decode_path

    full_prompt = (
        f"{prompt_template}\n\n"
        f"---\n\n"
        f"## Source Report\n\n"
        f"{report_text}"
    )

    print("  Calling Claude for social decode ...")
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": full_prompt}],
    )
    result = message.content[0].text

    decode_path.write_text(result, encoding="utf-8")
    print(f"  Social decode saved: {decode_path}")
    return decode_path
