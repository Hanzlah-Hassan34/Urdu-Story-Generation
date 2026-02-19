"""Preprocess and clean Urdu story corpus"""

import csv
import html
import re
import unicodedata
from pathlib import Path

# Configuration
IN_FILES = [Path("urdu_moral_stories.csv"), Path("urdu_funny_stories.csv")]
OUT_FILE = Path("corpus.txt")

# Special tokens
EOS, EOP, EOT = "\uE000", "\uE001", "\uE002"

# Regex patterns
AD_PATTERNS = [r"\bLIVE\b", r"\bAdvertisement\b", r"Tap to unmute", r"Learn more", r"An error occurred"]
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
SENT_RE = re.compile(r"[۔!?؟]+")
NON_URDU_RE = re.compile(r"[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9\s،۔؟؛]+")

def clean(text: str) -> str:
    """Clean and normalize Urdu text"""
    text = unicodedata.normalize("NFKC", TAG_RE.sub(" ", html.unescape(text or "")))
    for pattern in AD_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.I)
    text = text.replace(",", "،").replace(";", "؛").replace("?", "؟").replace("!", "۔").replace(".", "۔").replace("ـ", "")
    return WS_RE.sub(" ", NON_URDU_RE.sub(" ", text)).strip()

def story_to_line(content: str) -> str:
    """Convert story content to tokenized line with special markers"""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n|\n|\r\n", content or "") if p.strip()]
    sentences = []
    for para in paragraphs:
        sents = [s.strip() for s in SENT_RE.split(clean(para)) if s.strip()]
        if sents:
            sentences.append(f" {EOS} ".join(sents) + f" {EOP}")
    return (" ".join(sentences) + f" {EOT}").strip() if sentences else ""

def read_contents(path: Path):
    """Read story content from CSV file"""
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            content = (row.get("content") or "").strip()
            if content:
                yield content

def main():
    """Process all input files and write cleaned corpus"""
    lines = []
    for file_path in IN_FILES:
        if file_path.exists():
            lines.extend(filter(None, (story_to_line(c) for c in read_contents(file_path))))
    
    OUT_FILE.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8", newline="\n")
    print(f"Preprocessed {len(lines)} stories → {OUT_FILE}")

if __name__ == "__main__":
    main()
